# coding=utf-8
"""
Utility files for splitting large images into subimages

Author: Tom Doel
Copyright UCL 2017

"""
from math import ceil


def get_linear_byte_offset(image_size, bytes_per_voxel, start_coords):
    """
    Return the byte offset corresponding to the given coordinates.

    Assumes you have a stream of bytes representing a multi-dimensional image,
    """

    offset = 0
    offset_multiple = bytes_per_voxel
    for coord, image_length in zip(start_coords, image_size):
        offset += coord * offset_multiple
        offset_multiple *= image_length
    return offset


def get_number_of_blocks(image_size, max_block_size):
    """Returns a list containing the number of blocks in each dimension
    required to split the image into blocks that are subject to a maximum
    size limit """

    return [int(ceil(float(image_size_element) /
                     float(max_block_size_element)))
            for image_size_element, max_block_size_element in
            zip(image_size, max_block_size)]


def get_block_coordinate_range(block_number, block_size, overlap_size,
                               image_size):
    """
    Returns the minimum and maximum coordinate values in one dimension for
    an image block, where the dimension length image_size is to be split into
    the number of blocks specified by block_size with an overlap of
    overlap_size voxels at each boundary, and the current block_number is
    specified. There is no overlap at the outer border of the image, and the
    length of the final block is reduced if necessary so there is no padding
    """

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

    return [int(ceil(float(image_size_element) /
                     float(number_of_blocks_element)))
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
                    [get_block_coordinate_range(index, block, overlap, size)
                     for index, block, overlap, size in
                     zip([i, j, k], suggested_block_size, overlap_size,
                         image_size)])

    return block_ranges


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
