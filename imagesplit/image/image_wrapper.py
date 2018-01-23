# coding=utf-8
"""A wrapper for a multi-dimensional image with an origin offset"""
from abc import abstractmethod

from PIL import Image
import numpy as np


class ImageWrapperBase(object):
    """Multi-dimensional image array with an origin"""

    def __init__(self, origin, image_size=None, image=None):
        self.origin = origin
        if image is not None:
            self.size = image.get_size()
        else:
            self.size = image_size
        self.image = image

    def set_sub_image(self, sub_image):
        """Replaces part of the image with the corresponding subimage"""

        if self.image is None:
            self.image = ImageStorage.create_empty(
                size=self.size,
                dtype=sub_image.image.get_type())

        # Transform the image to our local coordinate system
        local_subimage = self.transform_sub_image(sub_image)
        start, size = self.transform_coords(sub_image)

        # Test if image is in bounds
        start_indices = np.subtract(start, self.origin)
        end_indices = np.add(start_indices, size)
        if np.any(np.less(start_indices, 0)) \
                or np.any(np.greater(end_indices, self.size)):
            raise ValueError("Subimage is not contained within the main image")

        # Set the part of the image to this subimage
        selector = tuple([slice(s, e) for s, e in
                          zip(start_indices, end_indices)])
        self.image.set(selector, local_subimage)

    @abstractmethod
    def transform_coords(self, sub_image):
        """Transforms sub_image start, size to this coordinate system"""
        pass

    @abstractmethod
    def transform_sub_image(self, sub_image):
        """Transforms sub_image to this coordinate system"""
        pass


class ImageWrapper(ImageWrapperBase):
    """Multi-dimensional image array with an origin"""

    def __init__(self, origin, image_size=None, image=None):
        super(ImageWrapper, self).__init__(origin=origin,
                                           image_size=image_size,
                                           image=image)

    def get_sub_image(self, start, size):
        """Returns the corresponding subimage"""

        start_indices = np.subtract(start, self.origin)
        end_indices = np.add(start_indices, np.array(size))
        if np.any(np.less(start_indices,
                          np.zeros_like(start_indices))) \
                or np.any(np.greater(end_indices, self.size)):
            raise ValueError("Subimage is not contained within the main image")
        selector = tuple([slice(s, e) for s, e in
                          zip(start_indices, end_indices)])
        return ImageWrapper(origin=start, image=self.image.get(selector))

    def transform_coords(self, sub_image):
        return sub_image.origin, sub_image.size

    def transform_sub_image(self, sub_image):
        return sub_image.image


class SmartImage(ImageWrapper):
    """Image wrapper which converts between Axes"""

    def __init__(self, start, size, image, transformer):
        super(SmartImage, self).__init__(origin=start, image_size=size,
                                         image=image)
        self.size = size
        self.origin = start
        self.image = image
        self._transformer = transformer

    def transform_to_other(self, transformer):
        """Returns this image transformed to a different local system"""

        if self.image is None:
            raise ValueError("Image has not been created")

        return self._transformer.image_to_other(self.image, transformer)

    def coords_to_other(self, transformer):
        """Converts coordinates to another system"""

        return self._transformer.to_other(self.origin, self.size, transformer)

    def transform_coords(self, sub_image):
        return sub_image.coords_to_other(self._transformer)

    def transform_sub_image(self, sub_image):
        return sub_image.transform_to_other(self._transformer)


class ImageStorage(object):
    """Abstraction for storing image data in an arbitrary orientation

    Allows storing of data without assuming the order in which the dimensions
    are stored in memory or indexed. This allows images to be indexed using
    the [x,y,z] convention while the numpy ordering is actually [z,y,x]

    """

    def __init__(self, numpy_image=None):
        self._numpy_image = numpy_image

    def set(self, selector, image):
        """Replaces part of the image data using the specified selectors"""

        self._numpy_image[list(reversed(selector))] = image.get_raw()

    def get(self, selector):
        """Returns part of the image data using the specified selectors"""

        return ImageStorage(self._numpy_image[list(reversed(selector))])

    def get_size(self):
        """Returns the image size in the global dimension ordering scheme"""

        return list(reversed(list(np.shape(self._numpy_image))))

    def get_type(self):
        """Returns the underlying data type"""

        return self._numpy_image.dtype

    def get_raw(self):
        """Return raw image array; might not be in global dimension ordering"""

        return self._numpy_image

    def get_image(self):
        """Creates and returns an Image object for this data"""

        return Image.fromarray(np.transpose(self._numpy_image))

    def get_raw_image(self):
        """Return raw image array in the standard PIL dimension ordering"""

        transposed = np.transpose(self._numpy_image)
        if np.ndim(transposed) == 3 and np.shape(transposed)[2] == 1:
            return np.squeeze(transposed, 2)
        return transposed

    def transpose(self, order):
        """Return a transpose of the image data using global ordering"""

        order = list(np.subtract(len(order) - 1, order))
        return ImageStorage(np.transpose(self._numpy_image,
                                         list(reversed(order))))

    def flip(self, do_flip):
        """Return a copy of image data flipped using global ordering"""

        image = self._numpy_image
        for index, flip in enumerate(do_flip):
            if flip:
                image = np.flip(image, len(do_flip) - 1 - index)
        return ImageStorage(image)

    def reshape(self, new_shape):
        """Return a reshaping of the image data using global ordering"""

        return ImageStorage(
            np.reshape(self._numpy_image, list(reversed(new_shape))))

    def __eq__(self, other):
        """Overrides the default implementation"""
        if isinstance(other, self.__class__):
            return np.array_equal(self._numpy_image, other.get_raw())
        return False

    def __ne__(self, other):
        """Overrides the default implementation"""
        return not self.__eq__(other)

    def copy(self):
        """Returns a new object with a copy of the underlying data"""

        return ImageStorage(self._numpy_image.copy())

    @classmethod
    def create_empty(cls, size, dtype):
        """Create empty object of the specified global size and data type"""

        raw = np.zeros(shape=list(reversed(size)), dtype=dtype)
        return cls(numpy_image=raw)

    @classmethod
    def from_raw_image(cls, raw, size=None):
        """Create ImageStorage object from this image data array"""

        if size and not np.array_equal(np.shape(raw),
                                       size[:np.size(np.shape(raw))]):
            raise ValueError('When loading an image, nonsingleton dimensions '
                             'must match size')
        # Add in singleton dimensions if required
        if size:
            raw = np.reshape(raw, size)
        return cls(np.transpose(raw))
