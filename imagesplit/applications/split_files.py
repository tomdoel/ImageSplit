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

from imagesplit.file.file_factory import FileFactory
from imagesplit.file.file_wrapper import FileHandleFactory
from imagesplit.utils.file_descriptor import write_descriptor_file, \
    generate_output_descriptors, generate_input_descriptors, \
    header_from_descriptor
from imagesplit.applications.write_files import write_files

# pylint: disable=too-many-arguments
from imagesplit.utils.versioning import get_version_string


def split_file(input_file_base, filename_out_base, start_index, output_type,
               dim_order, file_handle_factory, output_format, slice_output,
               rescale, out_compression, max_block_size_voxels,
               overlap_size_voxels, descriptor_filename=None, test=False):
    """Saves the specified image file as a number of smaller files"""

    if not filename_out_base:
        input_file_base = os.path.splitext(input_file_base)[0]
        filename_out_base = input_file_base + "_split"

    if rescale and rescale != "limits" and len(rescale) != 2:
        raise ValueError('Rescale must have no arguments, or a min and max')

    descriptors_in, global_descriptor, header = specify_input_descriptors(
        descriptor_filename, input_file_base, start_index, input_file_base)

    descriptors_out = specify_output_descriptors(
        dim_order,
        filename_out_base,
        global_descriptor,
        header,
        max_block_size_voxels,
        out_compression,
        output_format,
        output_type,
        overlap_size_voxels,
        slice_output
    )

    file_factory = FileFactory(file_handle_factory)

    write_files(descriptors_in, descriptors_out, file_factory, rescale, test)

    # Write out descriptor if one does not already exist
    if not descriptor_filename:
        write_descriptor_file(descriptors_in, descriptors_out,
                              filename_out_base, test)


def specify_input_descriptors(descriptor_filename, input_file_base,
                              start_index, filename_override):
    """Compute input parameters based on input files and/or descriptor files"""
    if not descriptor_filename:
        # pylint: disable=unused-variable
        [header, descriptors_in, global_descriptor] = \
            generate_input_descriptors(input_file_base, start_index)
    else:
        [header, descriptors_in, global_descriptor] = \
            header_from_descriptor(descriptor_filename, filename_override)
    return descriptors_in, global_descriptor, header


def specify_output_descriptors(dim_order, filename_out_base, global_descriptor,
                               header, max_block_size_voxels, out_compression,
                               output_format, output_type, overlap_size_voxels,
                               slice_output):
    """Compute output parameters based on a set of parameters"""
    if output_format is None:
        output_format = global_descriptor.file_format
    if output_type is None:
        output_type = global_descriptor.data_type
    if out_compression is None:
        out_compression = None
    if dim_order is None:
        dim_order = global_descriptor.axis.to_condensed_format()
    dim_order, max_block_size_voxels, overlap_size_voxels = parse_slice_output(
        dim_order, max_block_size_voxels, overlap_size_voxels, slice_output)
    if max_block_size_voxels is None:
        max_block_size_voxels = -1
    if overlap_size_voxels is None:
        overlap_size_voxels = 0
    out_msb = global_descriptor.msb
    voxel_size = global_descriptor.voxel_size
    descriptors_out = generate_output_descriptors(
        filename_out_base=filename_out_base,
        max_block_size_voxels=max_block_size_voxels,
        overlap_size_voxels=overlap_size_voxels,
        dim_order=dim_order,
        header=header,
        output_type=output_type,
        output_file_format=output_format,
        num_dims=global_descriptor.num_dims,
        image_size=global_descriptor.size,
        msb=out_msb,
        compression=out_compression,
        voxel_size=voxel_size)
    return descriptors_out


def parse_slice_output(dim_order, max_block_size_voxels, overlap_size_voxels,
                       slice_output):
    """Get output parameters for splitting into slices along axis"""
    new_dim_order = dim_order
    if slice_output:
        slice_output = slice_output.lower()
        if slice_output[0] == "s":
            new_dim_order = [2, -3, 1]
            max_block_size_voxels = [1, -1, -1]
            overlap_size_voxels = [0, 0, 0]
        elif slice_output[0] == "c":
            new_dim_order = [1, -3, 2]
            max_block_size_voxels = [-1, 1, -1]
            overlap_size_voxels = [0, 0, 0]
        elif slice_output[0] == "a":
            new_dim_order = [1, 2, 3]
            max_block_size_voxels = [-1, -1, 1]
            overlap_size_voxels = [0, 0, 0]
        elif slice_output == "1":
            new_dim_order = [dim_order[1], -dim_order[2], dim_order[0]]
            max_block_size_voxels = [-1, -1, -1]
            max_block_size_voxels[abs(dim_order[0]) - 1] = 1
            overlap_size_voxels = [0, 0, 0]
        elif slice_output == "2":
            new_dim_order = [dim_order[0], -dim_order[2], dim_order[1]]
            max_block_size_voxels = [-1, -1, -1]
            max_block_size_voxels[abs(dim_order[1]) - 1] = 1
            overlap_size_voxels = [0, 0, 0]
        elif slice_output == "3":
            new_dim_order = [dim_order[0], dim_order[1], dim_order[2]]
            max_block_size_voxels = [-1, -1, -1]
            max_block_size_voxels[abs(dim_order[2]) - 1] = 1
            overlap_size_voxels = [0, 0, 0]
        else:
            raise ValueError("Unkown slice parameter " + slice_output)
    return new_dim_order, max_block_size_voxels, overlap_size_voxels


