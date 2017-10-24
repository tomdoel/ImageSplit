from math import ceil

from niftysplit.utils.json_reader import write_json, read_json
from utils.metaio_reader import load_mhd_header


class SubImageDescriptor(object):
    """Describes an image in relation to a larger image"""

    def __init__(self, descriptor_dict):
        self._descriptor = descriptor_dict
        self.image_size = self._get_image_size()
        self.origin_start = self._get_origin_start()
        self.origin_end = self._get_origin_end()
        self.roi_start = self._get_roi_start()
        self.roi_end = self._get_roi_end()
        self.ranges = self._get_ranges()

    def _get_ranges(self):
        return self._descriptor["ranges"]

    def _get_roi_end(self):
        return [this_range[1] - this_range[3] for this_range in
                self._descriptor["ranges"]]

    def _get_roi_start(self):
        return [this_range[0] + this_range[2] for this_range in
                self._descriptor["ranges"]]

    def _get_origin_end(self):
        return [this_range[1] for this_range in
                self._descriptor["ranges"]]

    def _get_origin_start(self):
        return [this_range[0] for this_range in
                self._descriptor["ranges"]]

    def _get_image_size(self):
        """Return the size of this subvolume including overlap regions"""
        return [1 + this_range[1] - this_range[0] for this_range in
                self._descriptor["ranges"]]


def get_number_of_blocks(image_size, max_block_size):
    """Returns a list containing the number of blocks in each dimension
    required to split the image into blocks that are subject to a maximum
    size limit """

    return [int(ceil(float(image_size_element) / float(max_block_size_element))) for
            image_size_element, max_block_size_element in
            zip(image_size, max_block_size)]


def get_block_coordinate_range(block_number, block_size, overlap_size,
                               image_size):
    """Returns the minimum and maximum coordinate values in one dimension for
    an image block, where the dimension length image_size is to be split into
    the number of blocks specified by block_size with an overlap of
    overlap_size voxels at each boundary, and the current block_number is
    specified. There is no overlap at the outer border of the image, and the
    length of the final block is reduced if necessary so there is no padding """

    # Compute the minimum coordinate of the block
    if block_number == 0:
        min_coord = 0
        start_border = 0
    else:
        min_coord = block_number * block_size - overlap_size
        start_border = overlap_size

    # Compute the maximum coordinate of the block
    end_border = overlap_size
    max_coord = int((block_number + 1) * block_size - 1 + overlap_size)
    if max_coord >= image_size:
        max_coord = image_size - 1
        end_border = 0

    return min_coord, max_coord, start_border, end_border


def get_suggested_block_size(image_size, number_of_blocks):
    """Returns a recommended block size (a list of the number of blocks in
    each dimension) to allow the specified image_size to be split into the
    specified number of blocks in each dimension, with each block being
    roughly equal in size """

    return [ceil(float(image_size_element) / float(number_of_blocks_element))
            for image_size_element, number_of_blocks_element in
            zip(image_size, number_of_blocks)]


def get_image_block_ranges(image_size, max_block_size, overlap_size):
    """Returns a list of ranges, where each recommended block size (a list of
    the number of blocks in each dimension) to allow the specified image_size
    to be split into the specified number of blocks in each dimension,
    with each block being roughly equal in size """

    number_of_blocks = get_number_of_blocks(image_size, max_block_size)
    suggested_block_size = get_suggested_block_size(image_size,
                                                    number_of_blocks)
    block_ranges = []

    for i in range(number_of_blocks[0]):
        for j in range(number_of_blocks[1]):
            for k in range(number_of_blocks[2]):
                block_ranges.append(
                    [get_block_coordinate_range(index, block, overlap, size) for
                     index, block, overlap, size in
                     zip([i, j, k], suggested_block_size, overlap_size,
                         image_size)])

    return block_ranges


def write_descriptor_file(descriptors_in, descriptors_out, filename_out_base):
    """Saves descriptor files"""
    descriptor = {"appname": "GIFT-Surg split data", "version": "1.0",
                  "split_files": descriptors_out,
                  "source_files": descriptors_in}
    descriptor_output_filename = filename_out_base + "_info.gift"
    write_json(descriptor_output_filename, descriptor)


def generate_output_descriptors(filename_out_base, max_block_size_voxels,
                                overlap_size_voxels, header):
    """Creates descriptors represeting file output"""
    image_size = header["DimSize"]
    num_dims = header["NDims"]
    max_block_size_voxels_array = convert_to_array(max_block_size_voxels,
                                                   "block size", num_dims)
    overlap_voxels_size_array = convert_to_array(overlap_size_voxels,
                                                 "overlap size", num_dims)
    ranges = get_image_block_ranges(image_size, max_block_size_voxels_array,
                                    overlap_voxels_size_array)

    descriptors_out = []
    index = 0
    for subimage_range in ranges:
        suffix = "_" + str(index)
        output_filename_header = filename_out_base + suffix + ".mhd"
        file_descriptor_out = {"filename": output_filename_header,
                               "ranges": subimage_range, "suffix": suffix,
                               "index": index}
        descriptors_out.append(file_descriptor_out)
        index += 1
    return descriptors_out


def convert_to_array(scalar_or_list, parameter_name, num_dims):
    """Converts a list or scalar to an array"""
    if not isinstance(scalar_or_list, list):
        array = [scalar_or_list] * num_dims
    elif len(scalar_or_list) == num_dims:
        array = scalar_or_list
    else:
        raise ValueError(
            'The ' + parameter_name + 'parameter must be a scalar, or a list '
                                      'containing one entry for '
                                      'each image dimension')
    return array


def load_descriptor(descriptor_filename):
    """Loads and parses a file descriptor from disk"""
    data = read_json(descriptor_filename)
    if data["appname"] != "GIFT-Surg split data":
        raise ValueError('Not a GIFT-Surg file')
    if data["version"] != "1.0":
        raise ValueError('Cannot read this file version')
    return data


def generate_descriptor_from_header(filename_out_base, original_header):
    """Load a header and uses to define a file descriptor"""
    output_image_size = original_header["DimSize"]
    descriptors_out = []
    descriptor_out = {"index": 0, "suffix": "",
                      "filename": filename_out_base + '.mhd',
                      "ranges": [[0, output_image_size[0] - 1, 0, 0],
                                 [0, output_image_size[1] - 1, 0, 0],
                                 [0, output_image_size[2] - 1, 0, 0]]}
    descriptors_out.append(descriptor_out)
    return descriptors_out


def header_from_descriptor(descriptor_filename):
    """Create a file header based on descriptor information"""
    descriptor = load_descriptor(descriptor_filename)
    original_file_list = descriptor["source_files"]
    if len(original_file_list) != 1:
        raise ValueError(
            'This function only supports data derived from a single file')
    original_file_descriptor = original_file_list[0]
    original_header = load_mhd_header(
        original_file_descriptor["filename"])
    input_file_list = descriptor["split_files"]
    return original_header, input_file_list