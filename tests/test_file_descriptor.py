from unittest import TestCase

from imagesplit.utils.file_descriptor import SubImageDescriptor


class TestSubImageDescriptor(TestCase):
    def test_from_dict(self):
        d_orig = self.make_dict()
        sid = SubImageDescriptor.from_dict(d_orig)
        d2 = SubImageDescriptor.to_dict(sid)
        self.assertDictEqual(d_orig, d2)

    @staticmethod
    def make_dict():
        """Returns a dictionary object representing a subimage descriptor"""
        return {"index": 1,
                "suffix": "suf",
                "filename": "my-filename",
                "data_type": "short",
                "file_format": "mhd",
                "template": {"a": 1, "b": "blah"},
                "dim_order": [1, 2, 3],
                "compression": None,
                "msb": False,
                "voxel_size": [1.0, 1.0, 1.0],
                "ranges": [[0, 11, 0, 2], [0, 11, 0, 2], [0, 11, 0, 2]]}
