from unittest import TestCase
from mock import Mock

import numpy as np
from parameterized import parameterized, param

from niftysplit.file.linear_image_file import AbstractImageFile
from niftysplit.image.combined_image import SubImage, Source, \
    CoordinateTransformer, CombinedImage
from niftysplit.image.image_wrapper import ImageWrapper
from niftysplit.utils.file_descriptor import SubImageDescriptor


class FakeImageFile(AbstractImageFile, Source):
    """Fake data source"""

    def __init__(self, descriptor):
        self.descriptor = descriptor
        self.open = True

    def read_image(self, start_global, size):
        pass

    def write_image(self, data_source):
        pass

    def close(self):
        self.open = False


class FakeFileFactory(object):
    """Create objects for handling file input and output"""

    def __init__(self):
        self.read_files = []
        self.write_files = []

    def create_read_file(self, descriptor):
        """Create a class for reading"""

        read_file = FakeImageFile(descriptor)
        self.read_files.append(read_file)
        return read_file

    def create_write_file(self, descriptor):
        """Create a class for writing"""

        write_file = FakeImageFile(descriptor)
        self.write_files.append(write_file)
        return write_file


class TestCombinedImage(TestCase):

    def test_combined_image(self):
        d1 = self._make_descriptor(1, [[0, 9, 0, 2], [0,  9,  0, 2], [0,  9,  0, 2]])
        d2 = self._make_descriptor(2, [[0, 9, 0, 2], [0,  9,  0, 2], [10, 19, 0, 2]])
        d3 = self._make_descriptor(3, [[0, 9, 0, 2], [0,  9,  0, 2], [20, 29, 0, 2]])
        d4 = self._make_descriptor(4, [[0, 9, 0, 2], [10, 19, 2, 2], [0,  9,  2, 2]])
        d5 = self._make_descriptor(5, [[0, 9, 0, 2], [10, 19, 2, 2], [10, 19, 2, 2]])
        d6 = self._make_descriptor(6, [[0, 9, 0, 2], [10, 19, 2, 2], [20, 29, 2, 2]])
        d7 = self._make_descriptor(7, [[0, 9, 0, 2], [20, 29, 2, 0], [0,  9,  2, 0]])
        d8 = self._make_descriptor(8, [[0, 9, 0, 2], [20, 29, 2, 0], [10, 19, 2, 0]])
        d9 = self._make_descriptor(9, [[0, 9, 0, 2], [20, 29, 2, 0], [20, 29, 2, 0]])

        d11 = self._make_descriptor(11, [[10, 19, 0, 2], [0,  9,  0, 2], [0,  9,  0, 2]])
        d12 = self._make_descriptor(12, [[10, 19, 0, 2], [0,  9,  0, 2], [10, 19, 0, 2]])
        d13 = self._make_descriptor(13, [[10, 19, 0, 2], [0,  9,  0, 2], [20, 29, 0, 2]])
        d14 = self._make_descriptor(14, [[10, 19, 0, 2], [10, 19, 2, 2], [0,  9,  2, 2]])
        d15 = self._make_descriptor(15, [[10, 19, 0, 2], [10, 19, 2, 2], [10, 19, 2, 2]])
        d16 = self._make_descriptor(16, [[10, 19, 0, 2], [10, 19, 2, 2], [20, 29, 2, 2]])
        d17 = self._make_descriptor(17, [[10, 19, 0, 2], [20, 29, 2, 0], [0,  9,  2, 0]])
        d18 = self._make_descriptor(18, [[10, 19, 0, 2], [20, 29, 2, 0], [10, 19, 2, 0]])
        d19 = self._make_descriptor(19, [[10, 19, 0, 2], [20, 29, 2, 0], [20, 29, 2, 0]])

        d21 = self._make_descriptor(21, [[20, 29, 0, 2], [0,  9,  0, 2], [0,  9,  0, 2]])
        d22 = self._make_descriptor(22, [[20, 29, 0, 2], [0,  9,  0, 2], [10, 19, 0, 2]])
        d23 = self._make_descriptor(23, [[20, 29, 0, 2], [0,  9,  0, 2], [20, 29, 0, 2]])
        d24 = self._make_descriptor(24, [[20, 29, 0, 2], [10, 19, 2, 2], [0,  9,  2, 2]])
        d25 = self._make_descriptor(25, [[20, 29, 0, 2], [10, 19, 2, 2], [10, 19, 2, 2]])
        d26 = self._make_descriptor(26, [[20, 29, 0, 2], [10, 19, 2, 2], [20, 29, 2, 2]])
        d27 = self._make_descriptor(27, [[20, 29, 0, 2], [20, 29, 2, 0], [0,  9,  2, 0]])
        d28 = self._make_descriptor(28, [[20, 29, 0, 2], [20, 29, 2, 0], [10, 19, 2, 0]])
        d29 = self._make_descriptor(29, [[20, 29, 0, 2], [20, 29, 2, 0], [20, 29, 2, 0]])

        descriptors = [d1, d2, d3, d4, d5, d6, d7, d8, d9,
                       d11, d12, d13, d14, d15, d16, d17, d18, d19,
                       d21, d22, d23, d24, d25, d26, d27, d28, d29]

        file_factory = FakeFileFactory()

        ci = CombinedImage(descriptors, file_factory)
        source = Mock()
        ci.write_image(source)
        self.assertEquals(len(file_factory.write_files), 27)
        for descriptor, write_file in zip(descriptors, file_factory.write_files):
            self.assertEquals(descriptor.ranges, write_file.descriptor.ranges)
            self.assertFalse(write_file.open)

        # ToDo: test read and close

    def _make_descriptor(self, index, ranges):
        return SubImageDescriptor({"filename": 'TestFileName',
            "ranges": ranges, "suffix": "SUFFIX", "dim_order": [1, 2, 3],
            "data_type": "XXXX", "index": index, "template": []})


