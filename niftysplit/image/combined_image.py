# coding=utf-8

"""Classes for aggregating images from multiple files into a single image"""
from abc import ABCMeta, abstractmethod

import numpy as np
from niftysplit.image.image_wrapper import ImageWrapper


class Source(object):
    """Base class for reading data"""
    __metaclass__ = ABCMeta

    @abstractmethod
    def read_image(self, start, size):
        """Read image from specified starting coordinates and size"""
        pass

    @abstractmethod
    def close(self):
        """Read image from specified starting coordinates and size"""
        pass


class CombinedImage(Source):
    """A kind of virtual file for writing where the data are distributed
        across multiple real files. """

    def __init__(self, descriptors, file_factory):
        """Create for the given set of descriptors"""

        self._subimages = []
        for subimage_descriptor in descriptors:
            self._subimages.append(SubImage(subimage_descriptor, file_factory))

    def read_image(self, start, size):
        """Assembles an image range from subimages"""

        combined_image = ImageWrapper(start, image_size=size)
        for subimage in self._subimages:

            # Find the part of the requested region that fits in the ROI
            sub_start, sub_size = subimage.bind_by_roi(start, size)

            # Check if any of region is contained in this subimage
            if np.all(np.greater(sub_size, np.zeros_like(sub_size))):
                part_image = subimage.read_image_global(sub_start, sub_size)
                combined_image.set_sub_image(part_image)

    def close(self):
        """Closes all streams and files"""
        for subimage in self._subimages:
            subimage.close()

    def write_image(self, source):
        """Write out all the subimages with data from supplied source"""

        # Get each subimage to write itself
        for next_image in self._subimages:
            next_image.write_image(source)


class SubImage(Source):
    """An image which forms part of a larger image"""

    def __init__(self, descriptor, file_factory):
        self._file_factory = file_factory
        self._descriptor = descriptor
        self._read_source = None

        self._roi_start = self._descriptor.roi_start
        self._roi_size = np.add(
            np.subtract(self._descriptor.roi_end, self._descriptor.roi_start),
            np.ones_like(self._roi_start))

        self._transformer = CoordinateTransformer(
            self._descriptor.origin_start,
            self._descriptor.image_size,
            self._descriptor.dim_order,
            self._descriptor.dim_flip)

    def read_image(self, start, size):
        """Returns a subimage containing any overlap from the ROI"""

        # Wrap the image data in an ImageWrapper
        return ImageWrapper(
            start,
            image=self._get_read_source().read_image(start, size))

    def close(self):
        """Close all streams and files"""

        if self._read_source:
            self._read_source.close()
            self._read_source = None

    def write_image(self, global_source):
        """Write out SubImage using data from the specified source"""

        out_file = self._file_factory.create_write_file(self._descriptor)
        local_source = LocalSource(global_source, self._transformer)
        out_file.write_image(local_source)
        out_file.close()

    def bind_by_roi(self, start_global, size_global):
        """Find the part of the specified region that fits within the ROI"""

        start = np.maximum(start_global, self._roi_start)
        end = np.minimum(np.add(start_global, size_global),
                         np.add(self._roi_start, self._roi_size))
        size = np.subtract(end, start)
        return start, size

    def _get_read_source(self):
        if not self._read_source:
            local_source = self._file_factory.create_read_file(self._descriptor)
            self._read_source = GlobalSource(local_source, self._transformer)
        return self._read_source


class GlobalSource(Source):
    """Data source allowing use of a local source with global coordinates"""

    def __init__(self, data_source, converter):
        self._data_source = data_source
        self._converter = converter

    def read_image(self, start_global, size_global):
        """Returns a partial image using the specified global coordinates"""

        # Convert to local coordinates for the data source
        start, size = self._converter.to_local(start_global, size_global)

        # Get the image data from the data source
        return self._data_source.read_image(start, size)

    def close(self):
        """Close all streams and files"""
        self._data_source.close()


class LocalSource(Source):
    """Data source allowing use of a global source with local coordinates"""

    def __init__(self, data_source, converter):
        self._data_source = data_source
        self._converter = converter

    def read_image(self, start_local, size_local):
        """Returns a partial image using the specified local coordinates"""

        start, size = self._converter.to_global(start_local, size_local)
        return self._data_source.read_image(start, size)

    def close(self):
        """Close all streams and files"""
        self._data_source.close()


class CoordinateTransformer(object):
    """Convert coordinates between orthogonal systems"""

    def __init__(self, origin, size, dim_ordering, dim_flip):
        """Create a transformer object for converting between systems

        :param origin: local coordinate origin in global coordinates
        :param size: size of the local frame in global coordinates
        :param dim_ordering: ordering of local dimensions
        :param dim_flip: whether local axes should be flipped
        """
        self._origin = origin
        self._size = size
        self._dim_ordering = dim_ordering
        self._dim_flip = dim_flip

    def to_local(self, global_start, global_size):
        """Convert global coordinates to local coordinates"""

        # Translate coordinates to the local origin
        start = np.subtract(global_start, self._origin)
        size = np.array(global_size)  # Make sure global_size is a numpy array

        # Permute dimensions of local coordinates
        start = start[self._dim_ordering]
        size = size[self._dim_ordering]
        size_t = np.array(self._size)[self._dim_ordering]

        # Flip dimensions where necessary
        for index, flip in enumerate(self._dim_flip):
            if flip:
                start[index] = size_t[index] - start[index] - 1

        return start, size

    def to_global(self, local_start, local_size):
        """Convert local coordinates to global coordinates"""

        start = np.array(local_start)
        size = np.array(local_size)

        size_t = np.array(self._size)[self._dim_ordering]

        # Flip dimensions where necessary
        for index, flip in enumerate(self._dim_flip):
            if flip:
                start[index] = size_t[index] - start[index] - 1

        # Reverse permute dimensions of local coordinates
        start = start[np.argsort(self._dim_ordering)]
        size = size[np.argsort(self._dim_ordering)]

        # Translate coordinates to the global origin
        start = np.add(start, self._origin)
        size = np.array(size)  # Make sure global_size is a numpy array

        return start, size
