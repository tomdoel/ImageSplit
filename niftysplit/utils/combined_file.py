# coding=utf-8
"""
Wrapper for an image which consists of one or more subimages

Author: Tom Doel
Copyright UCL 2017

"""

import numpy as np

from image.image_wrapper import ImageWrapper
from niftysplit.utils.file_descriptor import SubImageDescriptor
from niftysplit.utils.sub_image import SubImage


def write_files(descriptors_in, descriptors_out, file_factory):
    """Creates a set of output files from the input files"""

    descriptors_in_sorted = sorted(descriptors_in, key=lambda k: k['index'])
    descriptors_out_sorted = sorted(descriptors_out, key=lambda k: k['index'])

    desc_in = [SubImageDescriptor(d) for d in descriptors_in_sorted]
    desc_out = [SubImageDescriptor(d) for d in descriptors_out_sorted]

    input_combined = CombinedFileReader(desc_in, file_factory)
    output_combined = CombinedFileWriter(desc_out, file_factory)
    output_combined.write_image_file(input_combined)

    input_combined.close()
    output_combined.close()




class CombinedFileWriter(object):
    """A kind of virtual file for writing where the data are distributed
        across multiple real files. """

    def __init__(self, descriptors, file_factory):
        """Create for the given set of descriptors"""

        self._subimages = []
        for subimage_descriptor in descriptors:
            file_handle = file_factory.create_write_file(subimage_descriptor)
            self._subimages.append(SubImage(subimage_descriptor, file_handle))

    def write_image_file(self, input_combined):
        """Write out all the subimages"""

        # Get each subimage to write itself
        for next_image in self._subimages:
            next_image.write_image_file(input_combined)

    def close(self):
        """Close all files and streams"""
        for subimage in self._subimages:
            subimage.close()


class CombinedFileReader(object):
    """A kind of virtual file for reading where the data are distributed
    across multiple real files. """

    def __init__(self, descriptors, file_factory):
        self._subimages = []
        self._cached_last_subimage = None
        for subimage_descriptor in descriptors:
            file_handle = file_factory.create_read_file(subimage_descriptor)
            self._subimages.append(SubImage(subimage_descriptor, file_handle))

    def read_image(self, start_global, size):
        """Assembles an image range from subimages"""

        combined_image = ImageWrapper(start_global, image_size=size)
        for next_subimage in self._subimages:
            part_image = next_subimage.read_part_image(start_global, size)
            if part_image:
                combined_image.set_sub_image(part_image)

    def read_image_stream(self, start_coords_global, num_voxels_to_read,
                          read_direction):
        """
        Reads pixels from an abstract image stream

        :param start_coords_global: Global coordinates of first voxel to read
        :param num_voxels_to_read: Number of voxels to read
        :param read_direction: +1 read forward along first dimension
                               -1 read back along first dimension
                               similarly for other dimensions: +2, -2, +3, -3
        :return: np array containing the data that has been read
        """
        byte_stream = None
        flip = read_direction < 0
        incr_dim = abs(read_direction) - 1
        current_start_coords = [start_coords_global[0], start_coords_global[1],
                                start_coords_global[2]]
        while num_voxels_to_read > 0:
            next_image = self._find_subimage(current_start_coords, True)
            next_byte_stream = next_image.read_line(
                current_start_coords, num_voxels_to_read, read_direction)
            if byte_stream is not None:
                byte_stream = np.concatenate((byte_stream, next_byte_stream))
            else:
                byte_stream = next_byte_stream
            num_voxels_read = round(len(next_byte_stream))
            num_voxels_to_read -= num_voxels_read
            # if flip:
            #     current_start_coords[incr_dim] -= num_voxels_read
            # else:
            #     current_start_coords[incr_dim] += num_voxels_read
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
