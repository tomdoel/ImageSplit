from image.image_wrapper import ImageWrapper
from utils.sub_image import SubImage


class CombinedImage(object):
    """A kind of virtual file for writing where the data are distributed
        across multiple real files. """

    def __init__(self, descriptors, file_factory):
        """Create for the given set of descriptors"""

        self._subimages = []
        for subimage_descriptor in descriptors:
            self._subimages.append(SubImage(subimage_descriptor, file_factory))

    def write_image_file(self, input_combined):
        """Write out all the subimages"""

        # Get each subimage to write itself
        for next_image in self._subimages:
            next_image.write_subimage(input_combined)

    def read_image(self, start_global, size):
        """Assembles an image range from subimages"""

        combined_image = ImageWrapper(start_global, image_size=size)
        for next_subimage in self._subimages:
            part_image = next_subimage.read_part_image(start_global, size)
            if part_image:
                combined_image.set_sub_image(part_image)

    def close(self):
        """Closes all streams and files"""
        for subimage in self._subimages:
            subimage.close()