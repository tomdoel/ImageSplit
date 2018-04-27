from unittest import TestCase

from imagesplit.file.data_type import DataType


class TestDataType(TestCase):
    def test_name_from_metaio(self):
        self.assertEqual(DataType.name_from_metaio("MET_SHORT"), "short")

    def test_metaio_from_name(self):
        self.assertEqual(DataType.metaio_from_name("short"), "MET_SHORT")
