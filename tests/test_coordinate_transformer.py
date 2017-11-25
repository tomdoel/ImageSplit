from unittest import TestCase

from image.image_wrapper import ImageStorage
from niftysplit.image.combined_image import CoordinateTransformer, Axis
from parameterized import parameterized, param
import numpy as np


class TestCoordinateTransformer(TestCase):
    @parameterized.expand([
        param(origin=[0, 0, 0], size=[10, 10, 10], order=[0, 1, 2], flip=[0, 0, 0], g_start=[0, 0, 0], g_size=[10, 10, 10], l_start=[0, 0, 0], l_size=[10, 10, 10]),
        param(origin=[0, 0, 0], size=[20, 20, 20], order=[0, 1, 2], flip=[0, 0, 0], g_start=[0, 1, 2], g_size=[5, 5, 5], l_start=[0, 1, 2], l_size=[5, 5, 5]),
        param(origin=[0, 1, 2], size=[20, 20, 20], order=[0, 1, 2], flip=[0, 0, 0], g_start=[0, 1, 2], g_size=[5, 6, 7], l_start=[0, 0, 0], l_size=[5, 6, 7]),
        param(origin=[6, 3, 1], size=[20, 25, 35], order=[0, 1, 2], flip=[0, 0, 0], g_start=[7, 9, 11], g_size=[5, 6, 7], l_start=[1, 6, 10], l_size=[5, 6, 7]),
        param(origin=[6, 3, 1], size=[20, 25, 35], order=[0, 2, 1], flip=[0, 0, 0], g_start=[7, 9, 11], g_size=[5, 6, 7], l_start=[1, 10, 6], l_size=[5, 7, 6]),
        param(origin=[6, 3, 1], size=[20, 25, 35], order=[2, 0, 1], flip=[0, 0, 0], g_start=[7, 9, 11], g_size=[5, 6, 7], l_start=[10, 1, 6], l_size=[7, 5, 6]),
        param(origin=[0, 0, 0], size=[5, 6, 7], order=[0, 1, 2], flip=[1, 0, 0], g_start=[1, 2, 3], g_size=[2, 3, 4], l_start=[3, 2, 3], l_size=[2, 3, 4]),
        param(origin=[1, 0, 0], size=[5, 6, 7], order=[0, 1, 2], flip=[1, 0, 0], g_start=[1, 2, 3], g_size=[2, 3, 4], l_start=[4, 2, 3], l_size=[2, 3, 4]),
        param(origin=[0, 0, 0], size=[5, 6, 7], order=[0, 1, 2], flip=[1, 1, 0], g_start=[1, 2, 3], g_size=[2, 3, 4], l_start=[3, 3, 3], l_size=[2, 3, 4]),
        param(origin=[6, 3, 1], size=[20, 25, 35], order=[2, 0, 1], flip=[1, 0, 0], g_start=[7, 9, 11], g_size=[5, 6, 7], l_start=[24, 1, 6], l_size=[7, 5, 6])
    ])
    def test_local_global(self, origin, size, order, flip, g_start, g_size, l_start, l_size):
        ct = CoordinateTransformer(origin, size, Axis(order, flip))

        o_l_start, o_l_size = ct.to_local(g_start, g_size)
        self.assertTrue(np.array_equal(o_l_start, l_start))
        self.assertTrue(np.array_equal(o_l_size, l_size))

        o_g_start, o_g_size = ct.to_global(l_start, l_size)
        self.assertTrue(np.array_equal(o_g_start, g_start))
        self.assertTrue(np.array_equal(o_g_size, g_size))

    @parameterized.expand([
        param(origin=[0, 0, 0], size=[10, 10, 10], order=[0, 1, 2], flip=[0, 0, 0], g_start=[0, 0, 0], g_size=[10, 10, 10], l_start=[0, 0, 0], l_size=[10, 10, 10]),
        param(origin=[0, 0, 0], size=[20, 20, 20], order=[0, 1, 2], flip=[0, 0, 0], g_start=[0, 1, 2], g_size=[5, 5, 5], l_start=[0, 1, 2], l_size=[5, 5, 5]),
        param(origin=[0, 1, 2], size=[20, 20, 20], order=[0, 1, 2], flip=[0, 0, 0], g_start=[0, 1, 2], g_size=[5, 6, 7], l_start=[0, 0, 0], l_size=[5, 6, 7]),
        param(origin=[6, 3, 1], size=[20, 25, 35], order=[0, 1, 2], flip=[0, 0, 0], g_start=[7, 9, 11], g_size=[5, 6, 7], l_start=[1, 6, 10], l_size=[5, 6, 7]),
        param(origin=[6, 3, 1], size=[20, 25, 35], order=[0, 2, 1], flip=[0, 0, 0], g_start=[7, 9, 11], g_size=[5, 6, 7], l_start=[1, 10, 6], l_size=[5, 7, 6]),
        param(origin=[6, 3, 1], size=[20, 25, 35], order=[2, 0, 1], flip=[0, 0, 0], g_start=[7, 9, 11], g_size=[5, 6, 7], l_start=[10, 1, 6], l_size=[7, 5, 6]),
        param(origin=[0, 0, 0], size=[5, 6, 7], order=[0, 1, 2], flip=[1, 0, 0], g_start=[1, 2, 3], g_size=[2, 3, 4], l_start=[3, 2, 3], l_size=[2, 3, 4]),
        param(origin=[1, 0, 0], size=[5, 6, 7], order=[0, 1, 2], flip=[1, 0, 0], g_start=[1, 2, 3], g_size=[2, 3, 4], l_start=[4, 2, 3], l_size=[2, 3, 4]),
        param(origin=[0, 0, 0], size=[5, 6, 7], order=[0, 1, 2], flip=[1, 1, 0], g_start=[1, 2, 3], g_size=[2, 3, 4], l_start=[3, 3, 3], l_size=[2, 3, 4]),
        param(origin=[6, 3, 1], size=[20, 25, 35], order=[2, 0, 1], flip=[1, 0, 0], g_start=[7, 9, 11], g_size=[5, 6, 7], l_start=[24, 1, 6], l_size=[7, 5, 6])
    ])
    def test_image(self, origin, size, order, flip, g_start, g_size, l_start, l_size):
        ct = CoordinateTransformer(origin, size, Axis(order, flip))

        transformed_start, transformed_size = ct.to_local(g_start, size)
        global_image = np.reshape(np.arange(0, np.prod(size)), size)
        local_image = ct.image_to_local(ImageStorage(global_image))
        np.testing.assert_array_equal(size, global_image.shape)
        np.testing.assert_array_equal(transformed_size, local_image.get_size())
        test_image = np.transpose(global_image, order)
        for index, flip in enumerate(flip):
            if flip:
                test_image = np.flip(test_image, index)
        np.testing.assert_array_equal(test_image, local_image.get_raw())

        global_image_2 = ct.image_to_global(local_image)
        np.testing.assert_array_equal(global_image, global_image_2.get_raw())

    @parameterized.expand([
        param(dim=[0, 1, 2], flip=[0, 0, 0], expected=[[[0, 1, 2], [3, 4, 5], [6, 7, 8], [9, 10, 11]], [[20, 21, 22], [23, 24, 25], [26, 27, 28], [29, 30, 31]]]),
        param(dim=[0, 2, 1], flip=[0, 0, 0], expected=[[[0, 3, 6, 9], [1, 4, 7, 10], [2, 5, 8, 11]], [[20, 23, 26, 29], [21, 24, 27, 30], [22, 25, 28, 31]]]),
        param(dim=[0, 2, 1], flip=[0, 0, 1], expected=[[[9, 6, 3, 0], [10, 7, 4, 1], [11, 8, 5, 2]], [[29, 26, 23, 20], [30, 27, 24, 21], [31, 28, 25, 22]]]),
        param(dim=[1, 2, 0], flip=[0, 0, 0], expected=[[[0, 20], [1, 21], [2, 22]], [[3, 23], [4, 24], [5, 25]], [[6, 26], [7, 27], [8, 28]], [[9, 29], [10, 30], [11, 31]]]),
        param(dim=[1, 2, 0], flip=[0, 0, 1], expected=[[[20, 0], [21, 1], [22, 2]], [[23, 3], [24, 4], [25, 5]], [[26, 6], [27, 7], [28, 8]], [[29, 9], [30, 10], [31, 11]]]),
        param(dim=[0, 1, 2], flip=[0, 1, 0], expected=[[[9, 10, 11], [6, 7, 8], [3, 4, 5], [0, 1, 2]], [[29, 30, 31], [26, 27, 28], [23, 24, 25], [20, 21, 22]]]),
        param(dim=[0, 1, 2], flip=[1, 0, 0], expected=[[[20, 21, 22], [23, 24, 25], [26, 27, 28], [29, 30, 31]], [[0, 1, 2], [3, 4, 5], [6, 7, 8], [9, 10, 11]]]),
        param(dim=[0, 1, 2], flip=[0, 0, 1], expected=[[[2, 1, 0], [5, 4, 3], [8, 7, 6], [11, 10, 9]], [[22, 21, 20], [25, 24, 23], [28, 27, 26], [31, 30, 29]]])
    ])
    def test_flip_explicit(self, dim, flip, expected):
        global_image = np.array([[[0, 1, 2], [3, 4, 5], [6, 7, 8], [9, 10, 11]],
                        [[20, 21, 22], [23, 24, 25], [26, 27, 28], [29, 30, 31]]])

        ct = CoordinateTransformer(np.zeros_like(dim), np.shape(global_image), Axis(dim, flip))
        local_image = ct.image_to_local(ImageStorage(global_image.copy()))
        np.testing.assert_array_equal(local_image.get_raw(), np.array(expected))
        np.testing.assert_array_equal(local_image.get_raw(), np.array(expected))

        global_image_2 = ct.image_to_global(local_image)
        np.testing.assert_array_equal(global_image, global_image_2.get_raw())
