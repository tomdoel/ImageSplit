from unittest import TestCase

import numpy as np
from mock import Mock
from parameterized import parameterized, param

from tests.common_test_functions import FakeImageFileReader, create_dummy_image
from niftysplit.image.combined_image import SubImage, CoordinateTransformer, \
    CombinedImage, LocalSource, Axis
from niftysplit.utils.file_descriptor import SubImageDescriptor


class FakeFileFactory(object):
    """Create objects for handling file input and output"""

    def __init__(self, image=None):
        self.image = image
        self.read_files = []
        self.write_files = []

    def create_read_file(self, descriptor):
        """Create a class for reading"""

        read_file = FakeImageFileReader(descriptor, self.image)
        self.read_files.append(read_file)
        return read_file

    def create_write_file(self, descriptor):
        """Create a class for writing"""

        write_file = FakeImageFileReader(descriptor)
        self.write_files.append(write_file)
        return write_file


class TestCombinedImage(TestCase):

    def test_combined_image(self):
        d1 = self._make_descriptor( 1,  [[ 0, 11, 0, 2], [ 0, 11, 0, 2], [ 0, 11, 0, 2]])
        d2 = self._make_descriptor( 2,  [[ 0, 11, 0, 2], [ 0, 11, 0, 2], [ 8, 21, 2, 2]])
        d3 = self._make_descriptor( 3,  [[ 0, 11, 0, 2], [ 0, 11, 0, 2], [18, 29, 2, 0]])
        d4 = self._make_descriptor( 4,  [[ 0, 11, 0, 2], [ 8, 21, 2, 2], [ 0, 11, 0, 2]])
        d5 = self._make_descriptor( 5,  [[ 0, 11, 0, 2], [ 8, 21, 2, 2], [ 8, 21, 2, 2]])
        d6 = self._make_descriptor( 6,  [[ 0, 11, 0, 2], [ 8, 21, 2, 2], [18, 29, 2, 0]])
        d7 = self._make_descriptor( 7,  [[ 0, 11, 0, 2], [18, 29, 2, 0], [ 0, 11, 0, 2]])
        d8 = self._make_descriptor( 8,  [[ 0, 11, 0, 2], [18, 29, 2, 0], [ 8, 21, 2, 2]])
        d9 = self._make_descriptor( 9,  [[ 0, 11, 0, 2], [18, 29, 2, 0], [18, 29, 2, 0]])

        d11 = self._make_descriptor(11, [[ 8, 21, 2, 2], [ 0, 11, 0, 2], [ 0, 11, 0, 2]])
        d12 = self._make_descriptor(12, [[ 8, 21, 2, 2], [ 0, 11, 0, 2], [ 8, 21, 2, 2]])
        d13 = self._make_descriptor(13, [[ 8, 21, 2, 2], [ 0, 11, 0, 2], [18, 29, 2, 0]])
        d14 = self._make_descriptor(14, [[ 8, 21, 2, 2], [ 8, 21, 2, 2], [ 0, 11, 0, 2]])
        d15 = self._make_descriptor(15, [[ 8, 21, 2, 2], [ 8, 21, 2, 2], [ 8, 21, 2, 2]])
        d16 = self._make_descriptor(16, [[ 8, 21, 2, 2], [ 8, 21, 2, 2], [18, 29, 2, 0]])
        d17 = self._make_descriptor(17, [[ 8, 21, 2, 2], [18, 29, 2, 0], [ 0, 11, 0, 2]])
        d18 = self._make_descriptor(18, [[ 8, 21, 2, 2], [18, 29, 2, 0], [ 8, 21, 2, 2]])
        d19 = self._make_descriptor(19, [[ 8, 21, 2, 2], [18, 29, 2, 0], [18, 29, 2, 0]])

        d21 = self._make_descriptor(21, [[18, 29, 2, 0], [ 0, 11, 0, 2], [ 0, 11, 0, 2]])
        d22 = self._make_descriptor(22, [[18, 29, 2, 0], [ 0, 11, 0, 2], [ 8, 21, 2, 2]])
        d23 = self._make_descriptor(23, [[18, 29, 2, 0], [ 0, 11, 0, 2], [18, 29, 2, 0]])
        d24 = self._make_descriptor(24, [[18, 29, 2, 0], [ 8, 21, 2, 2], [ 0, 11, 0, 2]])
        d25 = self._make_descriptor(25, [[18, 29, 2, 0], [ 8, 21, 2, 2], [ 8, 21, 2, 2]])
        d26 = self._make_descriptor(26, [[18, 29, 2, 0], [ 8, 21, 2, 2], [18, 29, 2, 0]])
        d27 = self._make_descriptor(27, [[18, 29, 2, 0], [18, 29, 2, 0], [ 0, 11, 0, 2]])
        d28 = self._make_descriptor(28, [[18, 29, 2, 0], [18, 29, 2, 0], [ 8, 21, 2, 2]])
        d29 = self._make_descriptor(29, [[18, 29, 2, 0], [18, 29, 2, 0], [18, 29, 2, 0]])

        descriptors = [d1, d2, d3, d4, d5, d6, d7, d8, d9,
                       d11, d12, d13, d14, d15, d16, d17, d18, d19,
                       d21, d22, d23, d24, d25, d26, d27, d28, d29]

        image = create_dummy_image([30, 30, 30])
        file_factory = FakeFileFactory(image=image)

        ci = CombinedImage(descriptors, file_factory)
        source = Mock()
        self.assertEqual(len(file_factory.write_files), 0)
        ci.write_image(source)
        self.assertEqual(len(file_factory.write_files), 27)
        for descriptor, write_file in zip(descriptors, file_factory.write_files):
            self.assertEqual(descriptor.ranges.ranges, write_file.descriptor.ranges.ranges)
            self.assertFalse(write_file.open)

        self.assertEqual(len(file_factory.read_files), 0)

        # Test reading and assembling the whole image
        read_image = ci.read_image([0, 0, 0], [30, 30, 30], global_coordinate_transformer([30, 30, 30]))
        np.testing.assert_array_equal(image.image, read_image.image)

        # Test reading part of the image excluding some of the subimages
        read_image = ci.read_image([0, 0, 0], [5, 5, 5], global_coordinate_transformer([30, 30, 30]))
        np.testing.assert_array_equal(image.get_sub_image([0, 0, 0], [5, 5, 5]).image, read_image.image)

        # Test file closing
        self.assertEqual(len(file_factory.read_files), 27)
        for read_file in file_factory.read_files:
            self.assertTrue(read_file.open)
        ci.close()
        for read_file in file_factory.read_files:
            self.assertFalse(read_file.open)

    def _make_descriptor(self, index, ranges):
        return SubImageDescriptor.from_dict({"filename": 'TestFileName',
            "ranges": ranges, "suffix": "SUFFIX", "dim_order": [1, 2, 3],
            "data_type": "XXXX", "index": index, "template": []})


