# coding=utf-8
"""
Utility for reading and writing data to metaio (mhd/mha) files

Author: Tom Doel
Copyright UCL 2017

"""
import copy
import os
from collections import OrderedDict
from six.moves import configparser

from niftysplit.file.file_wrapper import FileWrapper, FileStreamer
from niftysplit.file.image_file_reader import LinearImageFileReader


class VolFile(LinearImageFileReader):
    """A class for reading or writing 3D imaging data to/from a MetaIO file
    pair (.mhd and .raw). """

    # pylint: disable=too-many-instance-attributes

    def __init__(self, subimage_descriptor, header_filename,
                 file_handle_factory):
        super(VolFile, self).__init__(subimage_descriptor.ranges.image_size)
        self._file_handle_factory = file_handle_factory
        self._header_filename = header_filename
        self._input_path = os.path.dirname(os.path.abspath(header_filename))
        self._file_wrapper = None
        self._file_streamer = None
        # File is for reading
        self._mode = 'rb'
        # self._header = load_mhd_header(header_filename)

        # self._bytes_per_voxel = compute_bytes_per_voxel(
        #     self._header["ElementType"])
        # self._numpy_format = get_numpy_datatype(
        #     self._header["ElementType"],
        #     self._header["BinaryDataByteOrderMSB"])
        # self._subimage_size = self._header["DimSize"]
        self._dimension_ordering = get_dimension_ordering(self._header)

    @staticmethod
    def create_read_file(subimage_descriptor, file_handle_factory):
        """Create a MetaIoFile class for writing"""

        filename = subimage_descriptor.filename
        return VolFile(subimage_descriptor, filename, file_handle_factory)

    def close_file(self):
        """Close file"""
        self.close()

    def write_line(self, start_coords, image_line):
        """Write consecutive voxels to the raw binary file."""

        raise ValueError("Writing of vol files is not supported")

    def read_line(self, start_coords, num_voxels_to_read):
        """Read consecutive voxels of image data from the raw binary file
        starting at the specified coordinates. """

        return self._get_file_streamer().read_line(start_coords,
                                                   num_voxels_to_read)

    def get_bytes_per_voxel(self):
        """Return the number of bytes used to represent a single voxel in
        this image. """

        header = self._get_header()
        return compute_bytes_per_voxel(header["ElementType"])

    def get_dimension_ordering(self):
        """
        Return the preferred dimension ordering for writing data.

        Returns an array of 3 element, where each element represents a
        dimension in the global coordinate system numbered from 1 to 3 and
        is positive if data are to be written in ascending coordinates (in
        the global system) or negative if to be written in descending global
        coordinates along that dimension
        """

        return self._dimension_ordering

    def _get_header(self):
        """Return an OrderedDict containing the MetaIO metaheader metadata
        for this image. """

        if not self._header:
            self._header = load_vge_header(self._header_filename)
        return self._header

    def _get_file_wrapper(self):
        """Return the FileWrapper representing this image, creating it if
        it does not already exist. """

        if not self._file_wrapper:
            header = self._get_header()
            filename_raw = os.path.join(self._input_path,
                                        header["ElementDataFile"])
            self._file_wrapper = FileWrapper(filename_raw,
                                             self._file_handle_factory,
                                             self._mode)
        return self._file_wrapper

    def _get_file_streamer(self):
        """Return the FileStreamer representing this image, creating it
        if it does not already exist. """

        if not self._file_streamer:
            self._file_streamer = FileStreamer(self._get_file_wrapper(),
                                               self._subimage_size,
                                               self._bytes_per_voxel,
                                               self._numpy_format,
                                               self._dimension_ordering)
        return self._file_streamer

    def close(self):
        """Close the files associated with this image, if they are not
        already closed. """

        if self._file_streamer:
            self._file_streamer.close()
            self._file_streamer = None
        if self._file_wrapper:
            self._file_wrapper.close()
            self._file_wrapper = None


def load_vge_header(filename):
    """Load vge as an ini file"""

    header = configparser.ConfigParser()
    header.read(filename)

    # for section in header.sections():
        

    header_dict = {s: dict(header.items(s)) for s in header.sections()}

    return header_dict


def load_mhd_header(filename):
    """Return an OrderedDict containing metadata loaded from an mhd file."""

    metadata = OrderedDict()

    # with open(filename) as header_file:
    #     for line in header_file:
    #         (key, val) = [x.strip() for x in line.split("=")]
    #         if key in ['ElementSpacing', 'Offset', 'CenterOfRotation',
    #                    'TransformMatrix']:
    #             new_val = [float(s) for s in val.split()]
    #         elif key in ['NDims', 'ElementNumberOfChannels']:
    #             new_val = int(val)
    #         elif key in ['DimSize']:
    #             new_val = [int(s) for s in val.split()]
    #         elif key in ['BinaryData', 'BinaryDataByteOrderMSB',
    #                      'CompressedData']:
    #             # pylint: disable=simplifiable-if-statement
    #             if val.lower() == "true":
    #                 new_val = True
    #             else:
    #                 new_val = False
    #         else:
    #             new_val = val
    #
    #         metadata[key] = new_val

    return metadata


def compute_bytes_per_voxel(element_type):
    """Returns number of bytes required to store one voxel for the given
    metaIO ElementType """

    switcher = {
        'MET_CHAR': 1,
        'MET_UCHAR': 1,
        'MET_SHORT': 2,
        'MET_USHORT': 2,
        'MET_INT': 4,
        'MET_UINT': 4,
        'MET_LONG': 4,
        'MET_ULONG': 4,
        'MET_LONG_LONG': 8,
        'MET_ULONG_LONG': 8,
        'MET_FLOAT': 4,
        'MET_DOUBLE': 8,
    }
    return switcher.get(element_type, 2)


def get_numpy_datatype(element_type, byte_order_msb):
    """Returns the numpy datatype corresponding to this ElementType"""

    if byte_order_msb and (byte_order_msb or byte_order_msb == "True"):
        prefix = '>'
    else:
        prefix = '<'
    switcher = {
        'MET_CHAR': 'i1',
        'MET_UCHAR': 'u1',
        'MET_SHORT': 'i2',
        'MET_USHORT': 'u2',
        'MET_INT': 'i4',
        'MET_UINT': 'u4',
        'MET_LONG': 'i4',
        'MET_ULONG': 'u4',
        'MET_LONG_LONG': 'i8',
        'MET_ULONG_LONG': 'u8',
        'MET_FLOAT': 'f4',
        'MET_DOUBLE': 'f8',
    }
    return prefix + switcher.get(element_type, 2)


def get_dimension_ordering(header):
    """
    Return the order in which dimensions are stored in the global system.
    The first element in the array contains the index of the global dimension
    which is represented by the first dimension in the file, and so on
    """
    return [1, 2, 3]
