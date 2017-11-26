# coding=utf-8

"""Unit tests"""

from unittest import TestCase
import numpy as np
from parameterized import parameterized, param

from common_test_functions import create_dummy_image
from niftysplit.image.image_wrapper import ImageWrapper, ImageStorage


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
        param(main_dim_size=[30, 30, 30, 30, 30], main_origin=[1, 2, 3, 4, 0], sub_dim_size=[5, 4, 6, 7, 2], sub_origin=[2, 3, 4, 5, 4]),


        param(main_dim_size=[10], main_origin=[1], sub_dim_size=[50], sub_origin=[3]),
        param(main_dim_size=[11, 12], main_origin=[2, 3], sub_dim_size=[5, 7], sub_origin=[4, -3]),
        param(main_dim_size=[1, 2, 3], main_origin=[1, 2, 3], sub_dim_size=[1, 2, 3], sub_origin=[-1, 2, 3]),
        param(main_dim_size=[10, 11, 12, 13], main_origin=[1, 2, 3, 4], sub_dim_size=[5, 46, 6, 7], sub_origin=[2, 3, 4, 5]),
        param(main_dim_size=[30, 30, 30, 30, 30], main_origin=[1, 2, 3, 4, 0], sub_dim_size=[5, 4, 65, 7, 2], sub_origin=[2, 3, 4, 5, 4])
    ])
    def test_set_sub_image(self, main_dim_size, main_origin, sub_dim_size, sub_origin):
        num_dimensions = len(main_dim_size)
        main_image = create_dummy_image(main_dim_size, origin=main_origin)
        main_image_unset = ImageWrapper(main_origin, image_size=main_dim_size)
        sub_image = create_dummy_image(sub_dim_size, origin=sub_origin, value_base=1000)
        is_valid = True
        for dim_index in range(0, num_dimensions):
            if sub_origin[dim_index] < main_origin[dim_index] or \
                                    sub_origin[dim_index] + sub_dim_size[dim_index] > \
                                    main_origin[dim_index] + main_dim_size[dim_index]:
                is_valid = False
        if is_valid:
            main_image.set_sub_image(sub_image)
            main_image_unset.set_sub_image(sub_image)
            self.assertTrue(
                np.array_equal(
                    main_image.get_sub_image(sub_origin, sub_dim_size).image,
                    sub_image.image))
            self.assertTrue(
                np.array_equal(
                    main_image_unset.get_sub_image(sub_origin, sub_dim_size).image,
                    sub_image.image))

        else:
            try:
                main_image.set_sub_image(sub_image)
                self.fail("Expeced this function call to fail")
            except ValueError:
                pass
            try:
                main_image.get_sub_image(sub_origin, sub_dim_size).image
                self.fail("Expeced this function call to fail")
            except ValueError:
                pass

