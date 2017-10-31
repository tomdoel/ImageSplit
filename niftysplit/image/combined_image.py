import numpy as np

from image.image_wrapper import ImageWrapper


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


class SubImage(object):
    """An image which forms part of a larger image"""

    def __init__(self, descriptor, file_factory):
        self._file_factory = file_factory
        self._descriptor = descriptor
        self._read_source = None

        # Construct the origin offset used to convert from global
        # coordinates. This excludes overlapping voxels
        self._image_size = self._descriptor.image_size
        self._origin_start = self._descriptor.origin_start
        self._origin_end = self._descriptor.origin_end
        self._roi_start = self._descriptor.roi_start
        self._dim_order = self._descriptor.dim_order
        self._dim_flip = self._descriptor.dim_flip
        self._roi_end = self._descriptor.roi_end
        self._roi_size = np.add(np.subtract(self._roi_end, self._roi_end),
                                np.ones(shape=self._roi_start))
        self._ranges = self._descriptor.ranges
        self._transformer = CoordinateTransformer(self._origin_start,
                                                  self._image_size,
                                                  self._dim_order,
                                                  self._dim_flip)

    def read_part_image(self, start_global, size):
        """Returns a subimage containing any overlap from the ROI"""

        # Find the part of the requested region that fits in the ROI
        start, end, size = self._get_bounds_in_roi(start_global, size)

        # Check if none of the requested region is contained in this subimage
        if np.any(np.less(size, np.zeros(shape=size))):
            return None

        image_data = self._get_read_source().read_image(start, size)

        # Wrap the image data in an ImageWrapper
        return ImageWrapper(start, image=image_data)

    def write_subimage(self, source):
        """Write out SubImage using data from the specified source"""
        file = self._file_factory.create_write_file(self._descriptor)
        transformed_source = TransformedDataSource(source, self._transformer)
        file.write_file(transformed_source)
        file.close()

    def close(self):
        """Close all streams and files"""
        self._read_source.close()
        self._read_source = None

    def _get_bounds_in_roi(self, start_global, size_global):
        start = np.maximum(start_global, self._roi_start)
        end = np.minimum(np.add(start_global, size_global),
                         np.add(self._roi_start, self._roi_size))
        size = np.subtract(end, start)
        return start, end, size

    def _get_read_source(self):
        if not self._read_source:
            source = self._file_factory.create_read_file(self._descriptor)
            self._read_source = TransformedDataSource(source, self._transformer)
        return self._read_source


class TransformedDataSource(object):
    """Data source with conversion between local and global coordinates"""

    def __init__(self, data_source, converter):
        self._data_source = data_source
        self._converter = converter

    def read_image(self, start_local, size_local):
        """Returns a partial image using the specified local coordinates"""

        start, size = self._converter.to_global(start_local, size_local)
        return self._data_source.read_image(start, size)

    def read_image_local(self, start_global, size_global):
        """Returns a partial image using the specified global coordinates"""

        # Convert to local coordinates for the data source
        start, size = self._converter.to_local(start_global, size_global)

        # Get the image data from the data source
        return self._data_source.read_image(start, size)


class CoordinateTransformer(object):
    """Convert coordinates between orthogonal systems"""

    def __init__(self, origin, size, dim_ordering, dim_flip):
        """Create a transformer object for converting between systems

        :param origin: local coordinate origin in global coordinates
        :param dim_ordering: ordering of local dimensions
        :param dim_flip: whether local axes should be flipped
        """
        self._origin = origin
        self._size = size
        self._dim_ordering = dim_ordering
        self._dim_flip = dim_flip

    def to_local(self, global_start, global_size):
        """Convert global coordinates to local coordinates"""

        # Translate coordinates to the local origin
        start = np.subtract(global_start, self._origin)

        # Permute dimensions of local coordinates
        start = np.transpose(start, self._dim_ordering)
        size = np.transpose(global_size, self._dim_ordering)

        # Flip dimensions where necessary
        for index, flip in enumerate(self._dim_flip):
            if flip:
                start[index] = size[index] - start[index] - 1

        return start, size

    def to_global(self, local_start, local_size):
        """Convert local coordinates to global coordinates"""

        # Translate coordinates to the local origin
        start = np.add(local_start, self._origin)
        size = local_size

        # Flip dimensions where necessary
        for index, flip in enumerate(self._dim_flip):
            if flip:
                start[index] = size[index] - start[index] - 1

        # Reverse permute dimensions of local coordinates
        start = np.transpose(start, np.argsort(self._dim_ordering))
        size = np.transpose(size, np.argsort(self._dim_ordering))

        return start, size