class TestSubImage(TestCase):

    def test_close(self):
        descriptor = SubImageDescriptor({
            "filename": 'TestFileName',
            "ranges": [[0, 10, 0, 0], [0, 10, 0, 0], [0, 10, 0, 0]],
            "suffix": "SUFFIX",
            "index": 0,
            "dim_order": [1, 2, 3],
            "data_type": "XXXX",
            "template": []})

        # Check that reading creates only one read file and it is left open
        file_factory = FakeFileFactory()
        self.assertEqual(len(file_factory.read_files), 0)
        self.assertEqual(len(file_factory.write_files), 0)
        si = SubImage(descriptor, file_factory)
        si.read_image([1, 1, 1], [1, 1, 1])
        self.assertEqual(len(file_factory.read_files), 1)
        self.assertTrue(file_factory.read_files[0].open)
        self.assertEqual(len(file_factory.write_files), 0)
        self.assertTrue(file_factory.read_files[0].open)
        si.read_image([1, 1, 1], [2, 2, 2])
        self.assertEqual(len(file_factory.read_files), 1)
        self.assertEqual(len(file_factory.write_files), 0)

        # Check that close() closes the read image
        self.assertTrue(file_factory.read_files[0].open)
        si.close()
        self.assertEqual(len(file_factory.read_files), 1)
        self.assertEqual(len(file_factory.write_files), 0)
        self.assertFalse(file_factory.read_files[0].open)

        # Check that file is closed after writing
        source = FakeImageFile([])
        self.assertEqual(len(file_factory.write_files), 0)
        si.write_image(source)
        self.assertEqual(len(file_factory.write_files), 1)
        self.assertFalse(file_factory.write_files[0].open)

    @parameterized.expand([
        param(dim_order=[1, 2, 3], ranges=[[0, 40, 0, 0], [0, 40, 0, 0], [0, 40, 0, 0]], start=[0, 0, 0], size=[10, 10, 10]),
        param(dim_order=[1, 2, 3], ranges=[[0, 40, 0, 0], [0, 40, 0, 0], [0, 40, 0, 0]], start=[0, 0, 0], size=[11, 11, 11]),
        param(dim_order=[1, 2, 3], ranges=[[0, 40, 0, 0], [0, 40, 0, 0], [0, 40, 0, 0]], start=[1, 2, 3], size=[20, 15, 15]),
        param(dim_order=[1, 2, 3], ranges=[[0, 40, 0, 0], [0, 40, 0, 0], [0, 40, 0, 0]], start=[5, 6, 7], size=[10, 10, 10]),
        param(dim_order=[1, 2, 3], ranges=[[0, 40, 0, 0], [0, 40, 0, 0], [0, 40, 0, 0]], start=[5, 6, 7], size=[10, 10, 10]),
        param(dim_order=[1, 2, 3], ranges=[[0, 40, 0, 0], [0, 40, 0, 0], [0, 40, 0, 0]], start=[15, 16, 17], size=[10, 10, 10]),
        param(dim_order=[2, 1, 3], ranges=[[0, 40, 0, 0], [0, 40, 0, 0], [0, 40, 0, 0]], start=[5, 6, 7], size=[10, 10, 10]),
        param(dim_order=[2, 3, 1], ranges=[[0, 40, 0, 0], [0, 40, 0, 0], [0, 40, 0, 0]], start=[5, 6, 7], size=[10, 10, 10]),
        param(dim_order=[3, 2, 1], ranges=[[0, 40, 0, 0], [0, 40, 0, 0], [0, 40, 0, 0]], start=[15, 16, 17], size=[10, 10, 10]),
        param(dim_order=[-2, 1, 3], ranges=[[0, 40, 0, 0], [0, 40, 0, 0], [0, 40, 0, 0]], start=[5, 6, 7], size=[10, 10, 10]),
        param(dim_order=[-2, 1], ranges=[[0, 40, 0, 0], [0, 40, 0, 0]], start=[5, 6], size=[10, 10]),
        param(dim_order=[-2, 1, 3, 4], ranges=[[0, 40, 0, 0], [0, 40, 0, 0], [0, 40, 0, 0], [0, 40, 0, 0]], start=[5, 6, 7, 8], size=[10, 10, 10, 10]),
        param(dim_order=[2, -3, 1], ranges=[[0, 40, 0, 0], [0, 40, 0, 0], [0, 40, 0, 0]], start=[5, 6, 7], size=[10, 10, 10]),
        param(dim_order=[3, 2, -1], ranges=[[0, 40, 0, 0], [0, 40, 0, 0], [0, 40, 0, 0]], start=[15, 16, 17], size=[10, 10, 10])
    ])
    def test_read_image(self, dim_order, ranges, start, size):
        descriptor = SubImageDescriptor({
            "filename": 'TestFileName', "suffix": "SUFFIX", "index": 0,
            "data_type": "XXXX", "template": [], "dim_order": dim_order,
            "ranges": ranges})

        read_file = Mock()
        global_image_size = len(dim_order)*[50]
        image = np.arange(0, np.prod(global_image_size)).reshape(global_image_size)
        image_wrapper = ImageWrapper(len(dim_order)*[0], image=image)
        sub_image = image_wrapper.get_sub_image(start, size)
        read_file.read_image.return_value = sub_image

        file_factory = Mock()
        file_factory.create_read_file.return_value = read_file

        si = SubImage(descriptor, file_factory)

        # CoordinateTransforer is tested elsewhere. Here we do not make sure
        # the coordinates have been transformed, using another
        # CoordinateTransformer to check, but we are not verifying the
        # transformations are correct, since the CoordinateTransformer test
        # should do this
        transformer = CoordinateTransformer(
            descriptor.origin_start, descriptor.image_size,
            descriptor.dim_order, descriptor.dim_flip)
        expected_start, expected_size = transformer.to_local(start, size)
        test_image = si.read_image(start, size)
        # ranges = (range(st, st+sz) for st, sz in zip(start, size))
        np.testing.assert_array_equal(test_image.image, sub_image)
        np.testing.assert_array_equal(read_file.read_image.call_args[0][0], expected_start)
        np.testing.assert_array_equal(read_file.read_image.call_args[0][1], expected_size)

    @parameterized.expand([
        param(dim_order=[1, 2, 3], ranges=[[0, 40, 0, 0], [0, 40, 0, 0], [0, 40, 0, 0]], start=[0, 0, 0], size=[10, 10, 10]),
        param(dim_order=[1, 2, 3], ranges=[[0, 40, 0, 0], [0, 40, 0, 0], [0, 40, 0, 0]], start=[0, 0, 0], size=[11, 11, 11]),
        param(dim_order=[1, 2, 3], ranges=[[0, 40, 0, 0], [0, 40, 0, 0], [0, 40, 0, 0]], start=[1, 2, 3], size=[20, 15, 15]),
        param(dim_order=[1, 2, 3], ranges=[[0, 40, 0, 0], [0, 40, 0, 0], [0, 40, 0, 0]], start=[5, 6, 7], size=[10, 10, 10]),
        param(dim_order=[1, 2, 3], ranges=[[0, 40, 0, 0], [0, 40, 0, 0], [0, 40, 0, 0]], start=[5, 6, 7], size=[10, 10, 10]),
        param(dim_order=[1, 2, 3], ranges=[[0, 40, 0, 0], [0, 40, 0, 0], [0, 40, 0, 0]], start=[15, 16, 17], size=[10, 10, 10]),
        param(dim_order=[2, 1, 3], ranges=[[0, 40, 0, 0], [0, 40, 0, 0], [0, 40, 0, 0]], start=[5, 6, 7], size=[10, 10, 10]),
        param(dim_order=[2, 3, 1], ranges=[[0, 40, 0, 0], [0, 40, 0, 0], [0, 40, 0, 0]], start=[5, 6, 7], size=[10, 10, 10]),
        param(dim_order=[3, 2, 1], ranges=[[0, 40, 0, 0], [0, 40, 0, 0], [0, 40, 0, 0]], start=[15, 16, 17], size=[10, 10, 10]),
        param(dim_order=[-2, 1, 3], ranges=[[0, 40, 0, 0], [0, 40, 0, 0], [0, 40, 0, 0]], start=[5, 6, 7], size=[10, 10, 10]),
        param(dim_order=[-2, 1], ranges=[[0, 40, 0, 0], [0, 40, 0, 0]], start=[5, 6], size=[10, 10]),
        param(dim_order=[-2, 1, 3, 4], ranges=[[0, 40, 0, 0], [0, 40, 0, 0], [0, 40, 0, 0], [0, 40, 0, 0]], start=[5, 6, 7, 8], size=[10, 10, 10, 10]),
        param(dim_order=[2, -3, 1], ranges=[[0, 40, 0, 0], [0, 40, 0, 0], [0, 40, 0, 0]], start=[5, 6, 7], size=[10, 10, 10]),
        param(dim_order=[3, 2, -1], ranges=[[0, 40, 0, 0], [0, 40, 0, 0], [0, 40, 0, 0]], start=[15, 16, 17], size=[10, 10, 10])
    ])
    def test_write_image(self, dim_order, ranges, start, size):
        descriptor = SubImageDescriptor({
            "filename": 'TestFileName', "suffix": "SUFFIX", "index": 0,
            "data_type": "XXXX", "template": [], "dim_order": dim_order,
            "ranges": ranges})

        file_factory = Mock()
        out_file = Mock()
        file_factory.create_write_file.return_value = out_file

        # This test verifies that the read source supplied to the output file
        # correctly converts from the file coordinate system to the global
        # coordinate system
        source = Mock()
        source.read_image.return_value = None  # Doesn't matter

        si = SubImage(descriptor, file_factory)
        si.write_image(source)

        # CoordinateTransforer is tested elsewhere.
        transformer = CoordinateTransformer(
            descriptor.origin_start, descriptor.image_size,
            descriptor.dim_order, descriptor.dim_flip)
        local_start, local_size = transformer.to_local(start, size)


        # Fetch the local data source provided to the file write method
        local_data_source = out_file.write_image.call_args[0][0]

        # Read from the local data source to trigger a read in the global source
        input_image = local_data_source.read_image(local_start, local_size)

        # Get the arguments
        test_start = source.read_image.call_args[0][0]
        test_size = source.read_image.call_args[0][1]

        np.testing.assert_array_equal(test_start, start)
        np.testing.assert_array_equal(test_size, size)

    @parameterized.expand([
        param(ranges=[[0, 10, 0, 0], [0, 10, 0, 0], [0, 10, 0, 0]], start=[0, 0, 0], size=[10, 10, 10], valid=True, valid_start=[0, 0, 0], valid_size=[10, 10, 10]),
        param(ranges=[[0, 10, 0, 0], [0, 10, 0, 0], [0, 10, 0, 0]], start=[0, 0, 0], size=[11, 11, 11], valid=True, valid_start=[0, 0, 0], valid_size=[11, 11, 11]),
        param(ranges=[[0, 10, 0, 0], [0, 10, 0, 0], [0, 10, 0, 0]], start=[-1, -2, -3], size=[20, 15, 15], valid=True, valid_start=[0, 0, 0], valid_size=[11, 11, 11]),
        param(ranges=[[0, 10, 0, 0], [0, 10, 0, 0], [0, 10, 0, 0]], start=[-5, -6, -7], size=[10, 10, 10], valid=True, valid_start=[0, 0, 0], valid_size=[5, 4, 3]),
        param(ranges=[[0, 10, 0, 0], [0, 10, 0, 0], [0, 10, 0, 0]], start=[5, 6, 7], size=[10, 10, 10], valid=True, valid_start=[5, 6, 7], valid_size=[6, 5, 4]),
        param(ranges=[[0, 10, 0, 0], [0, 10, 0, 0], [0, 10, 0, 0]], start=[15, 16, 17], size=[10, 10, 10], valid=False, valid_start=[5, 6, 7], valid_size=[0, 0, 0]),
        param(ranges=[[0, 10, 0, 0], [0, 10, 0, 0], [0, 10, 0, 0]], start=[-15, -16, -17], size=[10, 10, 10], valid=False, valid_start=[5, 6, 7], valid_size=[0, 0, 0]),
        param(ranges=[[0, 10, 0, 0], [0, 10, 0, 0], [0, 10, 0, 0], [0, 10, 0, 0]], start=[-15, -16, -17, -18], size=[10, 10, 10, 10], valid=False, valid_start=[5, 6, 7, 8], valid_size=[0, 0, 0, 0]),
        param(ranges=[[0, 10, 0, 0], [0, 10, 0, 0]], start=[-15, -16], size=[10, 10], valid=False, valid_start=[5, 6], valid_size=[0, 0])
    ])
    def test_bind_by_roi(self, ranges, start, size, valid, valid_start, valid_size):
        descriptor = SubImageDescriptor({
            "filename": 'TestFileName', "suffix": "SUFFIX", "index": 0,
            "data_type": "XXXX", "template": [], "dim_order": np.arange(1, len(start) + 1),
            "ranges": ranges})
        file_factory = FakeFileFactory()
        si = SubImage(descriptor, file_factory)
        start_test, size_test = si.bind_by_roi(start_global=start, size_global=size)

        if valid:
            # For values within bounds, check they are correct
            np.testing.assert_array_equal(size_test, valid_size)
            np.testing.assert_array_equal(start_test, valid_start)
        else:
            # For values out of bounds, the actual values are irrelevant but at least one of the size dimensions must be <= 0
            self.assertTrue(np.any(np.less(size_test, np.zeros_like(size_test))))
