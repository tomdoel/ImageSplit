# -*- coding: utf-8 -*-

import unittest

from parameterized import parameterized
import numpy as np

from niftysplit.image.combined_image import Limits
from niftysplit.utils.utilities import file_linear_byte_offset, rescale_image


class TestUtilities(unittest.TestCase):
    """Tests for utilities"""

    def test_get_linear_byte_offset(self):
        self.assertEqual(file_linear_byte_offset([11, 22, 33], 4, [1, 2, 3]),
                         (1 + 2 * 11 + 3 * 11 * 22) * 4)
        self.assertEqual(
            file_linear_byte_offset([11, 22, 33, 44], 4, [1, 2, 3, 4]),
            (1 + 2 * 11 + 3 * 11 * 22 + 4 * 11 * 22 * 33) * 4)
        self.assertEqual(file_linear_byte_offset([11, 22, 33], 1, [1, 2, 3]),
                         (1 + 2 * 11 + 3 * 11 * 22) * 1)
        self.assertEqual(file_linear_byte_offset([11, 22, 33], 4, [0, 2, 3]),
                         (0 + 2 * 11 + 3 * 11 * 22) * 4)
        self.assertEqual(
            file_linear_byte_offset([55, 301, 999], 7, [14, 208, 88]),
            (14 + 208 * 55 + 88 * 55 * 301) * 7)

    @parameterized.expand([
        [np.uint8, [1, 2, 3], Limits(0, 255), [1, 2, 3]],
        [np.uint8, [0, 2, 3], Limits(0, 255), [0, 2, 3]],
        [np.uint8, [-1, 2, 3], Limits(0, 255), [0, 2, 3]],
        [np.uint8, [0, 100, 300], Limits(100, 355), [0, 0, 200]],
        [np.uint8, [1, 2, 3], Limits(0, 255), [1, 2, 3]],
        [np.uint8, [0, 2, 3], Limits(0, 255), [0, 2, 3]],
        [np.uint8, [-1, 2, 3], Limits(0, 255), [0, 2, 3]],
        [np.uint8, [0, 100, 300], Limits(100, 355), [0, 0, 200]],
        [np.int8, [-128, -127, 0, 127, 128, 129], Limits(-127, 128), [-128, -128, -1, 126, 127, 127]],
        [np.int8, [-129, -128, -127, 0, 127, 128, 129], Limits(-128, 127), [-128, -128, -127, 0, 127, 127, 127]],
        [np.uint16, [-1, 0, 1, 65535, 65536], Limits(0, 65535), [0, 0, 1, 65535, 65535]],
        [np.uint16, [-1, 0, 1, 100, 65535, 65536], Limits(0, 32767), [0, 0, 2, 200, 65535, 65535]],
        [np.uint16, [-1, 0, 1, 65535, 65536], Limits(-1, 65534), [0, 1, 2, 65535, 65535]],
        [np.int16, [-32769, -32768, -32767, 0, 1, 32766, 32767, 32768], Limits(-32768, 32767), [-32768, -32768, -32767, 0, 1, 32766, 32767, 32767]],
    ])
    def test_rescale(self, data_type, image_line, rescale_limits, expected):
        result = rescale_image(data_type, image_line, rescale_limits)
        self.assertTrue(np.array_equal(expected, result))
