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

    def close(self):
        """Close all streams and files"""
        self._read_source.close()
        self._read_source = None

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
