# -*- coding: utf-8 -*-
import math
import os
import struct
import unittest

import numpy
import numpy as np
from parameterized import parameterized
from pyfakefs import fake_filesystem_unittest

from niftysplit.file import file_wrapper
from niftysplit.file.file_wrapper import FileStreamer


class FakeFileHandleFactory(object):
    def __init__(self, fake_file):
        self._fake_file = fake_file

    def create_file_handle(self, filename, mode):
        self._fake_file.initialise(filename, mode)
        return self._fake_file


class FakeFile(object):
    def __init__(self, data, bytes_per_voxel):
        self.data = data
        self.bytes_per_voxel = bytes_per_voxel
        self.data_pointer = 0
        self.closed = True
        self.filename = None
        self.mode = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, value, traceback):
        pass

    def seek(self, num_bytes):
        self.data_pointer = math.floor(num_bytes / self.bytes_per_voxel)

    def read(self, num_bytes):
        return self.data[slice(self.data_pointer, self.data_pointer + int(
            math.floor(num_bytes / self.bytes_per_voxel)))]

    def write(self, bytes_to_write):
        num_voxels = int(math.floor(len(bytes_to_write) / self.bytes_per_voxel))
        for index in range(0, num_voxels):
            self.data[self.data_pointer + index] = bytes_to_write[
                index * self.bytes_per_voxel]
        return len(bytes_to_write)

    def initialise(self, filename, mode):
        if not self.closed:
            raise ValueError('File is already open')
        self.filename = filename
        self.mode = mode
        self.open()

    def open(self):
        if not self.closed:
            raise ValueError('File is already open')
        self.closed = False

    def close(self):
        if self.closed:
            raise ValueError('File is already closed')

        self.closed = True

    def flush(self):
        pass


class TestFileWrapper(fake_filesystem_unittest.TestCase):
    """Tests for FileWrapper"""

    def setUp(self):
        self.setUpPyfakefs()

    def tearDown(self):
        pass

    # noinspection PyUnusedLocal
    @parameterized.expand([
        [[2, 3, 8], 4, [1, 2, 3], 2],
        [[101, 222, 4], 4, [1, 1, 1], 10],
        [[154, 141, 183], 4, [13, 12, 11], 30],
    ])
    def test_get_handle(self, image_size, bytes_per_voxel, start_coords,
                        num_voxels_to_read):
        fake_file = FakeFile(
            range(0, image_size[0] * image_size[1] * image_size[2] - 1),
            bytes_per_voxel)
        fake_file_handle_factory = FakeFileHandleFactory(fake_file)
        wrapper = file_wrapper.FileWrapper("abc", fake_file_handle_factory, 'rb')
        self.assertEqual(fake_file.closed, True)
        self.assertEqual(wrapper.get_handle(), fake_file)
        self.assertEqual(fake_file.filename, "abc")
        self.assertEqual(fake_file.mode, "rb")
        self.assertEqual(fake_file.closed, False)

    # noinspection PyUnusedLocal
    @parameterized.expand([
        [[2, 3, 8], 4, [1, 2, 3], 2],
        [[101, 222, 4], 4, [1, 1, 1], 10],
        [[154, 141, 183], 4, [13, 12, 11], 30],
    ])
    def test_open_with(self, image_size, bytes_per_voxel, start_coords,
                       num_voxels_to_read):
        fake_file = FakeFile(
            range(0, image_size[0] * image_size[1] * image_size[2] - 1),
            bytes_per_voxel)
        fake_file_handle_factory = FakeFileHandleFactory(fake_file)
        self.assertEqual(fake_file.closed, True)
        with file_wrapper.FileWrapper("abc", fake_file_handle_factory,
                                      'rb') as wrapper:
            self.assertEqual(fake_file.closed, False)
        self.assertEqual(fake_file.closed, True)

    # noinspection PyUnusedLocal
    @parameterized.expand([
        [[2, 3, 8], 4, [1, 2, 3], 2],
        [[101, 222, 4], 4, [1, 1, 1], 10],
        [[154, 141, 183], 4, [13, 12, 11], 30],
    ])
    def test_open_close(self, image_size, bytes_per_voxel, start_coords,
                        num_voxels_to_read):
        fake_file = FakeFile(
            range(0, image_size[0] * image_size[1] * image_size[2] - 1),
            bytes_per_voxel)
        fake_handle_factory = FakeFileHandleFactory(fake_file)
        wrapper = file_wrapper.FileWrapper("abc", fake_handle_factory, 'rb')
        self.assertEqual(fake_file.closed, True)
        wrapper.open()
        self.assertEqual(fake_file.filename, "abc")
        self.assertEqual(fake_file.mode, "rb")
        self.assertEqual(fake_file.closed, False)
        wrapper.close()
        self.assertEqual(fake_file.closed, True)


