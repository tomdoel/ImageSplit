# coding=utf-8
"""Write multidimensional data line by line"""

from abc import ABCMeta, abstractmethod
import itertools
import numpy as np


class AbstractImageFile(object):
    """Base class for writing data from source to destination"""
    __metaclass__ = ABCMeta

    @abstractmethod
    def write_image(self, data_source):
        """Create and write out this file, using data from this image source"""
        pass


class AbstractLinearImageFile(AbstractImageFile):
    """Base class for writing data from source to destination line by line"""

    @abstractmethod
    def write_line(self, start, image_line):
        """Write the next line of bytes to the file"""

    @abstractmethod
    def read_line(self, start, num_voxels):
        """Reads a line of bytes from the file"""
        pass

    @abstractmethod
    def close_file(self):
        """Close the file"""
        pass

    def __init__(self, subimage_descriptor):
        self.subimage_descriptor = subimage_descriptor
        self.size = subimage_descriptor.image_size

    def read_image(self, start_local, size_local):
        """Read the specified part of the image"""

        # Initialise the output array
        image = np.zeros(shape=size_local)

        # Compute coordinate ranges
        ranges = [range(st, sz) for st, sz in zip(start_local, size_local)]

        # Exclude first coordinate and get others in reverse order
        ranges_to_iterate = ranges[:0:-1]

        # Iterate over each line (equivalent to multiple for loops)
        for main_dim_size in itertools.product(*ranges_to_iterate):
            start = [0] + list(reversed(main_dim_size))
            size = np.ones(shape=size_local.shape)
            size[0] = size_local[0]

            # Read one image line from the file
            image_line = self.read_line(start, size)

            # Replace image line
            start_in_image = np.subtract(start, start_local)
            line_coords = [Ellipsis] + start_in_image[1:]
            image[line_coords] = image_line

        return image

    def write_image(self, data_source):
        """Create and write out this file, using data from this image source"""

        # Compute coordinate ranges
        ranges = [range(0, sz) for sz in self.size]

        # Exclude first coordinate and get others in reverse order
        ranges_to_iterate = ranges[:0:-1]

        # Iterate over each line (equivalent to multiple for loops)
        for main_dim_size in itertools.product(*ranges_to_iterate):
            start = [0] + list(reversed(main_dim_size))
            size = np.ones(shape=self.size.shape)
            size[0] = self.size[0]

            # Read one image line from the transformed source
            image_line = data_source.read_image_local(start, size)

            # Write out the image data to the file
            self.write_line(start, image_line.image)

        self.close_file()
