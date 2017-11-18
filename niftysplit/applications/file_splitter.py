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

from niftysplit.file.file_factory import FileFactory
from niftysplit.file.file_wrapper import FileHandleFactory
from niftysplit.utils.file_descriptor import write_descriptor_file, \
    generate_output_descriptors, generate_input_descriptors
from niftysplit.applications.write_files import write_files


def split_file(input_file, filename_out_base, max_block_size_voxels,
               overlap_size_voxels, start_index, output_type,
               dim_order, file_handle_factory, output_format):
    """Saves the specified image file as a number of smaller files"""

    [header, descriptors_in, global_descriptor] = \
        generate_input_descriptors(input_file, start_index)

    if not filename_out_base:
        input_file_base = os.path.splitext(input_file)[0]
        filename_out_base = input_file_base + "_split"

    if output_format is None:
        output_format = global_descriptor.file_format

    if dim_order is None:
        dim_order = global_descriptor.dim_order

    descriptors_out = generate_output_descriptors(
        filename_out_base=filename_out_base,
        max_block_size_voxels=max_block_size_voxels,
        overlap_size_voxels=overlap_size_voxels,
        dim_order=dim_order,
        header=header,
        output_type=output_type,
        output_file_format=output_format,
        num_dims=global_descriptor.num_dims,
        image_size=global_descriptor.size)

    file_factory = FileFactory(file_handle_factory)

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
    parser.add_argument("-r", "--format", required=False, default=None,
                        type=str,
                        help="Output file format such as mhd, tiff "
                             "(default: same as input file format)")

    parser.add_argument("-a", "--axis", nargs='+', required=False,
                        default=None, type=int,
                        help="Axis ordering (default 1 2 3). Specifies the "
                             "global axis corresponding to each dimension "
                             "in the imnage file. The first value is the "
                             "global axis represented by the first dimension "
                             "in the file, and so on. One value for each "
                             "dimension, dimensions are numbered 1,2,3,"
                             "... and a negative value means that axis is "
                             "flipped.")

    args = parser.parse_args(args)

    if args.filename == '_no_filename_specified':
        raise ValueError('No filename was specified')
    else:
        assert sys.version_info >= (2, 7)
        split_file(input_file=args.filename,
                   filename_out_base=args.out,
                   max_block_size_voxels=args.max,
                   overlap_size_voxels=args.overlap,
                   start_index=args.startindex,
                   output_type=args.type,
                   dim_order=args.axis,
                   file_handle_factory=FileHandleFactory(),
                   output_format=args.format)


if __name__ == '__main__':
    main(sys.argv[1:])
