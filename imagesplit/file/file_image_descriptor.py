# coding=utf-8
"""
Generalised metadata from and imaging file

Author: Tom Doel
Copyright UCL 2017

"""


class FileImageDescriptor(object):
    """File metadata"""

    def __init__(self, file_format, dim_order, data_type, image_size, msb,
                 compression, voxel_size):
        self.compression = compression
        self.image_size = image_size
        self.file_format = file_format
        self.dim_order = dim_order
        self.data_type = data_type
        self.msb = msb
        self.voxel_size = voxel_size
