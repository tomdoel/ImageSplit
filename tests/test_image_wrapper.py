# coding=utf-8

"""Unit tests"""

from unittest import TestCase
import numpy as np
from parameterized import parameterized, param

from niftysplit.image.image_wrapper import ImageWrapper
import itertools


class TestImageWrapper(TestCase):

    @parameterized.expand([
        param(main_dim_size=[10], main_origin=[1], sub_dim_size=[5], sub_origin=[3]),
        param(main_dim_size=[11, 12], main_origin=[2, 3], sub_dim_size=[5, 7], sub_origin=[4, 3]),
        param(main_dim_size=[1, 2, 3], main_origin=[1, 2, 3], sub_dim_size=[1, 2, 3], sub_origin=[1, 2, 3]),
        param(main_dim_size=[20, 20, 20], main_origin=[0, 0, 0], sub_dim_size=[20, 20, 20], sub_origin=[0, 0, 0]),
        param(main_dim_size=[20, 20, 20], main_origin=[0, 0, 0], sub_dim_size=[19, 18, 17], sub_origin=[1, 2, 3]),
        param(main_dim_size=[1, 2, 3], main_origin=[1, 2, 3], sub_dim_size=[1, 2, 3], sub_origin=[1, 2, 3]),
        param(main_dim_size=[10, 11, 12], main_origin=[1, 2, 3], sub_dim_size=[5, 8, 3], sub_origin=[2, 3, 4]),
        param(main_dim_size=[10, 11, 12, 13], main_origin=[1, 2, 3, 4], sub_dim_size=[5, 4, 6, 7], sub_origin=[2, 3, 4, 5]),
        param(main_dim_size=[30, 30, 30, 30, 30], main_origin=[1, 2, 3, 4, 0], sub_dim_size=[5, 4, 6, 7, 2], sub_origin=[2, 3, 4, 5, 4])
    ])
    def test_set_sub_image(self, main_dim_size, main_origin, sub_dim_size, sub_origin):
        num_dimensions = len(main_dim_size)
        raw_array = np.arange(0, np.prod(main_dim_size)).reshape(main_dim_size)
        main_image = ImageWrapper(main_origin, image=raw_array)
        sub_raw_array = np.reshape(np.arange(1000, 1000 + np.prod(sub_dim_size)), sub_dim_size)
        sub_image = ImageWrapper(sub_origin, image=sub_raw_array)
        is_valid = True
        for dim_index in range(0, num_dimensions):
            if sub_origin[dim_index] < main_origin[dim_index] or \
                                    sub_origin[dim_index] + sub_dim_size[dim_index] > \
                                    main_origin[dim_index] + main_dim_size[dim_index]:
                is_valid = False
        if is_valid:
            main_image.set_sub_image(sub_image)
            self.assertTrue(
                np.array_equal(
                    main_image.get_sub_image(sub_origin, sub_raw_array.shape),
                    sub_image.image))

        else:
            try:
                main_image.set_sub_image(sub_image)
                self.fail("Expeced this function call to fail")
            except ValueError:
                pass


