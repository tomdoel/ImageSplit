#!/usr/bin/env python
# coding=utf-8
"""
Utility for reading and writing data to metaio (mhd/mha) files

Author: Tom Doel
Copyright UCL 2017

"""
import copy
import os
from collections import OrderedDict

from niftysplit.utils.file_wrapper import FileWrapper, FileStreamer


class MetaIoFileFactory(object):
    """Factory for creating MetaIoFile classes"""

    def __init__(self, file_handle_factory, output_header, output_type):
        self._file_handle_factory = file_handle_factory
        self._output_header_template = copy.deepcopy(output_header)
        if output_type:
            self._output_header_template["ElementType"] = output_type

    def create_read_file(self, subimage_descriptor):
        """Create a MetaIoFile class for writing"""
        filename = subimage_descriptor.filename
        return MetaIoFile(filename, self._file_handle_factory, None)

    def create_write_file(self, subimage_descriptor):
        """Create a MetaIoFile class for this filename and template"""
        header_template = copy.deepcopy(self._output_header_template)
        header_template["DimSize"] = subimage_descriptor.image_size
        header_template["Origin"] = subimage_descriptor.origin_start
        filename = subimage_descriptor.filename
        return MetaIoFile(filename, self._file_handle_factory, header_template)


class MetaIoFile(object):
    """A class for reading or writing 3D imaging data to/from a MetaIO file
    pair (.mhd and .raw). """

    def __init__(self, header_filename, file_handle_factory, header_template):
        self._file_handle_factory = file_handle_factory
        self._header_filename = header_filename
        self._input_path = os.path.dirname(os.path.abspath(header_filename))
        self._file_wrapper = None
        self._file_streamer = None
        if header_template:
            # File is for writing
            self._mode = 'wb'
            # Force the raw filename to match the header filename
            base_filename = os.path.splitext(header_filename)[0]
            header = copy.deepcopy(header_template)
            header['ElementDataFile'] = base_filename + '.raw'

            save_mhd_header(header_filename, header)
            self._header = header

        else:
            # File is for reading
            self._mode = 'rb'
            self._header = None

    def write_image_stream(self, start_coords, image_line):
        """Write consecutive voxels to the raw binary file."""

        return self._get_file_streamer().write_image_stream(start_coords,
                                                            image_line)

    def read_image_stream(self, start_coords, num_voxels_to_read):
        """Read consecutive voxels of image data from the raw binary file
        starting at the specified coordinates. """

        return self._get_file_streamer().read_image_stream(start_coords,
                                                           num_voxels_to_read)

    def get_bytes_per_voxel(self):
        """Return the number of bytes used to represent a single voxel in
        this image. """

        header = self._get_header()
        return compute_bytes_per_voxel(header["ElementType"])

    def _get_header(self):
        """Return an OrderedDict containing the MetaIO metaheader metadata
        for this image. """

        if not self._header:
            self._header = load_mhd_header(self._header_filename)
        return self._header

    def _get_file_wrapper(self):
        """Return the HugeFileWrapper representing this image, creating it if
        it does not already exist. """

        if not self._file_wrapper:
            header = self._get_header()
            filename_raw = os.path.join(self._input_path,
                                        header["ElementDataFile"])
            self._file_wrapper = FileWrapper(filename_raw,
                                             self._file_handle_factory, self._mode)
        return self._file_wrapper

    def _get_file_streamer(self):
        """Return the HugeFileStreamer representing this image, creating it
        if it does not already exist. """

        if not self._file_streamer:
            header = self._get_header()
            bytes_per_voxel = compute_bytes_per_voxel(header["ElementType"])
            numpy_format = get_numpy_datatype(header["ElementType"],
                                              header["BinaryDataByteOrderMSB"])
            subimage_size = header["DimSize"]
            self._file_streamer = FileStreamer(self._get_file_wrapper(),
                                               subimage_size,
                                               bytes_per_voxel,
                                               numpy_format)
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


def load_mhd_header(filename):
    """Return an OrderedDict containing metadata loaded from an mhd file."""

    metadata = OrderedDict()

    with open(filename) as header_file:
        for line in header_file:
            (key, val) = [x.strip() for x in line.split("=")]
            if key in ['ElementSpacing', 'Offset', 'CenterOfRotation',
                       'TransformMatrix']:
                val = [float(s) for s in val.split()]
            elif key in ['NDims', 'ElementNumberOfChannels']:
                val = int(val)
            elif key in ['DimSize']:
                val = [int(s) for s in val.split()]
            elif key in ['BinaryData', 'BinaryDataByteOrderMSB',
                         'CompressedData']:
                # pylint: disable=simplifiable-if-statement
                # pylint: disable=redefined-variable-type
                if val.lower() == "true":
                    val = True
                else:
                    val = False

            metadata[key] = val

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


def save_mhd_header(filename, metadata):
    """Saves a mhd header file to disk using the given metadata"""

    # Add default metadata, replacing with custom specified values
    header = ''
    default_metadata = get_default_metadata()
    for key, val in default_metadata.items():
        if key in metadata.keys():
            value = metadata[key]
        else:
            value = val
        if value or value == 'False' or value == 0:
            value = str(value)
            value = value.replace("[", "").replace("]", "").replace(",", "")
            header += '%s = %s\n' % (key, value)

    # Add any custom metadata tags
    for key, val in metadata.items():
        if key not in default_metadata.keys():
            value = str(metadata[key])
            value = value.replace("[", "").replace("]", "").replace(",", "")
            header += '%s = %s\n' % (key, value)

    file_handle = open(filename, 'w')
    file_handle.write(header)
    file_handle.close()


def get_default_metadata():
    """Return an OrderedDict containing default mhd file metadata"""

    return OrderedDict(
        [('ObjectType', 'Image'), ('NDims', '3'), ('BinaryData', 'True'),
         ('BinaryDataByteOrderMSB', 'True'),
         ('CompressedData', []), ('CompressedDataSize', []),
         ('TransformMatrix', []), ('Offset', []),
         ('CenterOfRotation', []), ('AnatomicalOrientation', []),
         ('ElementSpacing', []), ('DimSize', []),
         ('ElementNumberOfChannels', []), ('ElementSize', []),
         ('ElementType', 'MET_FLOAT'), ('ElementDataFile', []),
         ('Comment', []), ('SeriesDescription', []), ('AcquisitionDate', []),
         ('AcquisitionTime', []),
         ('StudyDate', []), ('StudyTime', [])])


