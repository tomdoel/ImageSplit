# -*- coding: utf-8 -*-

import unittest

from utils.utilities import get_linear_byte_offset


class TestUtilities(unittest.TestCase):
    """Tests for utilities"""

    def test_get_linear_byte_offset(self):
        self.assertEqual(get_linear_byte_offset([11, 22, 33], 4, [1, 2, 3]),
                         (1 + 2 * 11 + 3 * 11 * 22) * 4)
        self.assertEqual(
            get_linear_byte_offset([11, 22, 33, 44], 4, [1, 2, 3, 4]),
            (1 + 2 * 11 + 3 * 11 * 22 + 4 * 11 * 22 * 33) * 4)
        self.assertEqual(get_linear_byte_offset([11, 22, 33], 1, [1, 2, 3]),
                         (1 + 2 * 11 + 3 * 11 * 22) * 1)
        self.assertEqual(get_linear_byte_offset([11, 22, 33], 4, [0, 2, 3]),
                         (0 + 2 * 11 + 3 * 11 * 22) * 4)
        self.assertEqual(
            get_linear_byte_offset([55, 301, 999], 7, [14, 208, 88]),
            (14 + 208 * 55 + 88 * 55 * 301) * 7)


if __name__ == '__main__':
    unittest.main()

