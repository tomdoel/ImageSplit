# coding=utf-8
"""
Wrapper for sub images that form part of a larger volume

Author: Tom Doel
Copyright UCL 2017

"""

import copy
import os

import numpy as np

from imagesplit.file.format_factory import FormatFactory
from imagesplit.file.metaio_reader import load_mhd_header
from imagesplit.image.combined_image import Axis
from imagesplit.utils.json_reader import write_json, read_json
from imagesplit.utils.utilities import ranges_for_max_block_size, \
    convert_to_array


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

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        return False

    def __ne__(self, other):
        return not self.__eq__(other)


class GlobalImageDescriptor(object):
    """Describes a full combined image"""

    def __init__(self, size, file_format, dim_order_condensed, data_type, msb,
                 voxel_size):
        self.data_type = data_type
        self.file_format = file_format
        self.size = size
        self.num_dims = len(size)
        self.msb = msb
        dim_order = dim_order_condensed if dim_order_condensed \
            else np.arange(1, self.num_dims + 1).tolist()
        self.axis = Axis.from_condensed_format(dim_order)
        self.voxel_size = voxel_size

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        return False

    def __ne__(self, other):
        return not self.__eq__(other)


class SubImageDescriptor(object):
    """Describes an image in relation to a larger image"""

    # pylint: disable=too-many-instance-attributes
    # pylint: disable=too-many-arguments

    def __init__(self, filename, file_format, data_type,
                 template, ranges, dim_order_condensed, suffix, index, msb,
                 compression, voxel_size):
        self.suffix = suffix
        self.index = index
        self.filename = filename
        self.file_format = file_format
        self.data_type = data_type
        self.template = template
        self.ranges = SubImageRanges(ranges)
        self.axis = Axis.from_condensed_format(dim_order_condensed)
        self.msb = msb
        self.compression = compression
        self.voxel_size = voxel_size

    def get_local_size(self):
        """Transpose the subimage size to the local coordinate system"""
        return np.take(self.ranges.image_size, self.axis.dim_order).tolist()

    def get_local_origin(self):
        """Transpose the subimage origin to the local coordinate system"""
        return np.take(self.ranges.origin_start, self.axis.dim_order).tolist()

    def get_local_voxel_size(self):
        """Transpose the subimage origin to the local coordinate system"""
        return np.take(self.voxel_size, self.axis.dim_order).tolist()

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
            index=descriptor_dict["index"],
            msb=descriptor_dict["msb"],
            compression=descriptor_dict["compression"],
            voxel_size=descriptor_dict["voxel_size"],
        )

    def to_dict(self):
        """Get a dictionary for the metadata for this subimage"""

        return {"index": self.index,
                "suffix": self.suffix,
                "filename": self.filename,
                "data_type": self.data_type,
                "file_format": self.file_format,
                "template": self.template,
                "dim_order": self.axis.to_condensed_format(),
                "compression": self.compression,
                "msb": self.msb,
                "voxel_size": self.voxel_size,
                "ranges": self.ranges.ranges}

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        return False

    def __ne__(self, other):
        return not self.__eq__(other)


def write_descriptor_file(descriptors_in, descriptors_out, filename_out_base,
                          test=False):
    """Saves descriptor files"""
    dict_in = convert_to_dict(descriptors_in)
    dict_out = convert_to_dict(descriptors_out)
    descriptor = {"appname": "ImageSplit data", "version": "1.0",
                  "split_files": dict_out,
                  "source_files": dict_in}
    descriptor_output_filename = filename_out_base + "_info.imagesplit"
    if not test:
        write_json(descriptor_output_filename, descriptor)


