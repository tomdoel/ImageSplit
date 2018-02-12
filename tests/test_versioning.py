# -*- coding: utf-8 -*-

import unittest

import re
from parameterized import parameterized

from imagesplit.utils import versioning
from imagesplit.utils.versioning import VERSION_TAG_REGEX


class TestVersioning(unittest.TestCase):
    """Tests for utilities"""

    @parameterized.expand([
        ['v0.1', True],
        ['v0.1dev', True],
        ['v1.0', True],
        ['v1.0dev', True],
        ['v1.0deva', False],
        ['1.0deva', False],
        ['1.0', False],
        ['1.0dev', False],
        ['dev', False],
    ])
    def test_tag_regex(self, tag, is_valid):
        self.assertTrue(is_valid == bool(re.match(VERSION_TAG_REGEX, tag)))

    @parameterized.expand([
        ['v0.1', '0.1'],
        ['v0.1s', None],
        ['v0.1-1-abcde', '0.1+1.abcde'],
        ['v0.1-G-abcde', None],
        ['v0.1-1-abcdek', None],
        ['v0.1-1-abcde-dirty', '0.1+1.abcde-dirty'],
        ['v0.1-1-abcde-broken', '0.1+1.abcde-broken'],
        ['v0.1-1-abcde-brokenn', None],
        ['abcde', 'DEFAULT+0.abcde'],
    ])
    def test_parse_describe(self, output, expected, default='DEFAULT'):
        self.assertEqual(versioning._parse_describe(output, default), expected)
