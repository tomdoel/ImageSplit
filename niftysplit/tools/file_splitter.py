#!/usr/bin/env python
# coding=utf-8

"""
Utility for splitting large images into subimages

Author: Tom Doel
Copyright UCL 2017

"""

from __future__ import division, print_function

import argparse
import os
import sys

from niftysplit.utils.combined_file import write_files
from niftysplit.utils.file_descriptor import write_descriptor_file, \
    generate_output_descriptors, generate_input_descriptors
from niftysplit.utils.file_wrapper import FileHandleFactory
from niftysplit.utils.metaio_reader import MetaIoFileFactory


def split_file(input_file, filename_out_base, max_block_size_voxels,
               overlap_size_voxels, start_index, output_type,
               file_handle_factory):
    """Saves the specified image file as a number of smaller files"""

    input_file_base = os.path.splitext(input_file)[0]
    if not filename_out_base:
        filename_out_base = input_file_base + "_split"

    [header, descriptors_in] = generate_input_descriptors(input_file_base,
                                                          start_index)

    descriptors_out = generate_output_descriptors(filename_out_base,
                                                  max_block_size_voxels,
                                                  overlap_size_voxels, header)

    file_factory = MetaIoFileFactory(file_handle_factory, header, output_type)

    write_files(descriptors_in, descriptors_out, file_factory)
    write_descriptor_file(descriptors_in, descriptors_out, filename_out_base)


def main(args):
    """Utility for splitting images into subimages"""
    parser = argparse.ArgumentParser(
        description='Splits a large MetaIO (.mhd) file into multiple parts '
                    'with overlap')

    parser.add_argument("-f", "--filename", required=True,
                        default="_no_filename_specified",
                        help="Name of file to split, or filename prefix for a "
                             "series of files")
    parser.add_argument("-o", "--out", required=False, default="",
                        help="Prefix of output files")
    parser.add_argument("-l", "--overlap", required=False, default="50",
                        type=int,
                        help="Number of voxels to overlap between outputs")
    parser.add_argument("-m", "--max", required=False, default="500", type=int,
                        help="Maximum number of voxels in each dimension")
    parser.add_argument("-s", "--startindex", required=False, default=None,
                        type=int,
                        help="Start index for filename suffix when loading a "
                             "series of files")
    parser.add_argument("-t", "--type", required=False, default=None, type=str,
                        help="Output data type (default: same as input file "
                             "datatype)")

    args = parser.parse_args(args)

    if args.filename == '_no_filename_specified':
        raise ValueError('No filename was specified')
    else:
        assert sys.version_info >= (3, 0)
        split_file(args.filename, args.out, args.max, args.overlap,
                   args.startindex, args.type,
                   FileHandleFactory())


if __name__ == '__main__':
    main(sys.argv[1:])