# pylint: disable=too-many-arguments
def generate_output_descriptors(filename_out_base,
                                max_block_size_voxels,
                                overlap_size_voxels,
                                dim_order,
                                header,
                                output_type,
                                num_dims,
                                output_file_format,
                                image_size,
                                msb,
                                compression,
                                voxel_size):
    """Creates descriptors representing file output"""
    max_block_size_voxels_array = convert_to_array(max_block_size_voxels,
                                                   "block size", num_dims)
    overlap_voxels_size_array = convert_to_array(overlap_size_voxels,
                                                 "overlap size", num_dims)
    ranges = ranges_for_max_block_size(image_size, max_block_size_voxels_array,
                                       overlap_voxels_size_array)

    extension = FormatFactory.get_extension_for_format(output_file_format)
    descriptors_out = []
    index = 0
    for subimage_range in ranges:
        suffix = "" if len(ranges) <= 1 else \
            "_" + '{0:04d}'.format(index)
        output_filename_header = filename_out_base + suffix + extension
        file_descriptor_out = SubImageDescriptor(
            filename=output_filename_header,
            file_format=output_file_format,
            ranges=subimage_range,
            suffix=suffix,
            index=index,
            dim_order_condensed=dim_order,
            data_type=output_type,
            template=copy.deepcopy(header),
            msb=msb,
            compression=compression,
            voxel_size=voxel_size
        )
        descriptors_out.append(file_descriptor_out)
        index += 1
    return descriptors_out


def load_descriptor(descriptor_filename):
    """Loads and parses a file descriptor from disk"""
    data = read_json(descriptor_filename)
    if data["appname"] != "ImageSplit data":
        raise ValueError('Not an ImageSplit file')
    if data["version"] != "1.0":
        raise ValueError('Cannot read this file version')
    return data


def header_from_descriptor(descriptor_filename, filename_override):
    """Create a file header based on descriptor information"""
    descriptor = load_descriptor(descriptor_filename)
    original_file_list = descriptor["source_files"]
    if len(original_file_list) != 1:
        raise ValueError(
            'This function only supports data derived from a single file')
    original_file_descriptor = original_file_list[0]
    file_format = FormatFactory.simplify_format(
        original_file_descriptor["file_format"])
    if file_format == "mhd":
        original_header = load_mhd_header(original_file_descriptor["filename"])
    else:
        original_header = None  # ToDo
    input_file_list = descriptor["split_files"]

    if filename_override:
        input_file_base, extension = os.path.splitext(filename_override)
        print("*" + input_file_base)
        print("*" + extension)
        for input_file in input_file_list:
            # old_filename = input_file["filename"]
            filename = input_file_base + input_file["suffix"] + extension
            input_file["filename"] = filename

    descriptors = convert_to_descriptors(input_file_list)

    global_descriptor = _aggregate_global_descriptor(descriptors)

    return original_header, descriptors, global_descriptor


def generate_input_descriptors(input_file, start_index):
    """Create descriptors for one or more input files that do not have a
    descriptor file"""

    format_factory = FormatFactory()
    input_file_base, extension = os.path.splitext(input_file)
    descriptors = []
    current_ranges = None
    combined_header = None
    full_image_size = None

    if start_index is None:
        # If no start index is specified, load a single header file
        file_index = 0
        format_str = ""
    else:
        # Load a series of files starting with the specified prefix
        file_index = start_index
        format_str = _get_format_string(extension, input_file_base, start_index)

    suffix = format_str.format(start_index)
    header_filename = input_file_base + suffix + extension

    if not os.path.isfile(header_filename):
        raise ValueError(
            'No file series found starting with ' + header_filename)

    # Loop through all the input files
    while True:
        file_descriptor, current_header = parse_header(header_filename,
                                                       format_factory)
        data_type = file_descriptor.data_type
        dim_order = file_descriptor.dim_order
        file_format = file_descriptor.file_format
        current_image_size = file_descriptor.image_size
        voxel_size = file_descriptor.voxel_size
        msb = file_descriptor.msb
        compression = file_descriptor.compression

        # Reorder image size and voxel size dimensions
        axis = Axis.from_condensed_format(dim_order)
        current_image_size = \
            np.take(current_image_size, axis.reverse_dim_order).tolist()
        voxel_size = np.take(voxel_size, axis.reverse_dim_order).tolist()

        if not current_ranges:
            full_image_size = copy.deepcopy(current_image_size)
            combined_header = copy.deepcopy(current_header)
            current_ranges = [[0, current_image_size[0] - 1, 0, 0],
                              [0, current_image_size[1] - 1, 0, 0],
                              [0, current_image_size[2] - 1, 0, 0]]
        else:
            # For multiple input files, concatenate volumes
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
            file_format=file_format,
            msb=msb,
            compression=compression,
            voxel_size=voxel_size
        ))

        if start_index is None:
            # Single file already loaded, so terminate the while True loop
            break
        else:
            # Search for next file, and if not found terminate the loop
            file_index += 1
            suffix = format_str.format(file_index)
            header_filename = input_file_base + suffix + extension
            if not os.path.isfile(header_filename):
                break

    full_image_size = np.array(full_image_size).tolist()

    global_descriptor = _aggregate_global_descriptor(descriptors)

    # Update the combined image size
    combined_header["DimSize"] = full_image_size

    # Update voxel size
    combined_header["ElementSize"] = voxel_size

    return combined_header, descriptors, global_descriptor