class TestStreamer(fake_filesystem_unittest.TestCase):
    """Tests for FileStreamer"""

    def setUp(self):
        self.setUpPyfakefs()

    def tearDown(self):
        pass

    @parameterized.expand([
        [[2, 3, 8], 4, True, [1, 2, 3], 2],
        [[101, 222, 4], 4, True, [1, 1, 1], 10],
        [[154, 141, 183], 4, True, [13, 12, 11], 30],
        [[2, 3, 8], 4, False, [1, 2, 3], 2],
        [[101, 222, 4], 4, False, [1, 1, 1], 10],
        [[154, 141, 183], 4, False, [13, 12, 11], 30],
        [[16, 16, 256], 1, False, [1, 2, 3], 2],
        [[16, 17, 256], 2, False, [1, 2, 3], 2],
        [[16, 17, 256], 4, False, [1, 2, 3], 2],
        [[16, 17, 256], 8, False, [1, 2, 3], 2],
    ])
    def test_read_image_stream(self, image_size, bytes_per_voxel, is_signed,
                               start_coords, num_voxels_to_read):

        # Create a fake file of random data within the full range of this
        # datatype
        base_data_numpy = TestStreamer.generate_array(
            image_size[0] * image_size[1] * image_size[2],
            bytes_per_voxel, is_signed)

        TestStreamer.write_to_fake_file(
            '/test/test_read_image_stream.bin', base_data_numpy,
            bytes_per_voxel,
            is_signed)
        file_handle_factory = file_wrapper.FileHandleFactory()
        wrapper = file_wrapper.FileWrapper(
            '/test/test_read_image_stream.bin', file_handle_factory, 'rb')
        file_streamer = FileStreamer(wrapper, image_size, bytes_per_voxel,
                                     TestStreamer.get_np_type(
                                             bytes_per_voxel, is_signed), [1, 2, 3])
        start = start_coords[0] + start_coords[1] * image_size[0] + \
            start_coords[2] * image_size[0] * image_size[1]
        end = start + num_voxels_to_read
        expected = base_data_numpy[start:end]
        read_file_contents = file_streamer.read_line(start_coords,
                                                     num_voxels_to_read)
        expected = np.asarray(expected, dtype=TestStreamer.get_np_type(
            bytes_per_voxel, is_signed))
        self.assertTrue(np.array_equal(expected, read_file_contents))

    @parameterized.expand([
        [[2, 3, 8], 4, True, [1, 2, 3], 2],
        [[101, 222, 4], 4, True, [1, 1, 1], 10],
        [[154, 141, 183], 4, True, [13, 12, 11], 30],
    ])
    def test_write_image_stream(self, image_size, bytes_per_voxel, is_signed,
                                start_coords, num_voxels_to_write):
        file_handle_factory = file_wrapper.FileHandleFactory()

        wrapper = file_wrapper.FileWrapper(
            '/test/test_write_image_stream.bin', file_handle_factory, 'wb')
        file_streamer = FileStreamer(wrapper, image_size, bytes_per_voxel,
                                     TestStreamer.get_np_type(
                                             bytes_per_voxel, is_signed), [1, 2, 3])
        start = start_coords[0] + start_coords[1] * image_size[0] + \
            start_coords[2] * image_size[0] * image_size[1]

        # end = start + num_voxels_to_write
        to_write_voxels = [0] * num_voxels_to_write
        for index in range(0, num_voxels_to_write):
            to_write_voxels[index] = index + 12

        base_data_numpy = TestStreamer.generate_array(
            image_size[0] * image_size[1] * image_size[2],
            bytes_per_voxel, is_signed)
        expected = base_data_numpy.copy()
        to_write_numpy = np.asarray(to_write_voxels,
                                    dtype=TestStreamer.get_np_type(
                                        bytes_per_voxel, is_signed))
        file_streamer.write_line([0, 0, 0], base_data_numpy)
        file_streamer.write_line(start_coords, to_write_numpy)
        file_streamer.close()
        read_file_contents = TestStreamer.read_from_fake_file(
            '/test/test_write_image_stream.bin',
            bytes_per_voxel, is_signed)
        for index in range(0, num_voxels_to_write):
            expected[index + start] = to_write_voxels[index]

        expected = np.asarray(expected, dtype=TestStreamer.get_np_type(
            bytes_per_voxel, is_signed))
        self.assertTrue(np.array_equal(expected, read_file_contents))

    @staticmethod
    def read_from_fake_file(file_name, bytes_per_voxel, is_signed):
        fmt = TestStreamer.get_fmt_string(bytes_per_voxel, is_signed)
        with open(file_name, 'rb') as f:
            size_bytes = os.fstat(f.fileno()).st_size
            num_elements = int(round(size_bytes / bytes_per_voxel))
            read_list = struct.unpack(fmt * num_elements, f.read())
            return read_list

    @staticmethod
    def generate_array(length, bytes_per_voxels, is_signed):
        min_value = 0
        max_value = 2 ** bytes_per_voxels + 1
        if is_signed:
            offset = round(max_value / 2) + 1
        else:
            offset = 0
        dt = TestStreamer.get_np_type(bytes_per_voxel=bytes_per_voxels,
                                      is_signed=is_signed)
        max_value -= offset
        return numpy.random.randint(low=min_value, high=max_value, size=length,
                                    dtype=dt)

    @staticmethod
    def get_fmt_string(bytes_per_voxel, is_signed):
        if is_signed:
            if bytes_per_voxel == 1:
                return 'b'
            elif bytes_per_voxel == 2:
                return 'h'
            elif bytes_per_voxel == 4:
                return 'i'
            elif bytes_per_voxel == 8:
                return 'q'
        else:
            if bytes_per_voxel == 1:
                return 'B'
            elif bytes_per_voxel == 2:
                return 'H'
            elif bytes_per_voxel == 4:
                return 'I'
            elif bytes_per_voxel == 8:
                return 'Q'
        return None

    @staticmethod
    def get_np_type(bytes_per_voxel, is_signed):
        if is_signed:
            if bytes_per_voxel == 1:
                return np.int8
            elif bytes_per_voxel == 2:
                return np.int16
            elif bytes_per_voxel == 4:
                return np.int32
            elif bytes_per_voxel == 8:
                return np.int64
        else:
            if bytes_per_voxel == 1:
                return np.uint8
            elif bytes_per_voxel == 2:
                return np.uint16
            elif bytes_per_voxel == 4:
                return np.uint32
            elif bytes_per_voxel == 8:
                return np.uint64
        return None

    @staticmethod
    def write_to_fake_file(file_name, array_to_write, bytes_per_voxel,
                           is_signed):

        fmt = TestStreamer.get_fmt_string(bytes_per_voxel, is_signed)
        folder = os.path.dirname(file_name)
        if not os.path.exists(folder):
            os.makedirs(folder)
        with open(file_name, 'wb') as f:
            num_elements = len(array_to_write)
            to_write_bytes = struct.pack(fmt * num_elements, *array_to_write)
            f.write(to_write_bytes)
