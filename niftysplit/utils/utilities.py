# coding=utf-8
"""
Utility files for splitting large images into subimages

Author: Tom Doel
Copyright UCL 2017

"""


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
