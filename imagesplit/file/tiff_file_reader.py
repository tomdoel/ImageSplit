# coding=utf-8

"""Read and write data to TIFF files"""
import os
import numpy as np
from PIL import Image, TiffImagePlugin

from imagesplit.file.data_type import DataType
from imagesplit.file.image_file_reader import BlockImageFileReader


class TiffFileReader(BlockImageFileReader):
    """Read and write to TIFF files"""

    def __init__(self, filename, image_size, data_type):
        super(TiffFileReader, self).__init__(image_size, data_type)
        self.cached_image = None
        self.filename = filename

    def close_file(self):
        """Closes file if required"""

    def load(self):
        """Load image data from TIFF file"""
        if not self.cached_image:
            img = Image.open(self.filename)
            self.cached_image = np.array(img)
        return self.cached_image

    def save(self, image):
        """Save out image data into TIFF file"""
        compression = self.data_type.compression

        if compression == 'default':
            compression = 'tiff_adobe_deflate'

        if compression not in [None,
                               'packbits',
                               'tiff_deflate',
                               'tiff_adobe_deflate',
                               'tiff_sgilog23',
                               'tiff_raw16']:
            raise ValueError(
                compression + ' compression not supported for TIFF files')

        img = Image.fromarray(image)

        if compression:
            # Set WRITE_LIBTIFF to true for compression, but restore previous
            # value afterwards in case user has deliberately set a value
            write_libtiff_previous_value = TiffImagePlugin.WRITE_LIBTIFF
            try:
                TiffImagePlugin.WRITE_LIBTIFF = True
                img.save(self.filename, compression=compression)

            finally:
                TiffImagePlugin.WRITE_LIBTIFF = write_libtiff_previous_value

        else:
            img.save(self.filename)

    @staticmethod
    # pylint: disable=unused-argument
    def create_write_file(subimage_descriptor, file_handle_factory):
        """Create a TiffFileReader class for this filename and template"""
        filename = subimage_descriptor.filename
        local_file_size = subimage_descriptor.get_local_size()
        byte_order_msb = subimage_descriptor.msb
        compression = subimage_descriptor.compression
        data_type = DataType(subimage_descriptor.data_type,
                             byte_order_msb=byte_order_msb,
                             compression=compression)
        return TiffFileReader(filename, local_file_size, data_type)

    @staticmethod
    def add_filename_suffix(filename, suffix):
        """Adds a suffix to to the filename before the extension"""
        name, ext = os.path.splitext(filename)
        return "{name}_{suffix}{ext}".format(name=name, suffix=suffix, ext=ext)
