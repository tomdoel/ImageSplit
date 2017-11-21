# coding=utf-8
"""Factory for creating file objects fod different file types"""
from niftysplit.file.header_reader import get_file_format
from niftysplit.file.metaio_reader import MetaIoFile
from niftysplit.file.tiff_file_reader import TiffFileReader
from niftysplit.file.vol_reader import VolFile


class FileFactory(object):
    """Create objects for handling file input and output"""

    def __init__(self, file_handle_factory):
        self._file_handle_factory = file_handle_factory
        self._metaio_factory = None

    def create_read_file(self, subimage_descriptor):
        """Create a class for reading"""

        file_format = get_file_format(subimage_descriptor.file_format)
        if file_format == "mhd":
            return MetaIoFile.create_read_file(subimage_descriptor,
                                               self._file_handle_factory)
        elif file_format == "vol":
                return VolFile.create_read_file(subimage_descriptor,
                                                self._file_handle_factory)
        else:
            raise ValueError("Format " + file_format + " not supported")

    def create_write_file(self, subimage_descriptor):
        """Create a class for writing"""

        file_format = get_file_format(subimage_descriptor.file_format)
        if file_format == "mhd":
            return MetaIoFile.create_write_file(subimage_descriptor,
                                                self._file_handle_factory)
        elif file_format == "tiff" or file_format == "tif":
            return TiffFileReader.create_write_file(subimage_descriptor,
                                                    self._file_handle_factory)
        else:
            raise ValueError("Format " + file_format + " not supported")

    @staticmethod
    def get_extension_for_format(file_format):
        """Returns the file extension for this file format"""

        file_format = get_file_format(file_format)
        if file_format == "mhd":
            return ".mhd"
        elif file_format == "tiff":
            return ".tiff"

        else:
            raise ValueError("Format " + file_format + " not supported")
