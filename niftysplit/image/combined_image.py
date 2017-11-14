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
        raise NotImplementedError

    @abstractmethod
    def close(self):
        """Read image from specified starting coordinates and size"""
        raise NotImplementedError


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

            # Fetch any part of the image which overlaps this subimage's ROI
            part_image = subimage.read_image_bound_by_roi(start, size)

            # If any part overlapped, copy this into the combined image
            if part_image:
                combined_image.set_sub_image(part_image)

        return combined_image.image

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
        self._read_file = None

        self._roi_start = self._descriptor.ranges.roi_start
        self._roi_size = self._descriptor.ranges.roi_size

        self._axis = Axis(dim_order=self._descriptor.dim_order,
                          dim_flip=self._descriptor.dim_flip)

        self._transformer = CoordinateTransformer(
            self._descriptor.ranges.origin_start,
            self._descriptor.image_size,
            self._axis)

    def read_image(self, start, size):
        """Returns a subimage containing any overlap from the image"""

        # Convert to local coordinates for the data source
        start_local, size_local = self._transformer.to_local(start, size)

        # Get the image data from the data source
        local_source = self._get_read_file()
        image_local = local_source.read_image(start_local, size_local)

        image = SmartImage(image_local, self._transformer)
        return ImageWrapper(start, image=image.transform_to_global())

    def read_image_bound_by_roi(self, start, size):
        """Returns a subimage containing any overlap from the ROI"""

        # Find the part of the requested region that fits in the ROI
        sub_start, sub_size = self.bind_by_roi(start, size)

        # Check if any of region is contained in this subimage
        if np.all(np.greater(sub_size, np.zeros_like(sub_size))):
            return self.read_image(sub_start, sub_size)
        else:
            return None

    def close(self):
        """Close all streams and files"""

        if self._read_file:
            self._read_file.close()
            self._read_file = None

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

    def _get_read_file(self):
        if not self._read_file:
            self._read_file = self._file_factory.create_read_file(
                self._descriptor)
        return self._read_file


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
        image_local = self._data_source.read_image(start, size)
        return self._converter.image_to_global(image_local)

    def close(self):
        """Close all streams and files"""
        self._data_source.close()


class SmartImage(object):
    """Image wrapper which converts between Axes"""

    def __init__(self, image, converter):
        self._image = image
        self._converter = converter

    def transform_to_global(self):
        """Returns a partial image using the specified global coordinates"""

        return self._converter.image_to_global(self._image)


class LocalSource(Source):
    """Data source allowing use of a global source with local coordinates"""

    def __init__(self, data_source, converter):
        self._data_source = data_source
        self._converter = converter

    def read_image(self, start_local, size_local):
        """Returns a partial image using the specified local coordinates"""

        start, size = self._converter.to_global(start_local, size_local)
        image_global = self._data_source.read_image(start, size)
        return self._converter.image_to_local(image_global)

    def close(self):
        """Close all streams and files"""
        self._data_source.close()


class CoordinateTransformer(object):
    """Convert coordinates between orthogonal systems"""

    def __init__(self, origin, size, axis):
        """Create a transformer object for converting between systems

        :param origin: local coordinate origin in global coordinates
        :param size: size of the local frame in global coordinates
        :param dim_ordering: ordering of local dimensions
        :param dim_flip: whether local axes should be flipped
        """
        self._origin = origin
        self._size = size
        self._axis = axis

    def to_local(self, global_start, global_size):
        """Convert global coordinates to local coordinates"""

        # Translate coordinates to the local origin
        start = np.subtract(global_start, self._origin)
        size = np.array(global_size)  # Make sure global_size is a numpy array

        # Permute dimensions of local coordinates
        start = start[self._axis.dim_order]
        size = size[self._axis.dim_order]
        size_t = np.array(self._size)[self._axis.dim_order]

        # Flip dimensions where necessary
        for index, flip in enumerate(self._axis.dim_flip):
            if flip:
                start[index] = size_t[index] - start[index] - 1

        return start, size

    def image_to_local(self, global_image):
        """Transform image to local coordinate system"""

        local_image = np.transpose(global_image, self._axis.dim_order)

        # Flip dimensions where necessary
        for index, flip in enumerate(self._axis.dim_flip):
            if flip:
                local_image = np.flip(local_image, index)

        return local_image

    def to_global(self, local_start, local_size):
        """Convert local coordinates to global coordinates"""

        start = np.array(local_start)
        size = np.array(local_size)

        size_t = np.array(self._size)[self._axis.dim_order]

        # Flip dimensions where necessary
        for index, flip in enumerate(self._axis.dim_flip):
            if flip:
                start[index] = size_t[index] - start[index] - 1

        # Reverse permute dimensions of local coordinates
        start = start[np.argsort(self._axis.dim_order)]
        size = size[np.argsort(self._axis.dim_order)]

        # Translate coordinates to the global origin
        start = np.add(start, self._origin)
        size = np.array(size)  # Make sure global_size is a numpy array

        return start, size

    def image_to_global(self, local_image):
        """Convert local coordinates to global coordinates"""

        # Flip dimensions where necessary
        for index, flip in enumerate(self._axis.dim_flip):
            if flip:
                local_image = np.flip(local_image, index)

        # Reverse permute dimensions of local coordinates
        global_image = np.transpose(local_image,
                                    np.argsort(self._axis.dim_order))

        return global_image


class Axis(object):
    """Defines coordinate system used by imaeg coordinates"""

    def __init__(self, dim_order, dim_flip):
        self.dim_order = dim_order
        self.dim_flip = dim_flip
