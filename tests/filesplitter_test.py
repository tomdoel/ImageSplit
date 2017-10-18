# -*- coding: utf-8 -*-

from tools.file_splitter import get_number_of_blocks, get_block_coordinate_range, get_image_block_ranges, \
    get_suggested_block_size

import unittest


class TestFileSplitter(unittest.TestCase):
    """Tests for FileSplitter"""

    def test_get_number_of_blocks(self):
        self.assertEqual(get_number_of_blocks([10, 10, 10], [5, 5, 5]), [2, 2, 2])
        self.assertEqual(get_number_of_blocks([9, 9, 9], [5, 5, 5]), [2, 2, 2])
        self.assertEqual(get_number_of_blocks([11, 11, 11], [5, 5, 5]), [3, 3, 3])
        self.assertEqual(get_number_of_blocks([2, 2, 2], [1, 2, 3]), [2, 1, 1])
        self.assertEqual(get_number_of_blocks([2001, 2000, 1999], [500, 500, 500]), [5, 4, 4])

    def test_get_block_coordinate_range(self):
        self.assertEqual(get_block_coordinate_range(0, 5, 1, 5), (0, 4, 0, 0))
        self.assertEqual(get_block_coordinate_range(0, 5, 1, 10), (0, 5, 0, 1))
        self.assertEqual(get_block_coordinate_range(1, 5, 1, 10), (4, 9, 1, 0))
        self.assertEqual(get_block_coordinate_range(0, 5, 1, 9), (0, 5, 0, 1))
        self.assertEqual(get_block_coordinate_range(1, 5, 1, 9), (4, 8, 1, 0))

    def test_get_suggested_block_size(self):
        self.assertEqual(get_suggested_block_size([5, 5, 5], [2, 2, 2]), [3, 3, 3])
        self.assertEqual(get_suggested_block_size([5, 5, 5], [2, 3, 4]), [3, 2, 2])
        self.assertEqual(get_suggested_block_size([99, 100, 101], [3, 4, 5]), [33, 25, 21])

    def test_get_image_block_ranges(self):
        self.assertEqual(get_image_block_ranges([5, 5, 5], [4, 5, 6], [0, 0, 0]),
                         [[(0, 2, 0, 0), (0, 4, 0, 0), (0, 4, 0, 0)], [(3, 4, 0, 0), (0, 4, 0, 0), (0, 4, 0, 0)]])
        self.assertEqual(get_image_block_ranges([5, 5, 5], [4, 5, 6], [2, 2, 2]),
                         [[(0, 4, 0, 2), (0, 4, 0, 0), (0, 4, 0, 0)], [(1, 4, 2, 0), (0, 4, 0, 0), (0, 4, 0, 0)]])
        self.assertEqual(get_image_block_ranges([999, 1000, 1001], [500, 500, 500], [0, 0, 0]),
                         [[(0, 499, 0, 0), (0, 499, 0, 0), (0, 333, 0, 0)],
                          [(0, 499, 0, 0), (0, 499, 0, 0), (334, 667, 0, 0)],
                          [(0, 499, 0, 0), (0, 499, 0, 0), (668, 1000, 0, 0)],
                          [(0, 499, 0, 0), (500, 999, 0, 0), (0, 333, 0, 0)],
                          [(0, 499, 0, 0), (500, 999, 0, 0), (334, 667, 0, 0)],
                          [(0, 499, 0, 0), (500, 999, 0, 0), (668, 1000, 0, 0)],
                          [(500, 998, 0, 0), (0, 499, 0, 0), (0, 333, 0, 0)],
                          [(500, 998, 0, 0), (0, 499, 0, 0), (334, 667, 0, 0)],
                          [(500, 998, 0, 0), (0, 499, 0, 0), (668, 1000, 0, 0)],
                          [(500, 998, 0, 0), (500, 999, 0, 0), (0, 333, 0, 0)],
                          [(500, 998, 0, 0), (500, 999, 0, 0), (334, 667, 0, 0)],
                          [(500, 998, 0, 0), (500, 999, 0, 0), (668, 1000, 0, 0)]])


if __name__ == '__main__':
    unittest.main()

