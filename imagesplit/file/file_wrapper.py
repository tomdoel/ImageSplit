# coding=utf-8

"""
Wrapping code for managing virtual images that may consist of multiple
subimages

Author: Tom Doel
Copyright UCL 2017

"""

import os

import numpy as np

from imagesplit.utils.utilities import file_linear_byte_offset, rescale_image


class FileStreamer(object):
    """Handle streaming of image data with arbitrarily large files"""

    def __init__(self, file_wrapper, image_size, bytes_per_voxel, numpy_format,
                 dimension_ordering):
        self._bytes_per_voxel = bytes_per_voxel
        self._image_size = image_size
        self._file_wrapper = file_wrapper
        self._numpy_format = numpy_format
        self._dimension_ordering = dimension_ordering

    def read_line(self, start_coords, num_voxels):
        """Read a line of image data from a binary file at the specified
        image location """

        offset = file_linear_byte_offset(self._image_size,
                                         self._bytes_per_voxel,
                                         start_coords)
        self._file_wrapper.get_handle().seek(offset)

        data_type = np.dtype(self._numpy_format)
        bytes_array = self._file_wrapper.get_handle().read(
            num_voxels * self._bytes_per_voxel)

        return np.frombuffer(bytes_array, dtype=data_type)

    def write_line(self, start_coords, image_line, rescale_limits):
        """Write a line of image data to a binary file at the specified image
        location """

        offset = file_linear_byte_offset(self._image_size,
                                         self._bytes_per_voxel,
                                         start_coords)
        self._file_wrapper.get_handle().seek(offset)

        data_type = np.dtype(self._numpy_format)

        if rescale_limits:
            image_line = rescale_image(data_type, image_line,
                                       rescale_limits)

        self._file_wrapper.get_handle().write(
            image_line.astype(data_type).tobytes())

    def close(self):
        """Close any files that have been opened."""
        self._file_wrapper.close()


class FileWrapper(object):
    """Read or write to arbitrarily large files."""

    def __init__(self, name, file_handle_factory, mode):
        self._file_handle_factory = file_handle_factory
        self._filename = name
        self._mode = mode
        self._file_handle = None

    def __del__(self):
        self.close()

    def __enter__(self):
        self.open()
        return self._file_handle

    def __exit__(self, exit_type, value, traceback):
        self.close()

    def get_handle(self):
        """Returns the file handle, opening if necessary"""
        if not self._file_handle:
            self.open()
        return self._file_handle

    def open(self):
        """Opens the file"""
        self._file_handle = self._file_handle_factory.create_file_handle(
            self._filename, self._mode)

    def close(self):
        """Close the file"""
        if self._file_handle and not self._file_handle.closed:
            self._file_handle.close()
            self._file_handle = None


class FileHandleFactory(object):
    """Creates file handles, allowing for abstraction to virtual files"""

    def __init__(self):
        pass

    @staticmethod
    def create_file_handle(filename, mode):
        """Create and open a real file with this path and file access mode"""
        folder = os.path.dirname(filename)
        if not os.path.exists(folder):
            os.makedirs(folder)
        return open(filename, mode)
