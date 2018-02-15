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
        ['v0.1-1-gabcde', '0.1+1.gabcde'],
        ['v0.1-G-gabcde', None],
        ['v0.1-1-gabcdek', None],
        ['v0.1-1-gabcde-dirty', '0.1+1.gabcde.dirty'],
        ['v0.1-1-gabcde-broken', '0.1+1.gabcde.broken'],
        ['v0.1-1-gabcde-brokenn', None],
        ['gabcde', 'DEFAULT+0.gabcde'],
        ['gabcde-dirty', 'DEFAULT+0.gabcde.dirty'],
    ])
    def test_parse_describe(self, output, expected, default='DEFAULT'):
        self.assertEqual(versioning._parse_describe(output, default), expected)

    @parameterized.expand([
        ['0.1', True],
        ['0.1dev', True],
        ['0.1s', False],
        ['0.1+1.gabcde', True],
        ['0.1+1-gabcde', False],
        ['0.1+1.ggabcde', False],
        ['0.1+G.gabcde', False],
        ['0.1+1.gabcdek', False],
        ['0.1+1.gabcde.dirty', True],
        ['0.1+1.dirty', False],
        ['0.1+1.gabcde.broken', True],
        ['0.1+1.gabcde.brokenn', False],
        ['0.1+5.g377bc35', True],
        ['gabcde', False],
        ['gabcde.dirty', False],
    ])
    def test_check_pip_version(self, version_string, expected):
        self.assertEqual(versioning._check_pip_version(version_string),
                         expected)
