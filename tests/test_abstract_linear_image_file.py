from unittest import TestCase

from parameterized import parameterized, param

from tests.common_test_functions import create_dummy_image, \
    SimpleMockSource, create_empty_image
from niftysplit.file.image_file_reader import LinearImageFileReader
from niftysplit.image.image_wrapper import ImageWrapper
import numpy as np


class MockAbstractLinearImageFile(LinearImageFileReader):
    def __init__(self, image):
        super(MockAbstractLinearImageFile, self).__init__(image.size)
        self.image = image

    def close_file(self):
        pass

    def read_line(self, start, num_voxels):
        size = np.ones_like(start)
        size[0] = num_voxels
        return self.image.get_sub_image(start, size).image.flatten()

    def write_line(self, start, image_line):
        size = np.zeros_like(start)
        size[0] = len(image_line)
        self.image.set_sub_image(ImageWrapper(origin=start, image=image_line))


class TestAbstractLinearImageFile(TestCase):
    @parameterized.expand([
        param(image_size=[5], start=[0], size=[5]),
        param(image_size=[5], start=[0], size=[1]),
        param(image_size=[5], start=[1], size=[4]),
        param(image_size=[5, 6], start=[1, 2], size=[4, 3]),
        param(image_size=[5, 9, 8], start=[1, 2, 3], size=[4, 3, 5]),
        param(image_size=[5, 9, 8,11], start=[1, 2, 3,5], size=[4, 3, 5,6])
    ])
    def test_read_image(self, image_size, start, size):
        dummy_image = create_dummy_image(image_size)
        linear_image_file = MockAbstractLinearImageFile(dummy_image)
        read_image = linear_image_file.read_image(start, size)
        test_image = dummy_image.get_sub_image(start, size)
        np.testing.assert_equal(read_image, test_image.image)

    @parameterized.expand([
        param(image_size=[5]),
        param(image_size=[5]),
        param(image_size=[5]),
        param(image_size=[5, 6]),
        param(image_size=[5, 9, 8]),
        param(image_size=[5, 9, 8, 11])
    ])
    def test_write_image(self, image_size):

        initial_image = create_empty_image(image_size)
        linear_image_file = MockAbstractLinearImageFile(initial_image)

        dummy_image = create_dummy_image(image_size)
        source = SimpleMockSource(dummy_image)

        linear_image_file.write_image(source)
        np.testing.assert_equal(initial_image.image, dummy_image.image)
