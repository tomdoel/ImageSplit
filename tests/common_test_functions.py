import numpy as np

from niftysplit.file.linear_image_file import AbstractImageFile
from niftysplit.image.combined_image import Source, CoordinateTransformer
from niftysplit.image.image_wrapper import ImageWrapper


class FakeImageFile(AbstractImageFile, Source):
    """Fake data source"""

    def __init__(self, descriptor, global_image=None):
        self.global_image = global_image
        self.descriptor = descriptor
        self.open = True
        self.transformer = CoordinateTransformer(
            self.descriptor.origin_start, self.descriptor.image_size,
            self.descriptor.dim_order, self.descriptor.dim_flip)

    def read_image(self, start, size):
        if self.global_image:
            start_global, size_global = self.transformer.to_global(start, size)
            return self.global_image.get_sub_image(start_global, size_global).image
        else:
            return None

    def write_image(self, data_source):
        pass

    def close(self):
        self.open = False


class SimpleMockSource(Source):
    """Fake data source"""

    def __init__(self, global_image=None):
        self.global_image = global_image
        self.open = True

    def read_image(self, start, size):
        if self.global_image:
            return self.global_image.get_sub_image(start, size).image
        else:
            return None

    def write_image(self, data_source):
        pass

    def close(self):
        self.open = False


def create_empty_image(size):
    return ImageWrapper(np.zeros_like(size), image=np.zeros(size))

def create_dummy_image(size):
    return ImageWrapper(np.zeros_like(size), image=np.arange(0, np.prod(size)).reshape(size))
