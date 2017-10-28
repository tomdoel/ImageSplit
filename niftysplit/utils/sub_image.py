# coding=utf-8
"""
Utility files for splitting large images into subimages

Author: Tom Doel
Copyright UCL 2017

"""


class SubImage(object):
    """An image which forms part of a larger image"""

    def __init__(self, descriptor, data_source):
        self._descriptor = descriptor
        self._data_source = data_source

        # Construct the origin offset used to convert from global
        # coordinates. This excludes overlapping voxels
        self._image_size = self._descriptor.image_size
        self._origin_start = self._descriptor.origin_start
        self._origin_end = self._descriptor.origin_end
        self._roi_start = self._descriptor.roi_start
        self._dim_order = self._descriptor.dim_order
        self._roi_end = self._descriptor.roi_end
        self._ranges = self._descriptor.ranges

        # Convenience arrays for reordering dimensions
        self._dim_index = [abs(d) - 1 for d in self._dim_order]
        self._dim_flip = [d < 0 for d in self._dim_order]

    def write_image_file(self, input_combined):
        output_ranges = self.get_ranges()

        # The order in which we iterate over dimensions depends on the
        # preferred ordering of the output file
        dimension_ordering = self.get_dimension_ordering()

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
                start_coords_global = self._get_start_coordinates(
                    dimension_ordering, u_start, v, w)

                image_line = input_combined.read_line(
                    start_coords_global, voxels_per_line, read_direction)
                self.write_line(start_coords_global,
                                      image_line, read_direction)

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

    def _get_start_coordinates(self, dimension_ordering, u_start, v, w):
        u = u_start
        v_dimension = abs(dimension_ordering[1]) - 1
        w_dimension = abs(dimension_ordering[2]) - 1
        u_dimension = abs(dimension_ordering[0]) - 1
        start_coords_global = [0, 0, 0]
        start_coords_global[u_dimension] = u
        start_coords_global[v_dimension] = v
        start_coords_global[w_dimension] = w
        return start_coords_global

    def get_ranges(self):
        """Returns the full range of global coordinates covered by this
        subimage """

        return self._ranges

    def write_line(self, start_coords, image_line, direction):
        """Writes a line of image data to a binary file at the specified
        image location """

        start_coords_local = self._to_local_coords(start_coords)
        self._data_source.write_line(start_coords_local, image_line, direction)

    def read_line(self, start_coords, num_voxels, direction):
        """Reads a line of image data from a binary file at the specified
        image location """

        if not self.contains_voxel(start_coords, True):
            raise ValueError('The data range to load extends beyond this file')

        # Don't read bytes beyond the end of the valid range
        if start_coords[0] + num_voxels - 1 > self._roi_end[0]:
            num_voxels = self._roi_end[0] - start_coords[0] + 1

        start_local, direction = self._to_local_coords(start_coords, direction)
        return self._data_source.read_line(start_local, num_voxels,
                                           direction)

    def contains_voxel(self, start_coords_global, must_be_in_roi):
        """Determines if the specified voxel lies within the ROI of this
        subimage """

        if must_be_in_roi:
            return (
                self._roi_start[0] <= start_coords_global[0] <= self._roi_end[
                    0] and
                self._roi_start[1] <= start_coords_global[1] <= self._roi_end[
                    1] and
                self._roi_start[2] <= start_coords_global[2] <= self._roi_end[
                    2])

        return (
            self._origin_start[0] <= start_coords_global[0] <=
            self._origin_end[
                0] and
            self._origin_start[1] <= start_coords_global[1] <=
            self._origin_end[
                1] and
            self._origin_start[2] <= start_coords_global[2] <=
            self._origin_end[
                2])

    def close(self):
        """Close all streams and files"""
        self._data_source.close()

    def get_bytes_per_voxel(self):
        """Return the number of bytes used to represent a single voxel"""
        return self._data_source.get_bytes_per_voxel()

    def get_dimension_ordering(self):
        """Return the preferred ordering of dimensions"""
        return self._data_source.get_dimension_ordering()

    def _to_local_coords(self, global_coords, direction):
        local_coords = [0, 0, 0]
        translated = [start_coord - origin_coord for start_coord, origin_coord
                      in zip(global_coords, self._origin_start)]

        # Flip coordinates if writing the voxels in reverse
        if self._dim_flip[0]:
            translated[0] = 1 + self._image_size[0] - translated[0]
        if self._dim_flip[1]:
            translated[1] = 1 + self._image_size[1] - translated[1]
        if self._dim_flip[2]:
            translated[2] = 1 + self._image_size[2] - translated[2]

        if self._dim_flip[abs(direction) - 1]:
            direction = - direction

        local_coords[0] = translated[self._dim_index[0]]
        local_coords[1] = translated[self._dim_index[1]]
        local_coords[2] = translated[self._dim_index[2]]

        return local_coords


class StoredImage(object):
    """Convert image coordinates to a"""

    def __init__(self, data_source):

        dim_order = data_source.get_dim_order()
        self._file_image_size = data_source.get_file_image_size()

        # Comvenience arrays for reordering dimensions
        self._dim_index = [abs(d) - 1 for d in dim_order]
        self._dim_flip = [1 if d < 0 else 0 for d in dim_order]

    def write_line(self, start_coords, image_line, direction):
        """Writes a line of image data to a binary file at the specified
        image location """

        file_coords, direction = self._to_file_coords(start_coords)
        self._data_source.write_line(file_coords, image_line, direction)

    def _to_file_coords(self, image_coords, direction):

        # Flip coordinates if writing the voxels in reverse
        flipped_coords = [x + flip*(1 + length - 2*x) for x, flip, length in
                          zip(image_coords, self._dim_flip, self._image_size)]

        # Reorder dimensions
        file_coords = [flipped_coords[self._dim_index[x]] for x in [0, 1, 2]]

        # Reorder direction
        direction = 1 + self._dim_index.index(abs(direction) - 1)

        # Flip direction
        if self._dim_flip[abs(direction) - 1]:
            direction = - direction


        return file_coords, direction
