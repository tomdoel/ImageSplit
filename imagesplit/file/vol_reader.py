# coding=utf-8
"""
Utility for reading and writing data to metaio (mhd/mha) files

Author: Tom Doel
Copyright UCL 2017

"""
import os
from six.moves import configparser

from imagesplit.file.data_type import DataType
from imagesplit.file.file_formats import FileFormats
from imagesplit.file.file_image_descriptor import FileImageDescriptor
from imagesplit.file.file_wrapper import FileWrapper, FileStreamer
from imagesplit.file.image_file_reader import LinearImageFileReader


class VolFile(LinearImageFileReader):
    """A class for reading or writing 3D imaging data to/from a MetaIO file
    pair (.mhd and .raw). """

    # pylint: disable=too-many-instance-attributes

    def __init__(self, local_image_size, header_filename,
                 file_handle_factory):
        super(VolFile, self).__init__(local_image_size)
        self._file_handle_factory = file_handle_factory
        self._header_filename = header_filename
        self._input_path = os.path.dirname(os.path.abspath(header_filename))
        self._file_wrapper = None
        self._file_streamer = None
        # File is for reading
        self._mode = 'rb'
        self._header = load_vge_header(header_filename)

        file_section = self._header["VolumeSection0\\_FileSection0"]
        self._bytes_per_voxel = compute_bytes_per_voxel(
            file_section["filedatatype"])
        self._numpy_format = get_numpy_datatype(
            file_section["filedatatype"],
            file_section["fileendian"])
        self._subimage_size = [int(s) for s in file_section["filesize"].split()]
        self._dimension_ordering = dim_order_from_header(
            self._header)

    @staticmethod
    def create_read_file(subimage_descriptor, file_handle_factory):
        """Create a MetaIoFile class for writing"""

        filename = subimage_descriptor.filename
        local_file_size = subimage_descriptor.ranges.image_size
        return VolFile(local_file_size, filename, file_handle_factory)

    def close_file(self):
        """Close file"""
        self.close()

    # pylint: disable=unused-argument
    def write_line(self, start_coords, image_line, rescale_limits):
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
        return compute_bytes_per_voxel(header["FileDataType"])

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
            file_section = header["VolumeSection0\\_FileSection0"]
            vol_name = file_section["filename"]
            # pylint: disable=unused-variable
            vol_path, vol_raw = os.path.split(vol_name)
            filename_raw = os.path.realpath(
                os.path.join(self._input_path, '..', vol_raw))
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

    @classmethod
    def load_and_parse_header(cls, filename):
        """Load vge header file and parse into FileImageDescriptor"""

        header = load_vge_header(filename)
        return parse_vge(header)


def load_vge_header(filename):
    """Load vge as an ini file"""

    header = configparser.ConfigParser()
    header.read(filename)

    # for section in header.sections():

    header_dict = {s: dict(header.items(s)) for s in header.sections()}

    return header_dict


def compute_bytes_per_voxel(file_data_type):
    """Returns number of bytes required to store one voxel for the given
    ElementType """

    switcher = {
        'VolumeDataType_Float': 4
    }
    return switcher.get(file_data_type, 2)


def get_numpy_datatype(element_type, endian):
    """Returns the numpy datatype corresponding to this ElementType"""

    endian_simplified = endian.strip().lower()
    byte_order_msb = endian_simplified and endian != "VolumeEndian_Little"
    if byte_order_msb:
        prefix = '>'
    else:
        prefix = '<'
    switcher = {
        'VolumeDataType_Float': 'f4',
    }
    return prefix + switcher.get(element_type, 2)


# pylint: disable=unused-argument
def dim_order_from_header(header):
    """
    Return the order in which dimensions are stored in the global system.
    The first element in the array contains the index of the global dimension
    which is represented by the first dimension in the file, and so on
    """
    return [1, 3, 2]  # ToDo: parse orientation from header


def parse_vge(header):
    """Parse vge header file"""

    file_section = header.get('VolumeSection0\\_FileSection0')
    image_size_string = file_section['filesize']
    image_size = [int(i) for i in image_size_string.split()]
    volume_section = header.get('VolumeSection0')
    voxel_size_string = volume_section['volumeresolution']
    voxel_size = [float(i) for i in voxel_size_string.split()]
    file_format = file_section['filefileformat']
    if file_format != "VolumeFileFormat_Raw":
        raise ValueError("Unknown file format " + file_format)
    msb = True  # True
    file_format = FileFormats.VOL_FORMAT
    dim_order = dim_order_from_header(header)
    data_type = DataType.name_from_vge(file_section['filedatatype'])
    compression = None

    header_dict = header

    return (FileImageDescriptor(file_format=file_format,
                                dim_order=dim_order,
                                data_type=data_type,
                                image_size=image_size,
                                msb=msb,
                                compression=compression,
                                voxel_size=voxel_size), header_dict)