def main(args=None):
    """Utility for splitting images into subimages"""

    parser = argparse.ArgumentParser(
        description='Splits a large file into slices or blocks with overlap')

    parser.add_argument("-i", "--input", required=True,
                        default="_no_filename_specified",
                        help="Name of input file, or filename prefix for a "
                             "set of files")
    parser.add_argument("-o", "--out", required=False, default="",
                        help="Name of output file, or filename prefix if more "
                             "than one file is output")
    parser.add_argument("-l", "--overlap", required=False, default=None,
                        type=int,
                        help="Number of voxels to overlap between output "
                             "images. If not specified, output images will not "
                             "overlap")
    parser.add_argument("-m", "--max", nargs='+', required=False, default=None,
                        type=int,
                        help="Maximum number of voxels in each dimension in "
                             "each output file. Can be a scalar or vector "
                             "corresponding to each image dimension. The file "
                             "will be optimally split such that each file "
                             "output dimension is less than or equal to this "
                             "maximum.")
    parser.add_argument("-x", "--startindex", required=False, default=None,
                        type=int,
                        help="Start index for filename suffix when loading or "
                             "saving a sequence of files")
    parser.add_argument("-t", "--type", required=False, default=None, type=str,
                        help="Output data type (default: same as input file "
                             "datatype)")
    parser.add_argument("-f", "--format", required=False, default=None,
                        type=str,
                        help="Output file format such as mhd, tiff "
                             "(default: same as input file format)")

    parser.add_argument("-r", "--rescale", nargs='*', required=False,
                        default=None, type=float,
                        help="Rescale image between the specified min and max "
                             "values. If no values are specified, use the "
                             "volume limits.")

    parser.add_argument("-z", "--compress", nargs='?', required=False,
                        const='default', default=None, type=str,
                        help="Enables compression (default no compression). "
                             "Valid values depend on the output file format. "
                             "-z with no extra argument will choose a suitable "
                             "compression for this file format. "
                             "For TIFF files, the default is Adboe deflat and "
                             "other valid values are those supported by PIL.")

    parser.add_argument("-s", "--slice", required=False, default=None,
                        type=str,
                        help="Divide image into slices along the specified "
                             "axis. Choose 1, 2, 3 etc to select an axis "
                             "relative to the current image orientation, or "
                             "c, s, a to select an absolute orientation."
                             "This argument cannot be used with --axis, --max "
                             "or --overlap.")
    parser.add_argument("-a", "--axis", nargs='+', required=False,
                        default=None, type=int,
                        help="Axis ordering (default 1 2 3). Specifies the "
                             "global axis corresponding to each dimension "
                             "in the image file. The first value is the "
                             "global axis represented by the first dimension "
                             "in the file, and so on. One value for each "
                             "dimension, dimensions are numbered 1,2,3,"
                             "... and a negative value means that axis is "
                             "flipped. This cannot be used with --slice")
    parser.add_argument("-d", "--descriptor", required=False, default=None,
                        help="Name of descriptor file (.gift) which defines "
                             "the file splitting")

    parser.add_argument("--test", required=False,
                        action='store_true',
                        help="If set, No writing will be performed to the "
                             "output files")

    version_string = get_version_string()
    parser.add_argument(
        "-v", "--version",
        action='version',
        version=version_string)

    args = parser.parse_args(args)

    rescale = args.rescale

    # Code inspection suggests "if not rescale", but that is wrong.
    # We only set to "limits" if rescale is [], ie set without a range,
    # whereas if rescale is None (not set) we keep it as None
    #
    # noinspection PySimplifyBooleanCheck
    if rescale == []:  # rescale is set on command line but not given a range
        rescale = 'limits'

    if args.slice and (args.axis or args.max or args.overlap):
        raise ValueError('Cannot use --slice with --axis, --max or --overlap')

    if args.input == '_no_filename_specified':
        raise ValueError('No filename was specified')
    else:
        assert sys.version_info >= (2, 7)
        split_file(input_file_base=args.input,
                   filename_out_base=args.out,
                   start_index=args.startindex,
                   output_type=args.type,
                   dim_order=args.axis,
                   file_handle_factory=FileHandleFactory(),
                   output_format=args.format,
                   slice_output=args.slice,
                   rescale=rescale,
                   out_compression=args.compress,
                   max_block_size_voxels=args.max,
                   overlap_size_voxels=args.overlap,
                   descriptor_filename=args.descriptor,
                   test=args.test)


if __name__ == '__main__':
    main(sys.argv[1:])
