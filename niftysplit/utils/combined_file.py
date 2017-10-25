# coding=utf-8
"""
Wrapper for an image which consists of one or more subimages

Author: Tom Doel
Copyright UCL 2017

"""

import numpy as np

from niftysplit.utils.file_descriptor import SubImageDescriptor
from niftysplit.utils.sub_image import SubImage


def write_files(descriptors_in, descriptors_out, file_factory):
    """Creates a set of output files from the input files"""
    input_combined = CombinedFileReader(descriptors_in, file_factory)
    output_combined = CombinedFileWriter(descriptors_out, file_factory)
    output_combined.write_image_file(input_combined)

    input_combined.close()
    output_combined.close()


class CombinedFileWriter(object):
    """A kind of virtual file for writing where the data are distributed
        across multiple real files. """

    def __init__(self, descriptors, file_factory):
        """Create for the given set of descriptors"""

        descriptors_sorted = sorted(descriptors, key=lambda k: k['index'])
        self._subimages = []
        for descriptor in descriptors_sorted:
            subimage_descriptor = SubImageDescriptor(descriptor)
            file_handle = file_factory.create_write_file(subimage_descriptor)
            self._subimages.append(SubImage(subimage_descriptor, file_handle))

    def write_image_file(self, input_combined):
        """Write out all the subimages"""

        # Iterate over all the files that will be created
        for next_image in self._subimages:
            output_ranges = next_image.get_ranges()

            # The order in which we iterate over dimensions depends on the
            # preferred ordering of the output file
            dimension_ordering = next_image.get_dimension_ordering()

            u_start, u_end, u_step, u_length = self._get_range(
                dimension_ordering, output_ranges, 0)
            v_start, v_end, v_step, v_length = self._get_range(
                dimension_ordering, output_ranges, 1)
            w_start, w_end, w_step, w_length = self._get_range(
                dimension_ordering, output_ranges, 2)

            voxels_per_line = u_length
            read_direction = dimension_ordering[0]

            for w in range(w_start, w_end, w_step):
                for v in range(v_start, v_end, v_step):
                    start_coords_global = self.get_start_coordinates(
                        dimension_ordering, u_start, v, w)

                    image_line = input_combined.read_line(
                        start_coords_global, voxels_per_line, read_direction)
                    next_image.write_line(start_coords_global,
                                          image_line, read_direction)

    def get_start_coordinates(self, dimension_ordering, u_start, v, w):
        u = u_start
        v_dimension = abs(dimension_ordering[1]) - 1
        w_dimension = abs(dimension_ordering[2]) - 1
        u_dimension = abs(dimension_ordering[0]) - 1
        start_coords_global = [0, 0, 0]
        start_coords_global[u_dimension] = u
        start_coords_global[v_dimension] = v
        start_coords_global[w_dimension] = w
        return start_coords_global

    def _get_range(self, dimension_ordering, output_ranges, index):

        dimension = abs(dimension_ordering[index]) - 1
        ranges = output_ranges[dimension]
        voxels_per_line = ranges[1] + 1 - ranges[0]

        if dimension_ordering[0] < 0:
            x_start = ranges[1]
            x_end = ranges[0] - 1
            x_step = -1
        else:
            x_start = ranges[0]
            x_end = ranges[1] + 1
            x_step = 1

        return x_start, x_end, x_step, voxels_per_line

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
            file_handle = file_factory.create_read_file(subimage_descriptor)
            self._subimages.append(SubImage(subimage_descriptor, file_handle))

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
            if flip:
                current_start_coords[incr_dim] -= num_voxels_read
            else:
                current_start_coords[incr_dim] += num_voxels_read
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
