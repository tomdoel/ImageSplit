from unittest import TestCase

from niftysplit.image.combined_image import CoordinateTransformer
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
        ct = CoordinateTransformer(origin, size, order, flip)

        o_l_start, o_l_size = ct.to_local(g_start, g_size)
        self.assertTrue(np.array_equal(o_l_start, l_start))
        self.assertTrue(np.array_equal(o_l_size, l_size))

        o_g_start, o_g_size = ct.to_global(l_start, l_size)
        self.assertTrue(np.array_equal(o_g_start, g_start))
        self.assertTrue(np.array_equal(o_g_size, g_size))
