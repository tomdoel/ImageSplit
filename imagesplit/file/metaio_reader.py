# coding=utf-8
"""
Utility for reading and writing data to metaio (mhd/mha) files

Author: Tom Doel
Copyright UCL 2017

"""
import copy
import os
from collections import OrderedDict

import numpy as np

from imagesplit.file.data_type import DataType
from imagesplit.file.file_image_descriptor import FileImageDescriptor
from imagesplit.file.file_wrapper import FileWrapper, FileStreamer
from imagesplit.file.image_file_reader import LinearImageFileReader
from imagesplit.image.combined_image import Axis
from imagesplit.utils.utilities import compute_bytes_per_voxel, \
    get_numpy_datatype


class MetaIoFile(LinearImageFileReader):
    """A class for reading or writing 3D imaging data to/from a MetaIO file
    pair (.mhd and .raw). """

    # pylint: disable=too-many-instance-attributes

    def __init__(self, local_file_size, header_filename,
                 file_handle_factory, header_template):
        super(MetaIoFile, self).__init__(local_file_size)
        self._file_handle_factory = file_handle_factory
        self._header_filename = header_filename
        self._input_path = os.path.dirname(os.path.abspath(header_filename))
        self._file_wrapper = None
        self._file_streamer = None
        if header_template:
            # File is for writing
            self._mode = 'wb'
            # Force the raw filename to match the header filename
            base_filename = os.path.splitext(
                os.path.basename(header_filename))[0]
            header = copy.deepcopy(header_template)
            header['ElementDataFile'] = base_filename + '.raw'

            save_mhd_header(header_filename, header)
            self._header = header

        else:
            # File is for reading
            self._mode = 'rb'
            self._header = load_mhd_header(header_filename)

        self._bytes_per_voxel = compute_bytes_per_voxel(
            self._header["ElementType"]) # ToDo: set this based on output format
        self._numpy_format = get_numpy_datatype(
            self._header["ElementType"],
            self._header["BinaryDataByteOrderMSB"])
        self._subimage_size = self._header["DimSize"]
        self._dimension_ordering = get_condensed_dim_order(self._header)

    @classmethod
    def load_and_parse_header(cls, filename):
        """Reads a MetaIO header file and parses"""

        header = load_mhd_header(filename)
        return parse_mhd(header)

    @classmethod
    def create_read_file(cls, subimage_descriptor, file_handle_factory):
        """Create a MetaIoFile class for writing"""

        filename = subimage_descriptor.filename
        local_file_size = subimage_descriptor.ranges.image_size
        return cls(local_file_size, filename, file_handle_factory, None)

    @classmethod
    def create_write_file(cls, subimage_descriptor, file_handle_factory):
        """Create a MetaIoFile class for this filename and template"""

        header_template = cls._create_meta_header(subimage_descriptor)
        # header_template = copy.deepcopy(subimage_descriptor.template)
        local_file_size = subimage_descriptor.get_local_size()
        local_origin = subimage_descriptor.get_local_origin()

        if subimage_descriptor.data_type:
            header_template["ElementType"] = \
                DataType.metaio_from_name(subimage_descriptor.data_type)
        header_template["DimSize"] = local_file_size
        header_template["Origin"] = local_origin
        filename = subimage_descriptor.filename
        return cls(local_file_size, filename, file_handle_factory,
                   header_template)

    def close_file(self):
        """Close file"""
        self.close()

    def write_line(self, start_coords, image_line, rescale_limits):
        """Write consecutive voxels to the raw binary file."""

        return self._get_file_streamer().write_line(
            start_coords, image_line, rescale_limits)

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

    @classmethod
    def _create_meta_header(cls, subimage_descriptor):
        local_file_size = subimage_descriptor.get_local_size()
        local_origin = subimage_descriptor.get_local_origin()
        local_voxel_size = subimage_descriptor.get_local_voxel_size()

        transform_matrix = condensed_to_cosine(
            subimage_descriptor.axis.to_condensed_format())

        header = get_default_metadata()
        header["ObjectType"] = 'Image'
        header["NDims"] = np.size(local_file_size)
        header["BinaryData"] = 'True'
        header["BinaryDataByteOrderMSB"] = subimage_descriptor.msb
        header["CompressedData"] = 'False'
        header["TransformMatrix"] = transform_matrix
        header["ElementSize"] = local_voxel_size
        header["DimSize"] = local_file_size
        header["ElementType"] = \
            DataType.metaio_from_name(subimage_descriptor.data_type)
        header["Origin"] = local_origin

        return header

    def _get_header(self):
        """Return an OrderedDict containing the MetaIO metaheader metadata
        for this image. """

        if not self._header:
            self._header = load_mhd_header(self._header_filename)
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


