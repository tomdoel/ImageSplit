# coding=utf-8
"""
Utility files for splitting large images into subimages

Author: Tom Doel
Copyright UCL 2017

"""

import numpy as np

from niftysplit.image.image_wrapper import ImageWrapper
from niftysplit.utils.utilities import CoordinateTransformer


class SubImage(object):
    """An image which forms part of a larger image"""

    def __init__(self, descriptor, file_factory):
        self._file_factory = file_factory
        self._descriptor = descriptor
        self._read_source = None

        # Construct the origin offset used to convert from global
        # coordinates. This excludes overlapping voxels
        self._image_size = self._descriptor.image_size
        self._origin_start = self._descriptor.origin_start
        self._origin_end = self._descriptor.origin_end
        self._roi_start = self._descriptor.roi_start
        self._dim_order = self._descriptor.dim_order
        self._dim_flip = self._descriptor.dim_flip
        self._roi_end = self._descriptor.roi_end
        self._roi_size = np.add(np.subtract(self._roi_end, self._roi_end),
                                np.ones(shape=self._roi_start))
        self._ranges = self._descriptor.ranges
        self._transformer = CoordinateTransformer(self._origin_start,
                                                  self._dim_order,
                                                  self._dim_flip)

    def read_part_image(self, start_global, size):
        """Returns a subimage containing any overlap from the ROI"""

        # Find the part of the requested region that fits in the ROI
        start, end, size = self._get_bounds_in_roi(start_global, size)

        # Check if none of the requested region is contained in this subimage
        if np.any(np.less(size, np.zeros(shape=size))):
            return None

        image_data = self._get_read_source().read_image(start, size)

        # Wrap the image data in an ImageWrapper
        return ImageWrapper(start, image=image_data)

    def write_subimage(self, source):
        """Write out SubImage using data from the specified source"""
        file = self._file_factory.create_write_file(self._descriptor)
        transformed_source = TransformedDataSource(source, self._transformer)
        file.write_file(transformed_source)
        file.close()

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
        self._read_source.close()
        self._read_source = None

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

    def _get_bounds_in_roi(self, start_global, size_global):
        start = np.maximum(start_global, self._roi_start)
        end = np.minimum(np.add(start_global, size_global),
                         np.add(self._roi_start, self._roi_size))
        size = np.subtract(end, start)
        return start, end, size

    def _get_read_source(self):
        if not self._read_source:
            source = self._file_factory.create_read_file(self._descriptor)
            self._read_source = TransformedDataSource(source, self._transformer)
        return self._read_source


class TransformedDataSource(object):
    """Data source with conversion between local and global coordinates"""

    def __init__(self, data_source, converter):
        self._data_source = data_source
        self._converter = converter

    def read_image(self, start_local, size_local):
        """Returns a partial image using the specified local coordinates"""

        start, size = self._converter.to_global(start_local, size_local)
        return self._data_source.read_image(start, size)

    def read_image_local(self, start_global, size_global):
        """Returns a partial image using the specified global coordinates"""

        # Convert to local coordinates for the data source
        start, size = self._converter.to_local(start_global, size_global)

        # Get the image data from the data source
        return self._data_source.read_image(start, size)
