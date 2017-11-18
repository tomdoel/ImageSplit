# coding=utf-8
"""
Wraper for sub images that form part of a larger volume

Author: Tom Doel
Copyright UCL 2017

"""

import copy
import os

import numpy as np

from niftysplit.file.metaio_reader import get_dim_order
from niftysplit.file.file_factory import FileFactory
from niftysplit.file.metaio_reader import load_mhd_header
from niftysplit.image.combined_image import Axis
from niftysplit.utils.json_reader import write_json, read_json
from niftysplit.utils.utilities import get_image_block_ranges, convert_to_array


class SubImageRanges(object):
    """Convert range arrays to image parameters"""

    def __init__(self, ranges):
        self.ranges = ranges

        self.origin_start = [r[0] for r in self.ranges]
        self.origin_end = [r[1] for r in self.ranges]
        self.image_size = [1 + r[1] - r[0] for r in self.ranges]

        self.roi_start = [r[0] + r[2] for r in self.ranges]
        self.roi_end = [r[1] - r[3] for r in self.ranges]
        self.roi_size = [1 + (r[1] - r[3]) - (r[0] + r[2]) for r in self.ranges]


class GlobalImageDescriptor(object):
    """Describes a full combined image"""

    def __init__(self, size, file_format, dim_order):
        self.file_format = file_format
        self.size = size
        self.num_dims = len(size)
        self.dim_order = dim_order if dim_order \
            else np.arange(1, self.num_dims + 1)


class SubImageDescriptor(object):
    """Describes an image in relation to a larger image"""

    # pylint: disable=too-many-instance-attributes

    def __init__(self, filename, file_format, data_type,
                 template, ranges, dim_order_condensed, suffix, index):
        self.suffix = suffix
        self.index = index
        self.filename = filename
        self.file_format = file_format
        self.data_type = data_type
        self.template = template
        self.ranges = SubImageRanges(ranges)
        self.axis = Axis.from_condensed_format(dim_order_condensed)

    @staticmethod
    def from_dict(descriptor_dict):
        """Create SubImageDescriptor from dictionary entries"""
        return SubImageDescriptor(
            filename=descriptor_dict["filename"],
            file_format=descriptor_dict["file_format"],
            data_type=descriptor_dict["data_type"],
            template=descriptor_dict["template"],
            ranges=descriptor_dict["ranges"],
            dim_order_condensed=descriptor_dict["dim_order"],
            suffix=descriptor_dict["suffix"],
            index=descriptor_dict["index"]
        )

    def to_dict(self):
        """Get a dictionary for the metadata for this subimage"""

        return {"index": self.index, "suffix": self.suffix,
                "filename": self.filename, "data_type": self.data_type,
                "file_format": self.file_format, "template": self.template,
                "dim_order": self.axis.to_condensed_format(),
                "ranges": self.ranges.ranges}


def write_descriptor_file(descriptors_in, descriptors_out, filename_out_base):
    """Saves descriptor files"""
    dict_in = convert_to_dict(descriptors_in)
    dict_out = convert_to_dict(descriptors_out)
    descriptor = {"appname": "GIFT-Surg split data", "version": "1.0",
                  "split_files": dict_out,
                  "source_files": dict_in}
    descriptor_output_filename = filename_out_base + "_info.gift"
    write_json(descriptor_output_filename, descriptor)


def generate_output_descriptors(filename_out_base,
                                max_block_size_voxels,
                                overlap_size_voxels,
                                dim_order,
                                header,
                                output_type,
                                output_file_format,
                                num_dims,
                                image_size):
    """Creates descriptors representing file output"""
    max_block_size_voxels_array = convert_to_array(max_block_size_voxels,
                                                   "block size", num_dims)
    overlap_voxels_size_array = convert_to_array(overlap_size_voxels,
                                                 "overlap size", num_dims)
    ranges = get_image_block_ranges(image_size, max_block_size_voxels_array,
                                    overlap_voxels_size_array)

    extension = FileFactory.get_extension_for_format(output_file_format)
    descriptors_out = []
    index = 0
    for subimage_range in ranges:
        suffix = "_" + str(index)
        output_filename_header = filename_out_base + suffix + extension
        file_descriptor_out = SubImageDescriptor(
            filename=output_filename_header,
            file_format=output_file_format,
            ranges=subimage_range,
            suffix=suffix,
            index=index,
            dim_order_condensed=dim_order,
            data_type=output_type,
            template=copy.deepcopy(header)
        )
        descriptors_out.append(file_descriptor_out)
        index += 1
    return descriptors_out


def load_descriptor(descriptor_filename):
    """Loads and parses a file descriptor from disk"""
    data = read_json(descriptor_filename)
    if data["appname"] != "GIFT-Surg split data":
        raise ValueError('Not a GIFT-Surg file')
    if data["version"] != "1.0":
        raise ValueError('Cannot read this file version')
    return data


def generate_descriptor_from_header(filename_out_base, original_header,
                                    output_type):
    """Use a header to define a file descriptor"""
    output_image_size = original_header["DimSize"]
    dim_order = [1, 2, 3]  # ToDo: get from header
    file_format = "mhd"

    return [SubImageDescriptor(
        filename=filename_out_base + '.mhd',
        file_format=file_format,
        data_type=output_type,
        template=copy.deepcopy(original_header),
        dim_order_condensed=dim_order,
        suffix="",
        index=0,
        ranges=[[0, output_image_size[0] - 1, 0, 0],
                [0, output_image_size[1] - 1, 0, 0],
                [0, output_image_size[2] - 1, 0, 0]])]