def _aggregate_global_descriptor(descriptors):
    global_ranges = None
    combined_dim_order = None
    combined_file_format = None
    data_type = None
    msb = None
    voxel_size = None

    for descriptor in descriptors:
        current_ranges = descriptor.ranges.ranges
        if not global_ranges:
            global_ranges = copy.deepcopy(current_ranges)
        else:
            global_ranges[0][0] = min(global_ranges[0][0], current_ranges[0][0])
            global_ranges[0][1] = max(global_ranges[0][1], current_ranges[0][1])
            global_ranges[1][0] = min(global_ranges[1][0], current_ranges[1][0])
            global_ranges[1][1] = max(global_ranges[1][1], current_ranges[1][1])
            global_ranges[2][0] = min(global_ranges[2][0], current_ranges[2][0])
            global_ranges[2][1] = max(global_ranges[2][1], current_ranges[2][1])

        if not combined_file_format:
            combined_file_format = descriptor.file_format
        if not combined_dim_order:
            combined_dim_order = descriptor.axis.to_condensed_format()
        if not data_type:
            data_type = descriptor.data_type
        if not msb:
            msb = descriptor.msb
        if not voxel_size:
            voxel_size = copy.deepcopy(descriptor.voxel_size)

    full_image_size = [global_ranges[0][1] - global_ranges[0][0] + 1,
                       global_ranges[1][1] - global_ranges[1][0] + 1,
                       global_ranges[2][1] - global_ranges[2][0] + 1]
    full_image_size = np.array(full_image_size).tolist()

    global_descriptor = GlobalImageDescriptor(
        size=full_image_size,
        file_format=combined_file_format,
        dim_order_condensed=combined_dim_order,
        data_type=data_type,
        msb=msb,
        voxel_size=voxel_size)

    return global_descriptor


def convert_to_descriptors(descriptors_dict):
    """Convert descriptor dictionary to list of SubImageDescriptor objects"""
    descriptors_sorted = sorted(descriptors_dict, key=lambda k: k['index'])
    desc = [SubImageDescriptor.from_dict(d) for d in descriptors_sorted]
    return desc


def convert_to_dict(descriptors):
    """Convert SubImageDescriptor objects to descriptor dictionary"""

    return [d.to_dict() for d in descriptors]


def parse_header(filename, factory):
    """Read metadata from any suported header type"""

    # pylint: disable=unused-variable
    header_base, extension = os.path.splitext(filename)

    format_string = factory.extension_to_format(extension)
    return factory.get_factory(format_string).load_and_parse_header(filename)


def _get_format_string(extension, input_file_base, start_index):
    for num_zeros in range(10, -1, -1):
        format_str = '{0:0' + str(num_zeros) + 'd}'
        suffix_test = format_str.format(start_index)
        header_filename = input_file_base + suffix_test + extension
        if os.path.isfile(header_filename):
            break
    return format_str
