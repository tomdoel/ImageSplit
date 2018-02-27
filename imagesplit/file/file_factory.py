# coding=utf-8
"""Factory for creating file objects fod different file types"""
from imagesplit.file.format_factory import FormatFactory


class FileFactory(object):
    """Create objects for handling file input and output"""

    def __init__(self, file_handle_factory):
        self._file_handle_factory = file_handle_factory

    def create_read_file(self, subimage_descriptor):
        """Create a class for reading"""

        return FormatFactory.get_factory(
            subimage_descriptor.file_format).create_read_file(
                subimage_descriptor, self._file_handle_factory)

    def create_write_file(self, subimage_descriptor):
        """Create a class for writing"""

        return FormatFactory.get_factory(
            subimage_descriptor.file_format).create_write_file(
                subimage_descriptor, self._file_handle_factory)