def load_mhd_header(filename):
    """Return an OrderedDict containing metadata loaded from an mhd file."""

    metadata = OrderedDict()

    with open(filename) as header_file:
        for line in header_file:
            (key, val) = [x.strip() for x in line.split("=")]
            if key in ['ElementSpacing', 'Offset', 'CenterOfRotation',
                       'TransformMatrix', 'ElementSize']:
                new_val = [float(s) for s in val.split()]
            elif key in ['NDims', 'ElementNumberOfChannels']:
                new_val = int(val)
            elif key in ['DimSize']:
                new_val = [int(s) for s in val.split()]
            elif key in ['BinaryData', 'BinaryDataByteOrderMSB',
                         'CompressedData']:
                # pylint: disable=simplifiable-if-statement
                if val.lower() == "true":
                    new_val = True
                else:
                    new_val = False
            else:
                new_val = val

            metadata[key] = new_val

    return metadata


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


def get_condensed_dim_order(header):
    """Return the condensed dimension order and flip string for this header"""
    if header["TransformMatrix"]:
        transform = header["TransformMatrix"]
        new_dimension_order, flip_orientation = \
            mhd_cosines_to_permutation(
                transform[0:3], transform[3:6], transform[6:9])
    elif header["AnatomicalOrientation"]:
        new_dimension_order, flip_orientation = \
            anatomical_to_permutation(
                header["AnatomicalOrientation"])
    else:
        new_dimension_order = [0, 1, 2]
        flip_orientation = [False, False, False]

    return Axis(new_dimension_order, flip_orientation).to_condensed_format()


def anatomical_to_permutation(anatomical_orientation_string):
    """Dimension permutation vector corresponding to this orientation string"""

    direction_cosine_1 = \
        anatomical_to_cosine(anatomical_orientation_string[0])
    direction_cosine_2 = \
        anatomical_to_cosine(anatomical_orientation_string[1])
    direction_cosine_3 = \
        anatomical_to_cosine(anatomical_orientation_string[2])

    permutation_vector, flip_orientation = \
        mhd_cosines_to_permutation(
            direction_cosine_1, direction_cosine_2, direction_cosine_3)

    return permutation_vector, flip_orientation


def anatomical_to_cosine(anatomical_orientation_char):
    """Get Dicom direction cosine for this orientation string"""
    if anatomical_orientation_char == 'R':
        return [1, 0, 0]
    elif anatomical_orientation_char == 'L':
        return [-1, 0, 0]
    elif anatomical_orientation_char == 'A':
        return [0, 1, 0]
    elif anatomical_orientation_char == 'P':
        return [0, -1, 0]
    elif anatomical_orientation_char == 'I':
        return [0, 0, 1]
    elif anatomical_orientation_char == 'S':
        return [0, 0, -1]
    else:
        raise ValueError('No implementation yet for anatomical orientation ' +
                         anatomical_orientation_char + '.')