def global_coordinate_transformer(size):
    return CoordinateTransformer(np.zeros_like(size), size, Axis(np.arange(0, len(size)), np.zeros_like(size)))


class TestSubImage(TestCase):

    def test_close(self):
        descriptor = SubImageDescriptor.from_dict({
            "filename": 'TestFileName',
            "ranges": [[0, 10, 0, 0], [0, 10, 0, 0], [0, 10, 0, 0]],
            "suffix": "SUFFIX",
            "index": 0,
            "dim_order": [1, 2, 3],
            "data_type": "XXXX",
            "template": []})

        # Check that reading creates only one read file and it is left open
        file_factory = FakeFileFactory(create_dummy_image([11, 11, 11]))
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
        source = FakeImageFileReader(descriptor)
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
        descriptor = SubImageDescriptor.from_dict({
            "filename": 'TestFileName', "suffix": "SUFFIX", "index": 0,
            "data_type": "XXXX", "template": [], "dim_order": dim_order,
            "ranges": ranges})

        read_file = Mock()
        global_image_size = len(dim_order)*[50]
        image = create_dummy_image(global_image_size)
        image_wrapper = image
        sub_image = image_wrapper.get_sub_image(start, size)
        read_file.read_image.return_value = sub_image.image

        file_factory = Mock()
        file_factory.create_read_file.return_value = read_file

        si = SubImage(descriptor, file_factory)

        # CoordinateTransforer is tested elsewhere. Here we do not make sure
        # the coordinates have been transformed, using another
        # CoordinateTransformer to check, but we are not verifying the
        # transformations are correct, since the CoordinateTransformer test
        # should do this
        transformer = CoordinateTransformer(
            descriptor.ranges.origin_start, descriptor.ranges.image_size,
            descriptor.axis)
        expected_start, expected_size = transformer.to_local(start, size)
        test_image = si.read_image(start, size)
        np.testing.assert_array_equal(test_image.image, sub_image.image)
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
        descriptor = SubImageDescriptor.from_dict({
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
        dummy_image = create_dummy_image(len(size)*[20])
        source.read_image.return_value = dummy_image

        si = SubImage(descriptor, file_factory)
        si.write_image(source)

        # CoordinateTransforer is tested elsewhere.
        transformer = CoordinateTransformer(
            descriptor.ranges.origin_start, descriptor.ranges.image_size,
            descriptor.axis)
        local_start, local_size = transformer.to_local(start, size)

        # Fetch the local data source provided to the file write method
        local_data_source = out_file.write_image.call_args[0][0]

        # Read from the local data source to trigger a read in the global source
        input_image = local_data_source.read_image(local_start, local_size)

        # Get the arguments
        test_start = source.read_image.call_args[0][0]
        test_size = source.read_image.call_args[0][1]

        np.testing.assert_array_equal(test_start, local_start)
        np.testing.assert_array_equal(test_size, local_size)

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
        descriptor = SubImageDescriptor.from_dict({
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


# class TestGlobalSource(TestCase):
#     @parameterized.expand([
#         param(origin=[0, 0, 0], global_size=[50, 50, 50], dim_order=[0, 1, 2], dim_flip=[0, 0, 0], start=[0, 0, 0], size=[10, 10, 10]),
#         param(origin=[1, 2, 3], global_size=[50, 60, 70], dim_order=[0, 2, 1], dim_flip=[0, 1, 1], start=[1, 0, 8], size=[10, 11, 13]),
#         param(origin=[1, 0, 0], global_size=[50, 50, 50], dim_order=[0, 1, 2], dim_flip=[0, 0, 0], start=[50, 0, 0], size=[10, 17, 30]),
#         param(origin=[0, 20, 0], global_size=[50, 50, 50], dim_order=[0, 1, 2], dim_flip=[0, 0, 0], start=[0, 0, 0], size=[10, 10, 10]),
#         param(origin=[5], global_size=[50], dim_order=[0], dim_flip=[1], start=[11], size=[11]),
#         param(origin=[2, 1], global_size=[30, 40], dim_order=[1, 0], dim_flip=[1, 0], start=[5, 8], size=[10, 11]),
#         param(origin=[1, 2, 3, 4], global_size=[50, 60, 70, 80], dim_order=[0, 2, 1, 3], dim_flip=[0, 1, 0, 1], start=[2, 4, 6, 8], size=[10, 11, 12,13])
#     ])
#     def test_global_source(self, origin, global_size, dim_order, dim_flip, start, size):
#         transformer = CoordinateTransformer(origin, global_size, Axis(dim_order, dim_flip))
#         data_source = Mock()
#         test_image = create_dummy_image(global_size).image.copy()
#         data_source.read_image.return_value = test_image
#         source = GlobalSource(data_source, transformer)
#         global_image = source.read_image(start, size)
#         local_start, local_size = transformer.to_local(start, size)
#         np.testing.assert_array_equal(data_source.read_image.call_args[0][0], local_start)
#         np.testing.assert_array_equal(data_source.read_image.call_args[0][1], local_size)
#
#         self.assertEqual(data_source.close.call_count, 0)
#         source.close()
#         self.assertEqual(data_source.close.call_count, 1)
#
#         local_image = transformer.image_to_local(global_image)
#         np.testing.assert_array_equal(local_image, test_image)


class TestLocalSource(TestCase):
    @parameterized.expand([
        param(origin=[0, 0, 0], global_size=[50, 50, 50], dim_order=[0, 1, 2], dim_flip=[0, 0, 0], start=[0, 0, 0], size=[10, 10, 10]),
        param(origin=[1, 2, 3], global_size=[50, 60, 70], dim_order=[0, 2, 1], dim_flip=[0, 1, 1], start=[1, 0, 8], size=[10, 11, 13]),
        param(origin=[1, 0, 0], global_size=[50, 50, 50], dim_order=[0, 1, 2], dim_flip=[0, 0, 0], start=[50, 0, 0], size=[10, 17, 30]),
        param(origin=[0, 20, 0], global_size=[50, 50, 50], dim_order=[0, 1, 2], dim_flip=[0, 0, 0], start=[0, 0, 0], size=[10, 10, 10]),
        param(origin=[5], global_size=[50], dim_order=[0], dim_flip=[1], start=[11], size=[11]),
        param(origin=[2, 1], global_size=[30, 40], dim_order=[1, 0], dim_flip=[1, 0], start=[5, 8], size=[10, 11]),
        param(origin=[1, 2, 3, 4], global_size=[50, 60, 70, 80], dim_order=[0, 2, 1, 3], dim_flip=[0, 1, 0, 1], start=[2, 4, 6, 8], size=[10, 11, 12, 13])
    ])
    def test_local_source(self, origin, global_size, dim_order, dim_flip, start, size):
        transformer = CoordinateTransformer(origin, global_size, Axis(dim_order, dim_flip))
        data_source = Mock()
        test_image = create_dummy_image(global_size)
        data_source.read_image.return_value = test_image
        source = LocalSource(data_source, transformer)
        local_image = source.read_image(start, size)
        global_start, t_global_size = transformer.to_global(start, size)
        np.testing.assert_array_equal(data_source.read_image.call_args[0][0],
                                      start)
        np.testing.assert_array_equal(data_source.read_image.call_args[0][1],
                                      size)

        self.assertEqual(data_source.close.call_count, 0)
        source.close()
        self.assertEqual(data_source.close.call_count, 1)

        global_image = transformer.image_to_global(local_image)
        np.testing.assert_array_equal(local_image, test_image.image)
