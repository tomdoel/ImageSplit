# coding=utf-8
"""
Wraper for sub images that form part of a larger volume

Author: Tom Doel
Copyright UCL 2017

"""

import copy
import os
from math import ceil

from niftysplit.utils.json_reader import write_json, read_json
from niftysplit.utils.metaio_reader import load_mhd_header


class SubImageDescriptor(object):
    """Describes an image in relation to a larger image"""

    def __init__(self, descriptor_dict):
        self._descriptor = descriptor_dict
        self.filename = self._get_filename()
        self.image_size = self._get_image_size()
        self.dim_order_and_flip = self._get_dim_order()
        self.origin_start = self._get_origin_start()
        self.origin_end = self._get_origin_end()
        self.roi_start = self._get_roi_start()
        self.roi_end = self._get_roi_end()
        self.ranges = self._get_ranges()

        self.file_format = "mhd"
        self.data_type = self._get_data_type()
        self.template = self._get_template()

        self.dim_order = [abs(d) - 1 for d in self.dim_order_and_flip]
        self.dim_flip = [d < 0 for d in self.dim_order_and_flip]

    def _get_filename(self):
        return self._descriptor["filename"]

    def _get_ranges(self):
        return self._descriptor["ranges"]

    def _get_dim_order(self):
        return self._descriptor["dim_order"]

    def _get_roi_end(self):
        return [this_range[1] - this_range[3] for this_range in
                self._descriptor["ranges"]]

    def _get_roi_start(self):
        return [this_range[0] + this_range[2] for this_range in
                self._descriptor["ranges"]]

    def _get_origin_end(self):
        return [this_range[1] for this_range in
                self._descriptor["ranges"]]

    def _get_origin_start(self):
        return [this_range[0] for this_range in
                self._descriptor["ranges"]]

    def _get_image_size(self):
        """Return the size of this subvolume including overlap regions"""
        return [1 + this_range[1] - this_range[0] for this_range in
                self._descriptor["ranges"]]

    def _get_data_type(self):
        return self._descriptor["data_type"]

    def _get_template(self):
        return self._descriptor["template"]


def get_number_of_blocks(image_size, max_block_size):
    """Returns a list containing the number of blocks in each dimension
    required to split the image into blocks that are subject to a maximum
    size limit """

    return [int(ceil(float(image_size_element) / float(max_block_size_element)))
            for image_size_element, max_block_size_element in
            zip(image_size, max_block_size)]


def get_block_coordinate_range(block_number, block_size, overlap_size,
                               image_size):
    """Returns the minimum and maximum coordinate values in one dimension for
    an image block, where the dimension length image_size is to be split into
    the number of blocks specified by block_size with an overlap of
    overlap_size voxels at each boundary, and the current block_number is
    specified. There is no overlap at the outer border of the image, and the
    length of the final block is reduced if necessary so there is no padding """

    # Compute the minimum coordinate of the block
    if block_number == 0:
        min_coord = 0
        start_border = 0
    else:
        min_coord = block_number * block_size - overlap_size
        start_border = overlap_size

    # Compute the maximum coordinate of the block
    end_border = overlap_size
    max_coord = int((block_number + 1) * block_size - 1 + overlap_size)
    if max_coord >= image_size:
        max_coord = image_size - 1
        end_border = 0

    return min_coord, max_coord, start_border, end_border


def get_suggested_block_size(image_size, number_of_blocks):
    """Returns a recommended block size (a list of the number of blocks in
    each dimension) to allow the specified image_size to be split into the
    specified number of blocks in each dimension, with each block being
    roughly equal in size """

    return [ceil(float(image_size_element) / float(number_of_blocks_element))
            for image_size_element, number_of_blocks_element in
            zip(image_size, number_of_blocks)]


def get_image_block_ranges(image_size, max_block_size, overlap_size):
    """Returns a list of ranges, where each recommended block size (a list of
    the number of blocks in each dimension) to allow the specified image_size
    to be split into the specified number of blocks in each dimension,
    with each block being roughly equal in size """

    number_of_blocks = get_number_of_blocks(image_size, max_block_size)
    suggested_block_size = get_suggested_block_size(image_size,
                                                    number_of_blocks)
    block_ranges = []

    for i in range(number_of_blocks[0]):
        for j in range(number_of_blocks[1]):
            for k in range(number_of_blocks[2]):
                block_ranges.append(
                    [get_block_coordinate_range(index, block, overlap, size) for
                     index, block, overlap, size in
                     zip([i, j, k], suggested_block_size, overlap_size,
                         image_size)])

    return block_ranges