def permutation_to_cosine(permutation, flip):
    """Get mhd direction cosine for this dimension permutation"""

    dir_cosine = [0, 0, 0, 0, 0, 0, 0, 0, 0]
    dir_cosine[permutation[0]*3] = -1 if flip[0] else 1
    dir_cosine[permutation[1]*3 + 1] = -1 if flip[1] else 1
    dir_cosine[permutation[2]*3 + 2] = -1 if flip[2] else 1

    return dir_cosine


def condensed_to_cosine(condensed_format):
    """Get mhd direction cosine for this condensed format axis"""

    axis = Axis.from_condensed_format(condensed_format)
    return permutation_to_cosine(axis.dim_order, axis.dim_flip)


def mhd_cosines_to_permutation(direction_cosine_1,
                               direction_cosine_2,
                               direction_cosine_3):
    """Get dimension permutation vectors for these mhd direction cosines"""
    orientation_1 = direction_cosine_1
    orientation_2 = direction_cosine_2
    orientation_3 = direction_cosine_3

    permutation_vector, dimension_1, dimension_2, dimension_3 = \
        permutation_from_orientations(orientation_1, orientation_2)

    flip_orientation = get_flip_from_orientations(
        orientation_1, orientation_2, orientation_3, dimension_1, dimension_2,
        dimension_3)
    if np.sum(np.equal(permutation_vector, 0)) != 1 or \
            np.sum(np.equal(permutation_vector, 1)) != 1 or \
            np.sum(np.equal(permutation_vector, 2)) != 1 or \
            np.size(np.setdiff1d(permutation_vector, [0, 1, 2])) != 0:
        raise ValueError('Invalid permutation vector')

    return permutation_vector, flip_orientation


def permutation_from_orientations(orientation_1, orientation_2):
    """Get dimension permutation vectors for these orientation vectors"""
    dimension_1, dimension_2, dimension_3 = \
        dimensions_from_orientations(orientation_1, orientation_2)

    permutation_vector = [2, 2, 2]
    permutation_vector[dimension_1] = 0
    permutation_vector[dimension_2] = 1
    return permutation_vector, dimension_1, dimension_2, dimension_3


def dimensions_from_orientations(orientation_vector_1,
                                 orientation_vector_2):
    """Get dimension permutation vectors for these orientation vectors"""

    dimension_number_1 = np.argmax(np.abs(orientation_vector_1))
    remaining_dimensions = np.setdiff1d([0, 1, 2], dimension_number_1)
    reduced_orientation_vector_2 = np.take(orientation_vector_2,
                                           remaining_dimensions)
    dim2_from_reduced_set = np.argmax(np.abs(reduced_orientation_vector_2))
    dimension_number_2 = remaining_dimensions[dim2_from_reduced_set]
    dimension_number_3 = np.setdiff1d([0, 1, 2],
                                      [dimension_number_1, dimension_number_2])
    dimension_number_3 = dimension_number_3[0]
    return dimension_number_1, dimension_number_2, dimension_number_3


def get_flip_from_orientations(orientation_1, orientation_2, orientation_3,
                               dimension_1, dimension_2, dimension_3):
    """Get dimension flip vectors for these orientation vectors"""

    flip = [False, False, False]
    flip[dimension_1] = orientation_1[dimension_1] < 0
    flip[dimension_2] = orientation_2[dimension_2] < 0
    flip[dimension_3] = orientation_3[dimension_3] < 0
    return flip


def parse_mhd(header):
    """Read a metaheader and returns a FileImageDescriptor"""

    file_format = "mhd"
    dim_order = get_condensed_dim_order(header)
    data_type = DataType.name_from_metaio(header["ElementType"])
    image_size = header["DimSize"]
    msb = header["BinaryDataByteOrderMSB"]
    compression = None
    voxel_size = header['ElementSize']
    return (FileImageDescriptor(file_format=file_format,
                                dim_order=dim_order,
                                data_type=data_type,
                                image_size=image_size,
                                msb=msb,
                                compression=compression,
                                voxel_size=voxel_size), header)
