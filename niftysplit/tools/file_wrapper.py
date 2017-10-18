#!/usr/bin/env python

#
# Copyright UCL 2017
# Author: Tom Doel
#
import copy
import os
from collections import OrderedDict

import numpy as np


def write_files(descriptors_in, descriptors_out, file_factory, original_header, output_type):
    input_combined = CombinedFileReader(descriptors_in, file_factory)
    output_combined = CombinedFileWriter(descriptors_out, file_factory, original_header, output_type)
    output_combined.write_image_file(input_combined)

    input_combined.close()
    output_combined.close()


class CombinedFileWriter:
    def __init__(self, descriptors, file_factory, header_template, element_type):
        """A kind of virtual file for writing where the data are distributed across multiple real files."""

        if element_type:
            header_template = copy.deepcopy(header_template)
            header_template["ElementType"] = element_type
        descriptors_sorted = sorted(descriptors, key=lambda k: k['index'])
        self._subimages = []
        self._cached_last_subimage = None
        self._bytes_per_voxel = compute_bytes_per_voxel(header_template["ElementType"])
        self._numpy_format = get_numpy_datatype(header_template["ElementType"],
                                                header_template["BinaryDataByteOrderMSB"])
        for descriptor in descriptors_sorted:
            self._subimages.append(SubImage(descriptor, file_factory, header_template))

    def write_image_file(self, input_combined):
        for next_image in self._subimages:
            output_ranges = next_image.get_ranges()
            i_range_global = output_ranges[0]
            j_range_global = output_ranges[1]
            k_range_global = output_ranges[2]
            num_voxels_to_read_per_line = i_range_global[1] + 1 - i_range_global[0]

            for k_global in range(k_range_global[0], 1 + k_range_global[1]):
                for j_global in range(j_range_global[0], 1 + j_range_global[1]):
                    start_coords_global = [i_range_global[0], j_global, k_global]
                    image_line = input_combined.read_image_stream(start_coords_global, num_voxels_to_read_per_line)
                    next_image.write_image_stream(start_coords_global, image_line)

    def close(self):
        for subimage in self._subimages:
            subimage.close()


class CombinedFileReader:
    """A kind of virtual file for reading where the data are distributed across multiple real files."""

    def __init__(self, descriptors, file_factory):
        descriptors_sorted = sorted(descriptors, key=lambda k: k['index'])
        self._subimages = []
        self._cached_last_subimage = None
        for descriptor in descriptors_sorted:
            self._subimages.append(SubImage(descriptor, file_factory, None))

    def read_image_stream(self, start_coords_global, num_voxels_to_read):
        byte_stream = None
        current_i_start = start_coords_global[0]
        while num_voxels_to_read > 0:
            current_start_coords = [current_i_start, start_coords_global[1], start_coords_global[2]]
            next_image = self._find_subimage(current_start_coords, True)
            next_byte_stream = next_image.read_image_stream(current_start_coords, num_voxels_to_read)
            if byte_stream is not None:
                byte_stream = np.concatenate((byte_stream, next_byte_stream))
            else:
                byte_stream = next_byte_stream
            num_voxels_read = round(len(next_byte_stream))
            num_voxels_to_read -= num_voxels_read
            current_i_start += num_voxels_read
        return byte_stream

    def close(self):
        for subimage in self._subimages:
            subimage.close()

    def _find_subimage(self, start_coords_global, must_be_in_roi):

        # For efficiency, first check the last subimage before going through the whole list
        if self._cached_last_subimage \
                and self._cached_last_subimage.contains_voxel(start_coords_global, must_be_in_roi):
            return self._cached_last_subimage

        # Iterate through the list of subimages to find the one containing these start coordinates
        for next_subimage in self._subimages:
            if next_subimage.contains_voxel(start_coords_global, must_be_in_roi):
                self._cached_last_subimage = next_subimage
                return next_subimage

        raise ValueError('Coordinates are out of range')


