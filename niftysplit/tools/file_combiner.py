#!/usr/bin/env python

#
# Copyright UCL 2017
# Author: Tom Doel
#

from __future__ import division, print_function

import argparse
import os
import sys

import file_splitter
import file_wrapper
from file_wrapper import FileHandleFactory, write_files, generate_input_descriptors
from json_reader import read_json


def load_descriptor(descriptor_filename):
    data = read_json(descriptor_filename)
    if not data["appname"] == "GIFT-Surg split data":
        raise ValueError('Not a GIFT-Surg file')
    if not data["version"] == "1.0":
        raise ValueError('Cannot read this file version')
    return data


def combine_file(input_file_base, descriptor_filename, filename_out_base, start_index, output_type, file_factory):
    """Combines several overlapping files into one output file"""

    if not filename_out_base:
        filename_out_base = os.path.splitext(filename_out_base)[0] + "_combined"

    if not descriptor_filename:
        [original_header, descriptors_in] = generate_input_descriptors(input_file_base, start_index)
    else:
        [original_header, descriptors_in] = generate_header_from_descriptor_file(descriptor_filename)

    descriptors_out = generate_output_descriptor_from_header(filename_out_base, original_header)

    write_files(descriptors_in, descriptors_out, file_factory, original_header, output_type)


def generate_output_descriptor_from_header(filename_out_base, original_header):
    output_image_size = original_header["DimSize"]
    descriptors_out = []
    descriptor_out = {"index": 0, "suffix": "", "filename": filename_out_base + '.mhd',
                      "ranges": [[0, output_image_size[0] - 1, 0, 0],
                                 [0, output_image_size[1] - 1, 0, 0],
                                 [0, output_image_size[2] - 1, 0, 0]]}
    descriptors_out.append(descriptor_out)
    return descriptors_out


def generate_header_from_descriptor_file(descriptor_filename):
    descriptor = load_descriptor(descriptor_filename)
    original_file_list = descriptor["source_files"]
    if not len(original_file_list) == 1:
        raise ValueError('This function only supports data derived from a single file')
    original_file_descriptor = original_file_list[0]
    original_header = file_wrapper.load_mhd_header(original_file_descriptor["filename"])
    input_file_list = descriptor["split_files"]
    return original_header, input_file_list


def main(args):
    parser = argparse.ArgumentParser(description='Combines multiple image parts into a single large MetaIO (.mhd) file')

    parser.add_argument("-f", "--filename", required=True, default="_no_filename_specified",
                        help="Base name of files to combine")
    parser.add_argument("-o", "--out", required=False, default="", help="Filename of combined output file")
    parser.add_argument("-d", "--descriptor", required=False, default=None,
                        help="Name of descriptor file (.gift) which defines the file splitting")
    parser.add_argument("-s", "--startindex", required=False, default="0", type=int,
                        help="Start index for filename suffix when loading a series of files")
    parser.add_argument("-t", "--type", required=False, default=None, type=str,
                        help="Output data type (default: same as input file datatype)")

    args = parser.parse_args(args)

    assert sys.version_info >= (3, 0)

    if args.filename == '_no_filename_specified':
        raise ValueError('No filename was specified')
    else:
        combine_file(args.filename, args.descriptor, args.out, args.startindex, args.type, FileHandleFactory())


if __name__ == '__main__':
    main(sys.argv[1:])
