# coding=utf-8

"""Classes for aggregating images from multiple files into a single image"""
from abc import ABCMeta, abstractmethod

import numpy as np
import six
from imagesplit.image.image_wrapper import SmartImage


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


class CombinedImage(object):
    """A kind of virtual file for writing where the data are distributed
        across multiple real files. """

    def __init__(self, descriptors, file_factory):
        """Create for the given set of descriptors"""

        self.limits = None
        self._subimages = []
        for subimage_descriptor in descriptors:
            self._subimages.append(SubImage(subimage_descriptor, file_factory))

    def read_image(self, start_local, size_local, transformer):
        """Assembles an image range from subimages"""

        # Create the output image wrapper
        combined_image = SmartImage(start=start_local,
                                    size=size_local,
                                    image=None,
                                    transformer=transformer)

        # Compute global coordinates to match with subimage descriptors
        start, size = transformer.to_global(start_local, size_local)

        # Check each subimage for overlaps
        for subimage in self._subimages:

            # Fetch any part of the image which overlaps this subimage's ROI
            part_image = subimage.read_image_bound_by_roi(start, size)

            # If any part overlapped, copy this into the combined image
            if part_image:
                combined_image.set_sub_image(part_image)

        return combined_image

    def close(self):
        """Closes all streams and files"""
        for subimage in self._subimages:
            subimage.close()

    def write_image(self, source, rescale, test=False):
        """Write out all the subimages with data from supplied source"""

        # If rescaling is required, get the global limits
        if not rescale:
            limits = None
            six.print_("Limits: No rescale")
        elif rescale == "limits":
            limits = source.get_limits()
            six.print_("Limits: " + str(limits.min) + ":" + str(limits.max))
        else:
            limits = Limits(rescale[0], rescale[1])
            six.print_("Limits: " + str(limits.min) + ":" + str(limits.max))

        # Get each subimage to write itself
        if not test:
            for next_image in self._subimages:
                next_image.write_image(source, limits)

    def get_limits(self):
        """Return minimum and maximum values across all subimages"""

        if not self.limits:
            minv = None
            maxv = None
            for next_image in self._subimages:
                next_min, next_max = next_image.get_limits()
                if minv is None or next_min < minv:
                    minv = next_min
                if maxv is None or next_max > maxv:
                    maxv = next_max
            self.limits = Limits(minv, maxv)

        return self.limits


class Limits(object):
    """Image range values across all subimages"""

    def __init__(self, rmin, rmax):
        self.min = rmin
        self.max = rmax


class SubImage(Source):
    """An image which forms part of a larger image"""

    def __init__(self, descriptor, file_factory):
        self._file_factory = file_factory
        self._descriptor = descriptor
        self._read_file = None

        self._roi_start = self._descriptor.ranges.roi_start
        self._roi_size = self._descriptor.ranges.roi_size

        self._axis = self._descriptor.axis

        self._transformer = CoordinateTransformer(
            self._descriptor.ranges.origin_start,
            self._descriptor.ranges.image_size,
            self._axis)

    def read_image(self, start, size):
        """Returns a subimage containing any overlap from the image"""

        # Convert to local coordinates for the data source
        start_local, size_local = self._transformer.to_local(start, size)

        # Get the image data from the data source
        local_source = self._get_read_file()
        image_local = local_source.read_image(start_local, size_local)

        return SmartImage(start=start_local,
                          size=size_local,
                          image=image_local,
                          transformer=self._transformer)

    def read_image_bound_by_roi(self, start, size):
        """Returns a subimage containing any overlap from the ROI"""

        # Find the part of the requested region that fits in the ROI
        sub_start, sub_size = self.bind_by_roi(start, size)

        # Check if any of region is contained in this subimage
        if np.all(np.greater(sub_size, 0)):
            return self.read_image(sub_start, sub_size)

        # Otherwise return None to indicate that the subimage is out of range
        return None

    def close(self):
        """Close all streams and files"""

        if self._read_file:
            self._read_file.close()
            self._read_file = None

    def write_image(self, global_source, rescale_limits):
        """Write out SubImage using data from the specified source"""

        out_file = self._file_factory.create_write_file(self._descriptor)
        local_source = LocalSource(global_source, self._transformer)
        out_file.write_image(local_source, rescale_limits)

    def bind_by_roi(self, start_global, size_global):
        """Find the part of the specified region that fits within the ROI"""

        start = np.maximum(start_global, self._roi_start)
        end = np.minimum(np.add(start_global, size_global),
                         np.add(self._roi_start, self._roi_size))
        size = np.subtract(end, start)
        return start, size

    def get_limits(self):
        """Return minimum and maximum values across all subimages"""

        image = self.read_image(self._descriptor.ranges.origin_start,
                                self._descriptor.ranges.image_size)

        minv = np.min(image.image.get_raw())
        maxv = np.max(image.image.get_raw())
        return minv, maxv

    def _get_read_file(self):
        if not self._read_file:
            self._read_file = self._file_factory.create_read_file(
                self._descriptor)
        return self._read_file