class SubImage:
    def __init__(self, descriptor, file_factory, header_template):
        self._descriptor = descriptor

        # Construct the origin offset used to convert from global coordinates. This excludes overlapping voxels
        self._image_size = [1 + this_range[1] - this_range[0] for this_range in descriptor["ranges"]]
        self._origin_start = [this_range[0] for this_range in descriptor["ranges"]]
        self._origin_end = [this_range[1] for this_range in descriptor["ranges"]]
        self._roi_start = [this_range[0] + this_range[2] for this_range in descriptor["ranges"]]
        self._roi_end = [this_range[1] - this_range[3] for this_range in descriptor["ranges"]]
        self._ranges = descriptor["ranges"]

        if header_template:
            header_template["DimSize"] = self._image_size
            header_template["Origin"] = self._origin_start
        self._file = MetaIoFile(descriptor["filename"], file_factory, header_template)

    def get_ranges(self):
        """Returns the full range of global coordinates covered by this subimage"""

        return self._ranges

    def write_image_stream(self, start_coords, image_line):
        """Writes a line of image data to a binary file at the specified image location"""

        start_coords_local = self._convert_coords_to_local(start_coords)
        self._file.write_image_stream(start_coords_local, image_line)

    def read_image_stream(self, start_coords, num_voxels_to_read):
        """Reads a line of image data from a binary file at the specified image location"""

        if not self.contains_voxel(start_coords, True):
            raise ValueError('The data range to load extends beyond this file')

        # Don't read bytes beyond the end of the valid range
        if start_coords[0] + num_voxels_to_read - 1 > self._roi_end[0]:
            num_voxels_to_read = self._roi_end[0] - start_coords[0] + 1

        start_coords_local = self._convert_coords_to_local(start_coords)
        return self._file.read_image_stream(start_coords_local, num_voxels_to_read)

    def contains_voxel(self, start_coords_global, must_be_in_roi):
        """Determines if the specified voxel lies within the ROI of this subimage """

        if must_be_in_roi:
            return (self._roi_start[0] <= start_coords_global[0] <= self._roi_end[0] and
                    self._roi_start[1] <= start_coords_global[1] <= self._roi_end[1] and
                    self._roi_start[2] <= start_coords_global[2] <= self._roi_end[2])
        else:
            return (self._origin_start[0] <= start_coords_global[0] <= self._origin_end[0] and
                    self._origin_start[1] <= start_coords_global[1] <= self._origin_end[1] and
                    self._origin_start[2] <= start_coords_global[2] <= self._origin_end[2])

    def close(self):
        self._file.close()

    def get_bytes_per_voxel(self):
        return self._file.get_bytes_per_voxel()

    def _convert_coords_to_local(self, start_coords):
        return [start_coord - origin_coord for start_coord, origin_coord in zip(start_coords, self._origin_start)]


