#!/usr/bin/env python

#
# Copyright UCL 2017
# Author: Tom Doel
#

import json


def write_json(filename, data):
    with open(filename, 'w') as data_file:
        json.dump(data, data_file, ensure_ascii=False)


def read_json(filename):
    with open(filename) as data_file:
        return json.load(data_file)

