# coding=utf-8
"""Write multidimensional data line by line"""

import itertools
import numpy as np
from abc import ABCMeta, abstractmethod


class AbstractImageFile(object):
    """Base class for writing data from source to destination line by line"""
    __metaclass__ = ABCMeta

    @abstractmethod
    def write_file(self, data_source):
        """Create and write out this file, using data from this image source"""
        pass


class AbstractLinearImageFile(AbstractImageFile):
    """Base class for writing data from source to destination line by line"""

    @abstractmethod
    def write_line(self, start, image_line):
        """Write the next line of bytes to the file"""
        pass

    @abstractmethod
    def close_file(self):
        """Close the file"""
        pass

    def __init__(self, subimage_descriptor):
        self.subimage_descriptor = subimage_descriptor
        self.size = subimage_descriptor.image_size

    def write_file(self, data_source):
        """Create and write out this file, using data from this image source"""

        # Exclude first coordinate and get a range for the rest in reverse order
        size_excluding_first = self.size[:0:-1]
        size_ranges = [range(0, s) for s in size_excluding_first]

        # self.create_write_file()

        # Iterate over all ranges (equivalent to multiple for loops)
        for main_dim_size in itertools.product(*size_ranges):
            start = [0] + list(reversed(main_dim_size))
            size = np.ones(shape=self.size)
            size[0] = self.size[0]

            # Read one image line from the transformed source
            image_line = data_source.read_image_local(start, size)

            # Write out the image data to the file
            self.write_line(start, image_line.image)

        self.close_file()
