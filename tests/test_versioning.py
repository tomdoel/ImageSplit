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
