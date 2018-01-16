#!/usr/bin/env python
# coding=utf-8
"""
Utility for reading and writing data to JSON files

Author: Tom Doel
Copyright UCL 2017

"""

import json


def write_json(filename, data):
    """Writes data to a file in JSON format"""
    with open(filename, 'w') as data_file:
        json.dump(data, data_file, ensure_ascii=False)


def read_json(filename):
    """Reads data from a file in JSON format"""
    with open(filename) as data_file:
        return json.load(data_file)