class MetaIoFile:
    """A class for reading or writing 3D imaging data to/from a MetaIO file pair (.mhd and .raw)."""
    def __init__(self, header_filename, file_factory, header_template):
        self._file_factory = file_factory
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

        return self._get_file_streamer().write_image_stream(start_coords, image_line)

    def read_image_stream(self, start_coords, num_voxels_to_read):
        """Read consecutive voxels of image data from the raw binary file starting at the specified coordinates."""

        return self._get_file_streamer().read_image_stream(start_coords, num_voxels_to_read)

    def get_bytes_per_voxel(self):
        """Return the number of bytes used to represent a single voxel in this image."""

        header = self._get_header()
        return compute_bytes_per_voxel(header["ElementType"])

    def _get_header(self):
        """Return an OrderedDict containing the MetaIO metaheader metadata for this image."""

        if not self._header:
            self._header = load_mhd_header(self._header_filename)
        return self._header

    def _get_file_wrapper(self):
        """Return the HugeFileWrapper representing this image, creating it if it does not already exist."""

        if not self._file_wrapper:
            header = self._get_header()
            filename_raw = os.path.join(self._input_path, header["ElementDataFile"])
            self._file_wrapper = HugeFileWrapper(filename_raw, self._file_factory, self._mode)
        return self._file_wrapper

    def _get_file_streamer(self):
        """Return the HugeFileStreamer representing this image, creating it if it does not already exist."""

        if not self._file_streamer:
            header = self._get_header()
            bytes_per_voxel = compute_bytes_per_voxel(header["ElementType"])
            numpy_format = get_numpy_datatype(header["ElementType"], header["BinaryDataByteOrderMSB"])
            subimage_size = header["DimSize"]
            self._file_streamer = HugeFileStreamer(self._get_file_wrapper(), subimage_size, bytes_per_voxel,
                                                   numpy_format)
        return self._file_streamer

    def close(self):
        """Close the files associated with this image, if they are not already closed."""

        if self._file_streamer:
            self._file_streamer.close()
            self._file_streamer = None
        if self._file_wrapper:
            self._file_wrapper.close()
            self._file_wrapper = None


class HugeFileStreamer:
    """A class to handle streaming of image data with arbitrarily large files"""

    def __init__(self, file_wrapper, image_size, bytes_per_voxel, numpy_format):
        self._bytes_per_voxel = bytes_per_voxel
        self._image_size = image_size
        self._file_wrapper = file_wrapper
        self._numpy_format = numpy_format

    def read_image_stream(self, start_coords, num_voxels_to_read):
        """Read a line of image data from a binary file at the specified image location"""

        offset = self._get_linear_byte_offset(self._image_size, self._bytes_per_voxel, start_coords)
        self._file_wrapper.get_handle().seek(offset)

        dt = np.dtype(self._numpy_format)
        bytes_array = self._file_wrapper.get_handle().read(num_voxels_to_read * self._bytes_per_voxel)
        return np.fromstring(bytes_array, dtype=dt)

    def write_image_stream(self, start_coords, image_line):
        """Write a line of image data to a binary file at the specified image location"""

        offset = self._get_linear_byte_offset(self._image_size, self._bytes_per_voxel, start_coords)
        self._file_wrapper.get_handle().seek(offset)

        dt = np.dtype(self._numpy_format)
        self._file_wrapper.get_handle().write(image_line.astype(dt).tobytes())

    @staticmethod
    def _get_linear_byte_offset(image_size, bytes_per_voxel, start_coords):
        """Return the byte offset corresponding to the point at the given coordinates. 
        
        Assumes you have a stream of bytes representing a multi-dimensional image, 
        """

        offset = 0
        offset_multiple = bytes_per_voxel
        for coord, image_length in zip(start_coords, image_size):
            offset += coord * offset_multiple
            offset_multiple *= image_length
        return offset

    def close(self):
        """Close any files that have been opened."""
        self._file_wrapper.close()


class HugeFileWrapper:
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
        if not self._file_handle:
            self.open()
        return self._file_handle

    def open(self):
        self._file_handle = self._file_handle_factory.create_file_handle(self._filename, self._mode)

    def close(self):
        if self._file_handle and not self._file_handle.closed:
            self._file_handle.close()
            self._file_handle = None


class FileHandleFactory:
    @staticmethod
    def create_file_handle(filename, mode):
        folder = os.path.dirname(filename)
        if not os.path.exists(folder):
            os.makedirs(folder)
        return open(filename, mode)


def load_mhd_header(filename):
    """Return an OrderedDict containing metadata loaded from an mhd file."""

    metadata = OrderedDict()

    with open(filename) as header_file:
        for line in header_file:
            (key, val) = [x.strip() for x in line.split("=")]
            if key in ['ElementSpacing', 'Offset', 'CenterOfRotation', 'TransformMatrix']:
                val = [float(s) for s in val.split()]
            elif key in ['NDims', 'ElementNumberOfChannels']:
                val = int(val)
            elif key in ['DimSize']:
                val = [int(s) for s in val.split()]
            elif key in ['BinaryData', 'BinaryDataByteOrderMSB', 'CompressedData']:
                if val.lower() == "true":
                    val = True
                else:
                    val = False

            metadata[key] = val

    return metadata


