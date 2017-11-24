# coding=utf-8
"""A wrapper for a multi-dimensional image with an origin offset"""

import numpy as np


class SmartImage(object):
    """Image wrapper which converts between Axes"""

    def __init__(self, start, size, image, transformer):
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

    def set_sub_image(self, sub_image):
        """Replaces part of the image with the corresponding subimage"""

        if self.image is None:
            self.image = np.zeros(shape=self.size, dtype=sub_image.image.dtype)

        # Transform the image to our local coordinate system
        local_subimage = self._transform_sub_image(sub_image)
        start, size = self._transform_coords(sub_image)

        # Test if image is in bounds
        start_indices = np.subtract(start, self.origin)
        end_indices = np.add(start_indices, size)
        if np.any(np.less(start_indices, 0)) \
                or np.any(np.greater(end_indices, self.size)):
            raise ValueError("Subimage is not contained within the main image")

        # Set the part of the image to this subimage
        selector = tuple([slice(s, e) for s, e in
                          zip(start_indices, end_indices)])
        self.image[selector] = local_subimage

    def _transform_coords(self, sub_image):
        return sub_image.coords_to_other(self._transformer)

    def _transform_sub_image(self, sub_image):
        return sub_image.transform_to_other(self._transformer)


class ImageWrapper(object):
    """Multi-dimensional image array with an origin"""

    def __init__(self, origin, image_size=None, image=None):
        self.origin = origin
        if image is not None:
            self.size = list(np.shape(image))
        else:
            self.size = image_size
        self.image = image

    def get_sub_image(self, start, size):
        """Returns the corresponding subimage"""

        start_indices = np.subtract(start, self.origin)
        end_indices = np.add(start_indices, np.array(size))
        if np.any(np.less(start_indices,
                          np.zeros_like(start_indices))) \
                or np.any(np.greater(end_indices, self.size)):
            raise ValueError("Subimage is not contained within the main image")
        selector = tuple([slice(start, end) for start, end in
                          zip(start_indices, end_indices)])
        return ImageWrapper(origin=start, image=self.image[selector])

    def set_sub_image(self, sub_image):
        """Replaces part of the image with the corresponding subimage"""

        if self.image is None:
            self.image = np.zeros(shape=self.size, dtype=sub_image.image.dtype)

        # Transform the image to our local coordinate system
        local_subimage = self._transform_sub_image(sub_image)
        start, size = self._transform_coords(sub_image)

        # Test if image is in bounds
        start_indices = np.subtract(start, self.origin)
        end_indices = np.add(start_indices, size)
        if np.any(np.less(start_indices, 0)) \
                or np.any(np.greater(end_indices, self.size)):
            raise ValueError("Subimage is not contained within the main image")

        # Set the part of the image to this subimage
        selector = tuple([slice(s, e) for s, e in
                          zip(start_indices, end_indices)])
        self.image[selector] = local_subimage

    def _transform_coords(self, sub_image):
        return zip(sub_image.origin, sub_image.size)

    def _transform_sub_image(self, sub_image):
        return sub_image.image
