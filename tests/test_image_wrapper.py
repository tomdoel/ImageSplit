# coding=utf-8

"""Unit tests"""

from unittest import TestCase
import numpy as np

from niftysplit.image.image_wrapper import ImageWrapper
import itertools


class TestImageWrapper(TestCase):
    def test_set_sub_image(self):
        test_array = np.array([[1, 2, 3, 4, 5, 6], [21, 22, 23, 24, 25, 26], [31, 32, 33, 34, 35, 36], [41, 42, 43, 44, 45, 46]])
        main_image = ImageWrapper([1, 2], image=test_array)
        sub_image = ImageWrapper([2, 3], image=np.array([[7, 8], [9, 10]]))
        main_image.set_sub_image(sub_image)
        compare_array = np.array([[1, 2, 3, 4, 5, 6], [21, 7, 8, 24, 25, 26], [31, 9, 10, 34, 35, 36], [41, 42, 43, 44, 45, 46]])
        self.assertTrue(np.array_equal(compare_array, main_image.image))

        all_dim_sizes = [1, 37]
        all_origins = [0, 17]
        for num_dimensions in [2, 3, 4]:

            multi_dimensions = [all_dim_sizes] * num_dimensions
            multi_origins = [all_origins] * num_dimensions
            dim_sizes_list = list(itertools.product(*multi_dimensions))
            offsets_list = list(itertools.product(*multi_origins))

            for main_dim_size in dim_sizes_list:
                for sub_dim_size in dim_sizes_list:
                    for main_origin in offsets_list:
                        for sub_origin in offsets_list:

                            self.check_image(num_dimensions, main_dim_size, main_origin, sub_dim_size, sub_origin)

    def check_image(self, num_dimensions, main_dim_size, main_origin,
                    sub_dim_size, sub_origin):
        raw_array = np.reshape(np.arange(0, np.prod(main_dim_size)), main_dim_size)
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


