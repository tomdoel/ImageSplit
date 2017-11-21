# coding=utf-8
"""
Read medical image header metadata

Author: Tom Doel
Copyright UCL 2017

"""
import os

from niftysplit.file.metaio_reader import load_mhd_header, get_dim_order
from niftysplit.file.vol_reader import load_vge_header


def parse_header(filename):
    """Read metadata from any suported header type"""

    #pylint: disable=unused-variable
    header_base, extension = os.path.splitext(filename)

    if extension.lower() == ".mhd" or extension.lower() == ".mha":
        header = load_mhd_header(filename)
        return parse_mhd(header)

    if extension.lower() == ".vge":
        header = load_vge_header(filename)
        return parse_vge(header)

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
    return (FileImageDescriptor(file_format=file_format,
                               dim_order=dim_order,
                               data_type=data_type,
                               image_size=image_size), header)


def parse_vge(header):
    """Parse vge header file"""

    image_size_string = header.get('VolumeSection0\\_FileSection0', 'FileSize')
    image_size = [int(i) for i in image_size_string.split()]
    file_format = header.get('VolumeSection0\\_FileSection0', 'FileFileFormat')
    dim_order = [1, 2, 3]  # ToDo: parse orientation from header
    data_type = header.get('VolumeSection0\\_FileSection0', 'FileDataType')
    if data_type != "VolumeDataType_Float":
        raise ValueError("Unknown data type " + data_type)
    data_type = "MET_LONG"

    header_dict = {s: dict(header.items(s)) for s in header.sections()}

    return (FileImageDescriptor(file_format=file_format,
                                dim_order=dim_order,
                                data_type=data_type,
                                image_size=image_size), header_dict)


def get_file_format(format_string):
    """Return an overall file format for the given string"""

    f = format_string.lower()
    if f == "mhd" or format_string == "mha":
        return "mhd"
    elif f == "tif" or format_string == "tif":
        return "tiff"
    elif f == "volumefileformat_raw":
        return "vol"