def header_from_descriptor(descriptor_filename):
    """Create a file header based on descriptor information"""
    descriptor = load_descriptor(descriptor_filename)
    original_file_list = descriptor["source_files"]
    if len(original_file_list) != 1:
        raise ValueError(
            'This function only supports data derived from a single file')
    original_file_descriptor = original_file_list[0]
    original_header = load_mhd_header(
        original_file_descriptor["filename"])
    input_file_list = descriptor["split_files"]
    descriptors = convert_to_descriptors(input_file_list)
    return original_header, descriptors


def generate_input_descriptors(input_file_base, start_index):
    """Create descriptors for input files"""
    descriptors = []

    if start_index is None:
        suffix = ""
        # If no start index is specified, load a single header file
        header_filename = input_file_base + suffix + '.mhd'
        combined_header = load_mhd_header(header_filename)
        file_descriptor = parse_header(combined_header)
        current_image_size = file_descriptor.image_size
        data_type = file_descriptor.data_type
        dim_order = file_descriptor.dim_order
        file_format = file_descriptor.file_format
        current_ranges = [[0, current_image_size[0] - 1, 0, 0],
                          [0, current_image_size[1] - 1, 0, 0],
                          [0, current_image_size[2] - 1, 0, 0]]

        # Create a descriptor for this subimage
        descriptors.append(SubImageDescriptor(
            index=0,
            suffix=suffix,
            filename=header_filename,
            ranges=current_ranges,
            template=combined_header,
            data_type=data_type,
            dim_order_condensed=dim_order,
            file_format=file_format
        ))

        global_descriptor = GlobalImageDescriptor(
            size=current_image_size,
            file_format=file_format,
            dim_order=dim_order)

        return combined_header, descriptors, global_descriptor

    else:
        # Load a series of files starting with the specified prefix
        file_index = start_index
        suffix = str(file_index)
        header_filename = input_file_base + suffix + '.mhd'

        if not os.path.isfile(header_filename):
            raise ValueError(
                'No file series found starting with ' + header_filename)

        current_ranges = None

        combined_header = None
        full_image_size = None
        file_format = None
        while True:
            suffix = str(file_index)
            header_filename = input_file_base + suffix + '.mhd'
            if not os.path.isfile(header_filename):
                global_descriptor = GlobalImageDescriptor(
                    size=full_image_size,
                    file_format=file_format,
                    dim_order=dim_order)

                return combined_header, descriptors, global_descriptor
            current_header = load_mhd_header(header_filename)

            file_descriptor = parse_header(current_header)
            current_image_size = file_descriptor.image_size
            data_type = file_descriptor.data_type
            dim_order = file_descriptor.dim_order
            file_format = file_descriptor.file_format

            if not current_ranges:
                full_image_size = copy.deepcopy(current_image_size)
                combined_header = copy.deepcopy(current_header)
                current_ranges = [[0, current_image_size[0] - 1, 0, 0],
                                  [0, current_image_size[1] - 1, 0, 0],
                                  [0, current_image_size[2] - 1, 0, 0]]
            else:
                if current_image_size[0] != full_image_size[0]:
                    raise ValueError(
                        'When loading without a descriptor file, the first '
                        'dimension of each file must '
                        'match')
                if current_image_size[1] != full_image_size[1]:
                    raise ValueError(
                        'When loading without a descriptor file, the second '
                        'dimension of each file must '
                        'match')
                full_image_size[2] = full_image_size[2] + current_image_size[2]
                current_ranges[2][0] = current_ranges[2][1] + 1
                current_ranges[2][1] = current_ranges[2][1] + \
                    current_image_size[2]

            # Update the combined image size
            combined_header["DimSize"] = full_image_size

            # Create a descriptor for this subimage
            ranges_to_write = copy.deepcopy(current_ranges)
            descriptors.append(SubImageDescriptor(
                index=file_index,
                suffix=suffix,
                filename=header_filename,
                ranges=ranges_to_write,
                template=combined_header,
                data_type=data_type,
                dim_order_condensed=dim_order,
                file_format = file_format,
            ))

            file_index += 1


class FileImageDescriptor(object):
    """File metadata"""
    def __init__(self, file_format, dim_order, data_type, image_size):
        self.image_size = image_size
        self.file_format = file_format
        self.dim_order = dim_order
        self.data_type = data_type


def parse_header(header):
    """Reads a metaheader and returns a FileImageDescriptor"""
    file_format = "mhd"
    dim_order = get_dim_order(header)
    data_type = header["ElementType"]
    image_size = header["DimSize"]
    return FileImageDescriptor(file_format=file_format,
                               dim_order=dim_order,
                               data_type=data_type,
                               image_size=image_size)


def convert_to_descriptors(descriptors_dict):
    """Convert descriptor dictionary to list of SubImageDescriptor objects"""
    descriptors_sorted = sorted(descriptors_dict, key=lambda k: k['index'])
    desc = [SubImageDescriptor.from_dict(d) for d in descriptors_sorted]
    return desc


def convert_to_dict(descriptors):
    """Convert SubImageDescriptor objects to descriptor dictionary"""

    return [d.to_dict() for d in descriptors]