def compute_bytes_per_voxel(element_type):
    """Returns number of bytes required to store one voxel for the given metaIO ElementType"""

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

    f = open(filename, 'w')
    f.write(header)
    f.close()


def generate_input_descriptors(input_file_base, start_index):
    descriptors = []

    if start_index is None:
        # If no start index is specified, load a single header file
        header_filename = input_file_base + '.mhd'
        combined_header = load_mhd_header(header_filename)
        current_image_size = combined_header["DimSize"]
        current_ranges = [[0, current_image_size[0] - 1, 0, 0],
                          [0, current_image_size[1] - 1, 0, 0],
                          [0, current_image_size[2] - 1, 0, 0]]

        # Create a descriptor for this subimage
        descriptor = {"index": 0, "suffix": "", "filename": header_filename, "ranges": current_ranges}
        descriptors.append(descriptor)
        return combined_header, descriptors

    else:
        # Load a series of files starting with the specified prefix
        file_index = start_index
        suffix = str(file_index)
        header_filename = input_file_base + suffix + '.mhd'

        if not os.path.isfile(header_filename):
            raise ValueError('No file series found starting with ' + header_filename)

        current_ranges = None
        combined_header = None
        full_image_size = None
        while True:
            suffix = str(file_index)
            header_filename = input_file_base + suffix + '.mhd'
            if not os.path.isfile(header_filename):
                return combined_header, descriptors
            current_header = load_mhd_header(header_filename)
            current_image_size = current_header["DimSize"]
            if not current_ranges:
                full_image_size = copy.deepcopy(current_image_size)
                combined_header = copy.deepcopy(current_header)
                current_ranges = [[0, current_image_size[0] - 1, 0, 0],
                                  [0, current_image_size[1] - 1, 0, 0],
                                  [0, current_image_size[2] - 1, 0, 0]]
            else:
                if not current_image_size[0] == full_image_size[0]:
                    raise ValueError('When loading without a descriptor file, the first dimension of each file must '
                                     'match')
                if not current_image_size[1] == full_image_size[1]:
                    raise ValueError('When loading without a descriptor file, the second dimension of each file must '
                                     'match')
                full_image_size[2] = full_image_size[2] + current_image_size[2]
                current_ranges[2][0] = current_ranges[2][1] + 1
                current_ranges[2][1] = current_ranges[2][1] + current_image_size[2]

            # Update the combined image size
            combined_header["DimSize"] = full_image_size

            # Create a descriptor for this subimage
            ranges_to_write = copy.deepcopy(current_ranges)
            descriptor = {"index": file_index, "suffix": suffix, "filename": header_filename, "ranges": ranges_to_write}
            descriptors.append(descriptor)

            file_index += 1


def get_default_metadata():
    """Return an OrderedDict containing default mhd file metadata"""

    return OrderedDict(
        [('ObjectType', 'Image'), ('NDims', '3'), ('BinaryData', 'True'), ('BinaryDataByteOrderMSB', 'True'),
         ('CompressedData', []), ('CompressedDataSize', []), ('TransformMatrix', []), ('Offset', []),
         ('CenterOfRotation', []), ('AnatomicalOrientation', []), ('ElementSpacing', []), ('DimSize', []),
         ('ElementNumberOfChannels', []), ('ElementSize', []), ('ElementType', 'MET_FLOAT'), ('ElementDataFile', []),
         ('Comment', []), ('SeriesDescription', []), ('AcquisitionDate', []), ('AcquisitionTime', []),
         ('StudyDate', []), ('StudyTime', [])])