def write_descriptor_file(descriptors_in, descriptors_out, filename_out_base):
    """Saves descriptor files"""
    descriptor = {"appname": "GIFT-Surg split data", "version": "1.0",
                  "split_files": descriptors_out,
                  "source_files": descriptors_in}
    descriptor_output_filename = filename_out_base + "_info.gift"
    write_json(descriptor_output_filename, descriptor)


def generate_output_descriptors(filename_out_base, max_block_size_voxels,
                                overlap_size_voxels, dim_order, header,
                                output_type):
    """Creates descriptors represeting file output"""
    image_size = header["DimSize"]
    num_dims = header["NDims"]
    max_block_size_voxels_array = convert_to_array(max_block_size_voxels,
                                                   "block size", num_dims)
    overlap_voxels_size_array = convert_to_array(overlap_size_voxels,
                                                 "overlap size", num_dims)
    ranges = get_image_block_ranges(image_size, max_block_size_voxels_array,
                                    overlap_voxels_size_array)

    descriptors_out = []
    index = 0
    for subimage_range in ranges:
        suffix = "_" + str(index)
        output_filename_header = filename_out_base + suffix + ".mhd"
        file_descriptor_out = {"filename": output_filename_header,
                               "ranges": subimage_range, "suffix": suffix,
                               "index": index,
                               "dim_order": dim_order,
                               "data_type": output_type,
                               "header": copy.deepcopy(header)}
        descriptors_out.append(file_descriptor_out)
        index += 1
    return descriptors_out


def convert_to_array(scalar_or_list, parameter_name, num_dims):
    """Converts a list or scalar to an array"""
    if not isinstance(scalar_or_list, list):
        array = [scalar_or_list] * num_dims
    elif len(scalar_or_list) == num_dims:
        array = scalar_or_list
    else:
        raise ValueError(
            'The ' + parameter_name + 'parameter must be a scalar, or a list '
                                      'containing one entry for '
                                      'each image dimension')
    return array


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
    """Load a header and uses to define a file descriptor"""
    output_image_size = original_header["DimSize"]
    dim_order = [1, 2, 3]  # ToDo: get from header
    descriptors_out = []
    descriptor_out = {"index": 0,
                      "suffix": "",
                      "filename": filename_out_base + '.mhd',
                      "dim_order": dim_order,
                      "data_type": output_type,
                      "template": copy.deepcopy(original_header),
                      "ranges": [[0, output_image_size[0] - 1, 0, 0],
                                 [0, output_image_size[1] - 1, 0, 0],
                                 [0, output_image_size[2] - 1, 0, 0]]}
    descriptors_out.append(descriptor_out)
    return descriptors_out


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
    return original_header, input_file_list


def generate_input_descriptors(input_file_base, start_index):
    """Create descriptors for input files"""
    descriptors = []

    if start_index is None:
        # If no start index is specified, load a single header file
        header_filename = input_file_base + '.mhd'
        combined_header = load_mhd_header(header_filename)
        current_image_size = combined_header["DimSize"]
        current_ranges = [[0, current_image_size[0] - 1, 0, 0],
                          [0, current_image_size[1] - 1, 0, 0],
                          [0, current_image_size[2] - 1, 0, 0]]

        # Create a descriptor for this subimage
        descriptor = {"index": 0, "suffix": "", "filename": header_filename,
                      "ranges": current_ranges, "template": combined_header}
        descriptors.append(descriptor)
        return combined_header, descriptors

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
        while True:
            suffix = str(file_index)
            header_filename = input_file_base + suffix + '.mhd'
            if not os.path.isfile(header_filename):
                return combined_header, descriptors
            current_header = load_mhd_header(header_filename)
            current_image_size = current_header["DimSize"]
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
            descriptor = {"index": file_index, "suffix": suffix,
                          "filename": header_filename,
                          "ranges": ranges_to_write,
                          "template": combined_header}
            descriptors.append(descriptor)

            file_index += 1


def convert_to_descriptors(descriptors):
    """Convert descriptor dictionary to list of SubImageDescriptor objects"""
    descriptors_sorted = sorted(descriptors, key=lambda k: k['index'])
    desc = [SubImageDescriptor(d) for d in descriptors_sorted]
    return desc
