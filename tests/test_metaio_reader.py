import unittest

from niftysplit.file.metaio_reader import compute_bytes_per_voxel


class TestMetaIoReader(unittest.TestCase):
    """Tests for MetaIoReader"""

    def test_compute_bytes_per_voxel(self):
        self.assertEqual(compute_bytes_per_voxel('MET_CHAR'), 1)
        self.assertEqual(compute_bytes_per_voxel('MET_UCHAR'), 1)
        self.assertEqual(compute_bytes_per_voxel('MET_SHORT'), 2)
        self.assertEqual(compute_bytes_per_voxel('MET_USHORT'), 2)
        self.assertEqual(compute_bytes_per_voxel('MET_INT'), 4)
        self.assertEqual(compute_bytes_per_voxel('MET_UINT'), 4)
        self.assertEqual(compute_bytes_per_voxel('MET_LONG'), 4)
        self.assertEqual(compute_bytes_per_voxel('MET_ULONG'), 4)
        self.assertEqual(compute_bytes_per_voxel('MET_LONG_LONG'), 8)
        self.assertEqual(compute_bytes_per_voxel('MET_ULONG_LONG'), 8)
        self.assertEqual(compute_bytes_per_voxel('MET_FLOAT'), 4)
        self.assertEqual(compute_bytes_per_voxel('MET_DOUBLE'), 8)