class LocalSource(Source):
    """Fetch and transform data using local coordinates"""

    def __init__(self, source, transformer):
        self._source = source
        self._transformer = transformer

    def read_image(self, start, size):
        """Returns a partial image using the specified local coordinates"""

        return self._source.read_image(
            start, size, self._transformer)

    def close(self):
        """Close all streams and files"""
        self._source.close()


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
        self.axis = axis

        size_t = np.array(self._size)[self.axis.dim_order]

        self._flip_offset = np.zeros_like(self.axis.dim_flip)
        self._flip_multiple = np.subtract(1, np.multiply(2, self.axis.dim_flip))

        for index, flip in enumerate(self.axis.dim_flip):
            if flip:
                self._flip_offset[index] = size_t[index] - 1

    def to_local(self, global_start, global_size):
        """Convert global coordinates to local coordinates"""

        # Translate coordinates to the local origin
        start = np.subtract(global_start, self._origin)
        size = np.array(global_size)  # Make sure global_size is a numpy array

        # Permute dimensions of local coordinates
        start = start[self.axis.dim_order]
        size = size[self.axis.dim_order]

        # Flip dimensions where necessary
        start = np.add(np.multiply(start, self._flip_multiple),
                       self._flip_offset)

        return start, size

    def to_other(self, local_start, local_size, other_transformer):
        """Convert local coordinates to a different local system"""

        global_start, global_size = self.to_global(local_start, local_size)
        return other_transformer.to_local(global_start, global_size)

    def to_global(self, local_start, local_size):
        """Convert local coordinates to global coordinates"""

        start = np.array(local_start)
        size = np.array(local_size)

        # Flip dimensions where necessary
        start = np.add(np.multiply(start, self._flip_multiple),
                       self._flip_offset)

        # Reverse permute dimensions of local coordinates
        start = start[self.axis.reverse_dim_order]
        size = size[self.axis.reverse_dim_order]

        # Translate coordinates to the global origin
        start = np.add(start, self._origin)
        size = np.array(size)  # Make sure global_size is a numpy array

        return start, size

    def image_to_local(self, global_image):
        """Transform global image to local coordinate system"""

        local_image = global_image.transpose(self.axis.dim_order)

        # Flip dimensions where necessary
        local_image = local_image.flip(self.axis.dim_flip)

        return local_image

    def image_to_other(self, local_image, other_transformer):
        """Transform image to a different local coordinate system"""

        # Flip dimensions where necessary
        local_image = local_image.flip(self.axis.dim_flip)

        # Reverse permute dimensions of local coordinates
        global_dim_order = np.array(self.axis.reverse_dim_order)
        global_flip = np.array(self.axis.dim_flip)[global_dim_order]
        local_dim_order = global_dim_order[other_transformer.axis.dim_order]
        local_image = local_image.transpose(local_dim_order)
        local_flip = global_flip[other_transformer.axis.dim_order]
        local_flip = np.logical_xor(local_flip,
                                    other_transformer.axis.dim_flip)

        # Flip dimensions where necessary
        local_image = local_image.flip(local_flip)

        return local_image

    def image_to_global(self, local_image):
        """Convert local coordinates to global coordinates"""

        # Flip dimensions where necessary
        local_image = local_image.flip(self.axis.dim_flip)

        # Reverse permute dimensions of local coordinates
        global_image = local_image.transpose(self.axis.reverse_dim_order)

        return global_image


class Axis(object):
    """Defines coordinate system used by image coordinates"""

    def __init__(self, dim_order, dim_flip):
        self.dim_order = dim_order
        self.dim_flip = dim_flip
        self.reverse_dim_order = np.argsort(dim_order).tolist()

    def to_condensed_format(self):
        """Creates a condensed Axis array for this Axis"""
        return [-1 - dim if flip else 1 + dim for dim, flip in
                zip(self.dim_order, self.dim_flip)]

    @staticmethod
    def from_condensed_format(dim_order_and_flip):
        """Creates an Axis from a condensed axis array"""
        if np.any(np.equal(dim_order_and_flip, 0)):
            raise ValueError('Dimensions are numbered from 1')
        dim_order = [abs(d) - 1 for d in dim_order_and_flip]
        dim_flip = [d < 0 for d in dim_order_and_flip]
        return Axis(dim_order=dim_order, dim_flip=dim_flip)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        return False

    def __ne__(self, other):
        return not self.__eq__(other)
