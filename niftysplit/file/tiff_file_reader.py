# coding=utf-8

"""Read and write data to TIFF files"""
from tifffile import imread, imsave
from niftysplit.file.image_file_reader import BlockImageFileReader


class TiffFileReader(BlockImageFileReader):
    """Read and write to TIFF files"""

    def __init__(self, filename, image_size):
        super(TiffFileReader, self).__init__(image_size)
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
        imsave(self.filename, image)

    @staticmethod
    def create_write_file(subimage_descriptor, file_handle_factory):
        """Create a TiffFileReader class for this filename and template"""
        filename = subimage_descriptor.filename
        image_size = subimage_descriptor.ranges.image_size
        return TiffFileReader(filename, image_size)
