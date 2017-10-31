#!/usr/bin/env python
# coding=utf-8
"""
Utility for combining subimages into images

Author: Tom Doel
Copyright UCL 2017

"""

from __future__ import division, print_function

import argparse
import os
import sys

from file.file_factory import FileFactory
from file.file_wrapper import FileHandleFactory
from niftysplit.utils.file_descriptor import convert_to_descriptors
from niftysplit.utils.file_descriptor import generate_descriptor_from_header, \
    header_from_descriptor, generate_input_descriptors
from tools.write_files import write_files


def combine_file(input_file_base, descriptor_filename, filename_out_base,
                 start_index, output_type, file_handle_factory):
    """Combines several overlapping files into one output file"""

    if not filename_out_base:
        filename_out_base = os.path.splitext(filename_out_base)[0] + "_combined"

    if not descriptor_filename:
        [original_header, descriptors_in] = generate_input_descriptors(
            input_file_base, start_index)
    else:
        [original_header,
         descriptors_in] = header_from_descriptor(descriptor_filename)

    file_factory = FileFactory(file_handle_factory)

    descriptors_out = generate_descriptor_from_header(filename_out_base,
                                                      original_header,
                                                      output_type)

    desc_in = convert_to_descriptors(descriptors_in)
    desc_out = convert_to_descriptors(descriptors_out)

    write_files(desc_in, desc_out, file_factory)


def main(args):
    """file_combiner command-line utility"""
    parser = argparse.ArgumentParser(
        description='Combines multiple image parts into a single large MetaIO '
                    '(.mhd) file')

    parser.add_argument("-f", "--filename", required=True,
                        default="_no_filename_specified",
                        help="Base name of files to combine")
    parser.add_argument("-o", "--out", required=False, default="",
                        help="Filename of combined output file")
    parser.add_argument("-d", "--descriptor", required=False, default=None,
                        help="Name of descriptor file (.gift) which defines "
                             "the file splitting")
    parser.add_argument("-s", "--startindex", required=False, default="0",
                        type=int,
                        help="Start index for filename suffix when loading a "
                             "series of files")
    parser.add_argument("-t", "--type", required=False, default=None, type=str,
                        help="Output data type (default: same as input file "
                             "datatype)")

    args = parser.parse_args(args)

    assert sys.version_info >= (3, 0)

    if args.filename == '_no_filename_specified':
        raise ValueError('No filename was specified')
    else:
        combine_file(args.filename, args.descriptor, args.out, args.startindex,
                     args.type, FileHandleFactory())


if __name__ == '__main__':
    main(sys.argv[1:])
