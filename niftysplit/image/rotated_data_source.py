# coding=utf-8

import numpy as np


class RotatedDataSource(object):
    """Rotates and flips global coordinates to match a data source"""

    def __init__(self, data_source):
        self._data_source = data_source


        # dim_order = data_source.get_dim_order()
        # self._file_image_size = data_source.get_file_image_size()
        #
        # # Comvenience arrays for reordering dimensions
        # self._dim_index = [abs(d) - 1 for d in dim_order]
        # self._dim_flip = [1 if d < 0 else 0 for d in dim_order]

    def write_line(self, start_coords, image_line, direction):
        """Writes a line of image data to a binary file at the specified
        image location """

        file_coords, direction = self._to_file_coords(start_coords)
        self._data_source.write_line(file_coords, image_line, direction)

    def _to_file_coords(self, image_coords, direction):
        # Flip coordinates if writing the voxels in reverse
        flipped_coords = [x + flip * (1 + length - 2 * x) for
                          x, flip, length in
                          zip(image_coords, self._dim_flip,
                              self._image_size)]

        # Reorder dimensions
        file_coords = [flipped_coords[self._dim_index[x]] for x in
                       [0, 1, 2]]

        # Reorder direction
        direction = 1 + self._dim_index.index(abs(direction) - 1)

        # Flip direction
        if self._dim_flip[abs(direction) - 1]:
            direction = - direction

        return file_coords, direction
