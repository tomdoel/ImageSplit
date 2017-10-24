#!/usr/bin/env python
# coding=utf-8
"""
Utility for reading and writing data to metaio (mhd/mha) files

Author: Tom Doel
Copyright UCL 2017

"""
from collections import OrderedDict


def load_mhd_header(filename):
    """Return an OrderedDict containing metadata loaded from an mhd file."""

    metadata = OrderedDict()

    with open(filename) as header_file:
        for line in header_file:
            (key, val) = [x.strip() for x in line.split("=")]
            if key in ['ElementSpacing', 'Offset', 'CenterOfRotation',
                       'TransformMatrix']:
                val = [float(s) for s in val.split()]
            elif key in ['NDims', 'ElementNumberOfChannels']:
                val = int(val)
            elif key in ['DimSize']:
                val = [int(s) for s in val.split()]
            elif key in ['BinaryData', 'BinaryDataByteOrderMSB',
                         'CompressedData']:
                # pylint: disable=simplifiable-if-statement
                # pylint: disable=redefined-variable-type
                if val.lower() == "true":
                    val = True
                else:
                    val = False

            metadata[key] = val

    return metadata