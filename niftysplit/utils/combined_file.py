import copy

import numpy as np

from utils.file_descriptor import SubImageDescriptor
from utils.metaio_reader import compute_bytes_per_voxel, get_numpy_datatype, \
    MetaIoFile
from utils.sub_image import SubImage


def write_files(descriptors_in, descriptors_out, file_factory, original_header,
                output_type):
    """Creates a set of output files from the input files"""
    input_combined = CombinedFileReader(descriptors_in, file_factory)
    output_combined = CombinedFileWriter(descriptors_out, file_factory,
                                         original_header, output_type)
    output_combined.write_image_file(input_combined)

    input_combined.close()
    output_combined.close()


class CombinedFileWriter(object):
    """A kind of virtual file for writing where the data are distributed
        across multiple real files. """

    def __init__(self, descriptors, file_factory, header_template,
                 element_type):
        """Create for the given set of descriptors"""

        if element_type:
            header_template = copy.deepcopy(header_template)
            header_template["ElementType"] = element_type
        descriptors_sorted = sorted(descriptors, key=lambda k: k['index'])
        self._subimages = []
        self._cached_last_subimage = None
        self._bytes_per_voxel = compute_bytes_per_voxel(
            header_template["ElementType"])
        self._numpy_format = get_numpy_datatype(header_template["ElementType"],
                                                header_template[
                                                    "BinaryDataByteOrderMSB"])
        for descriptor in descriptors_sorted:
            subimage_descriptor = SubImageDescriptor(descriptor)
            header_template["DimSize"] = subimage_descriptor.image_size
            header_template["Origin"] = subimage_descriptor.origin_start

            file = MetaIoFile(descriptor["filename"], file_factory,
                              header_template)

            self._subimages.append(SubImage(subimage_descriptor, file))

    def write_image_file(self, input_combined):
        """Write out all the subimages"""
        for next_image in self._subimages:
            output_ranges = next_image.get_ranges()
            i_range_global = output_ranges[0]
            j_range_global = output_ranges[1]
            k_range_global = output_ranges[2]
            num_voxels_to_read_per_line = i_range_global[1] + 1 - \
                                          i_range_global[0]

            for k_global in range(k_range_global[0], 1 + k_range_global[1]):
                for j_global in range(j_range_global[0], 1 + j_range_global[1]):
                    start_coords_global = [i_range_global[0], j_global,
                                           k_global]
                    image_line = input_combined.read_image_stream(
                        start_coords_global, num_voxels_to_read_per_line)
                    next_image.write_image_stream(start_coords_global,
                                                  image_line)

    def close(self):
        """Close all files and streams"""
        for subimage in self._subimages:
            subimage.close()


class CombinedFileReader(object):
    """A kind of virtual file for reading where the data are distributed
    across multiple real files. """

    def __init__(self, descriptors, file_factory):
        descriptors_sorted = sorted(descriptors, key=lambda k: k['index'])
        self._subimages = []
        self._cached_last_subimage = None
        for descriptor in descriptors_sorted:
            subimage_descriptor = SubImageDescriptor(descriptor)
            file = MetaIoFile(descriptor["filename"], file_factory, None)

            self._subimages.append(SubImage(subimage_descriptor, file))

    def read_image_stream(self, start_coords_global, num_voxels_to_read):
        """Reads pixels from an abstract image stream"""
        byte_stream = None
        current_i_start = start_coords_global[0]
        while num_voxels_to_read > 0:
            current_start_coords = [current_i_start, start_coords_global[1],
                                    start_coords_global[2]]
            next_image = self._find_subimage(current_start_coords, True)
            next_byte_stream = next_image.read_image_stream(
                current_start_coords, num_voxels_to_read)
            if byte_stream is not None:
                byte_stream = np.concatenate((byte_stream, next_byte_stream))
            else:
                byte_stream = next_byte_stream
            num_voxels_read = round(len(next_byte_stream))
            num_voxels_to_read -= num_voxels_read
            current_i_start += num_voxels_read
        return byte_stream

    def close(self):
        """Closes all streams and files"""
        for subimage in self._subimages:
            subimage.close()

    def _find_subimage(self, start_coords_global, must_be_in_roi):

        # For efficiency, first check the last subimage before going through
        # the whole list
        if self._cached_last_subimage \
                and self._cached_last_subimage.contains_voxel(
                        start_coords_global, must_be_in_roi):
            return self._cached_last_subimage

        # Iterate through the list of subimages to find the one containing
        # these start coordinates
        for next_subimage in self._subimages:
            if next_subimage.contains_voxel(start_coords_global,
                                            must_be_in_roi):
                self._cached_last_subimage = next_subimage
                return next_subimage

        raise ValueError('Coordinates are out of range')