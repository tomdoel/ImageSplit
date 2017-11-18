# coding=utf-8
"""
Read medical image header metadata

Author: Tom Doel
Copyright UCL 2017

"""
import os

from niftysplit.file.metaio_reader import load_mhd_header, get_dim_order


def parse_header(filename):
    """Read metadata from any suported header type"""

    header_base, extension = os.path.splitext(filename)

    if extension.lower() == ".mhd" or extension.lower() == ".mha":
        header = load_mhd_header(filename)
        return parse_mhd(header), header

    else:
        raise ValueError("Unknown image type: " + extension)


class FileImageDescriptor(object):
    """File metadata"""

    def __init__(self, file_format, dim_order, data_type, image_size):
        self.image_size = image_size
        self.file_format = file_format
        self.dim_order = dim_order
        self.data_type = data_type


def parse_mhd(header):
    """Read a metaheader and returns a FileImageDescriptor"""

    file_format = "mhd"
    dim_order = get_dim_order(header)
    data_type = header["ElementType"]
    image_size = header["DimSize"]
    return FileImageDescriptor(file_format=file_format,
                               dim_order=dim_order,
                               data_type=data_type,
                               image_size=image_size)
