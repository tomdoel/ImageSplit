from unittest import TestCase

from file.linear_image_file import AbstractImageFile
from niftysplit.image.combined_image import SubImage
from niftysplit.utils.file_descriptor import SubImageDescriptor


class TestSubImage(TestCase):
    pass
    # range = (min_coord, max_coord, start_border, end_border)
    # file_factory = FakeFileFactory()
    # descriptor_dict = {"filename": 'TestFileName',
    #                        "ranges": range, "suffix": "SUFFIX",
    #                        "index": index,
    #                        "dim_order": dim_order,
    #                        "data_type": output_type,
    #                        "header": copy.deepcopy(header)}
    #
    # descriptor = SubImageDescriptor(descriptor_dict)
    # si = SubImage(descriptor, file_factory)


class FakeFileFactory(object):
    """Create objects for handling file input and output"""

    def __init__(self, file_handle_factory):
        self._file_handle_factory = file_handle_factory
        self._metaio_factory = None

    def create_read_file(self, subimage_descriptor):
        """Create a class for reading"""

        return FakeImageFile()

    def create_write_file(self, subimage_descriptor):
        """Create a class for writing"""

        return FakeImageFile()


class FakeImageFile(AbstractImageFile):
    def write_file(self, data_source):
        pass
