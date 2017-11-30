# coding=utf-8

"""Read and write data to TIFF files"""
from tifffile import imread, imsave

from niftysplit.file.data_type import DataType
from niftysplit.file.image_file_reader import BlockImageFileReader


class TiffFileReader(BlockImageFileReader):
    """Read and write to TIFF files"""

    def __init__(self, filename, image_size, data_type):
        super(TiffFileReader, self).__init__(image_size, data_type)
        self.read_image = None
        self.filename = filename

    def close_file(self):
        """Closes file if required"""

    def load(self):
        """Load image data from TIFF file"""
        if not self.read_image:
            self.read_image = imread(self.filename)
        return self.read_image

    def save(self, image):
        """Save out image data into TIFF file"""
        # imsave(self.filename, image, imagej=True, compress='lzma')
        imsave(self.filename, image)
        # imsave(self.filename, image, compress='lzma')

    @staticmethod
    # pylint: disable=unused-argument
    def create_write_file(subimage_descriptor, file_handle_factory):
        """Create a TiffFileReader class for this filename and template"""
        filename = subimage_descriptor.filename
        local_file_size = subimage_descriptor.get_local_size()
        byte_order_msb = subimage_descriptor.msb
        data_type = DataType(subimage_descriptor.data_type,
                             byte_order_msb=byte_order_msb)
        return TiffFileReader(filename, local_file_size, data_type)
