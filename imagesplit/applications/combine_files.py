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

from imagesplit.file.file_factory import FileFactory
from imagesplit.file.file_wrapper import FileHandleFactory
from imagesplit.utils.file_descriptor import descriptor_from_mhd_header, \
    header_from_descriptor, generate_input_descriptors
from imagesplit.applications.write_files import write_files


def combine_file(input_file_base, descriptor_filename, filename_out_base,
                 start_index, output_type, file_handle_factory, rescale):
    """Combines several overlapping files into one output file"""

    if not filename_out_base:
        filename_out_base = os.path.splitext(input_file_base)[0] + "_combined"

    if not descriptor_filename:
        # pylint: disable=unused-variable
        [original_header, descriptors_in, global_descriptor] = \
            generate_input_descriptors(input_file_base, start_index)
    else:
        [original_header,
         descriptors_in] = header_from_descriptor(descriptor_filename)

    file_factory = FileFactory(file_handle_factory)

    descriptors_out = descriptor_from_mhd_header(filename_out_base,
                                                 original_header,
                                                 output_type)

    write_files(descriptors_in, descriptors_out, file_factory, rescale)


def main(args):
    """file_combiner command-line utility"""
    parser = argparse.ArgumentParser(
        description='Combines multiple image parts into a single large MetaIO '
                    '(.mhd) file')

    parser.add_argument("-i", "--input", required=True,
                        default="_no_filename_specified",
                        help="Base name of files to combine")
    parser.add_argument("-o", "--out", required=False, default="",
                        help="Filename of combined output file")
    parser.add_argument("-d", "--descriptor", required=False, default=None,
                        help="Name of descriptor file (.gift) which defines "
                             "the file splitting")
    parser.add_argument("-x", "--startindex", required=False, default="0",
                        type=int,
                        help="Start index for filename suffix when loading a "
                             "series of files")
    parser.add_argument("-t", "--type", required=False, default=None, type=str,
                        help="Output data type (default: same as input file "
                             "datatype)")

    parser.add_argument("-r", "--rescale", required=False, default=None,
                        type=str,
                        help="If true, rescale image to the full range of the "
                             "data type")
    args = parser.parse_args(args)

    assert sys.version_info >= (2, 7)

    if args.filename == '_no_filename_specified':
        raise ValueError('No filename was specified')
    else:
        combine_file(args.filename, args.descriptor, args.out, args.startindex,
                     args.type, FileHandleFactory(), args.rescale)


if __name__ == '__main__':
    main(sys.argv[1:])
