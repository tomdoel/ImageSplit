import unittest
from unittest import TestCase

from parameterized import parameterized, param

from imagesplit.file.metaio_reader import mhd_cosines_to_permutation, \
    permutation_to_cosine
from imagesplit.utils.utilities import compute_bytes_per_voxel


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

    @parameterized.expand([
        param(cosines=[1, 0, 0, 0, 1, 0, 0, 0, 1]),
        param(cosines=[1, 0, 0, 0, 0, 1, 0, 1, 0]),
        param(cosines=[0, 1, 0, 1, 0, 0, 0, 0, 1]),
        param(cosines=[0, 1, 0, 0, 0, 1, 1, 0, 0]),
        param(cosines=[0, 0, 1, 1, 0, 0, 0, 1, 0]),
        param(cosines=[0, 0, 1, 0, 1, 0, 1, 0, 0]),
    ])
    def test_mhd_cosines_to_permutation(self, cosines):
        for flip_i in [-1, 1]:
            for flip_j in [-1, 1]:
                for flip_k in [-1, 1]:
                    c1 = [x * flip_i for x in cosines[0:3]]
                    c2 = [x * flip_j for x in cosines[3:6]]
                    c3 = [x * flip_k for x in cosines[6:9]]
                    perm_computed, flip_computed = mhd_cosines_to_permutation(c1, c2, c3)
                    cosines_computed = permutation_to_cosine(perm_computed, flip_computed)
                    self.assertEqual(cosines_computed, c1 + c2 + c3)
