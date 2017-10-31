# coding=utf-8
"""
Utility files for splitting large images into subimages

Author: Tom Doel
Copyright UCL 2017

"""

import numpy as np

from utils.file_descriptor import SubImageDescriptor


def get_linear_byte_offset(image_size, bytes_per_voxel, start_coords,
                           dimension_ordering):
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


class CoordinateTransformer(object):
    """Convert coordinates between orthogonal systems"""

    def __init__(self, origin, dim_ordering, dim_flip):
        """Create a transformer object for converting between systems

        :param origin: local coordinate origin in global coordinates
        :param dim_ordering: ordering of local dimensions
        :param dim_flip: whether local axes should be flipped
        """
        self._origin = origin
        self._dim_ordering = dim_ordering
        self._dim_flip = dim_flip

    def to_local(self, global_start, global_size):
        """Convert global coordinates to local coordinates"""

        # Translate coordinates to the local origin
        start = np.subtract(global_start, self._origin)

        # Permute dimensions of local coordinates
        start = np.transpose(start, self._dim_ordering)
        size = np.transpose(global_size, self._dim_ordering)

        # Flip dimensions where necessary
        for index, flip in enumerate(self._dim_flip):
            if flip:
                start = np.flip(start, index)
                size = np.flip(size, index)

        return start, size


def convert_to_descriptors(descriptors):
    descriptors_sorted = sorted(descriptors, key=lambda k: k['index'])
    desc = [SubImageDescriptor(d) for d in descriptors_sorted]
    return desc