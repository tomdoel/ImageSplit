ImageSplit
==========

.. image:: https://cmiclab.cs.ucl.ac.uk/GIFT-Surg/ImageSplit/raw/master/giftsurg-icon.png
   :height: 128px
   :width: 128px
   :target: https://cmiclab.cs.ucl.ac.uk/GIFT-Surg/ImageSplit


.. image:: https://cmiclab.cs.ucl.ac.uk/GIFT-Surg/ImageSplit/badges/master/build.svg
   :target: https://cmiclab.cs.ucl.ac.uk/GIFT-Surg/ImageSplit/commits/master

.. image:: https://cmiclab.cs.ucl.ac.uk/GIFT-Surg/ImageSplit/badges/master/coverage.svg
   :target: https://cmiclab.cs.ucl.ac.uk/GIFT-Surg/ImageSplit/commits/master


ImageSplit is a utility for splitting very large image volumes into slices or multiple overlapping sub-volumes, and for recombining sub-volumes into a one or more volumes. ImageSplit can also convert the underlying data types.

ImageSplit is designed to prioritise low memory usage over performance, so that large volumes can be easily processed with limited memory resources.

Author: Tom Doel

ImageSplit was developed as part of the `GIFT-Surg`_ project, at the `Translational Imaging Group (TIG)`_ in the `Centre for Medical Image Computing (CMIC)`_ at `University College London (UCL)`_.


Usage
~~~~~

::

    imagesplit.py [-h] -i INPUT [-o OUT] [-l OVERLAP] [-m MAX [MAX ...]] [-x STARTINDEX] [-t TYPE] [-f FORMAT] [-r [RESCALE [RESCALE ...]]] [-z [COMPRESS]] [-s SLICE] [-a AXIS [AXIS ...]] [--test]


Arguments:


Input and output filenames:

    -i INPUT, --input INPUT  Name of input file, or filename prefix for a set of files

    -o OUT, --out OUT        Name of output file, or filename prefix if more than one file is output

    -x STARTINDEX, --startindex STARTINDEX
                             Start index for filename suffix when loading or saving
                             a sequence of files


Specify how to split the image:

    -l OVERLAP, --overlap OVERLAP
                             Number of voxels to overlap between output images. If
                             not specified, output images will not overlap

    -m MAX [MAX ...], --max MAX [MAX ...]
                             Maximum number of voxels in each dimension in each
                             output file. Can be a scalar or vector corresponding
                             to each image dimension. The file will be optimally
                             split such that each file output dimension is less
                             than or equal to this maximum.


Specify file format, data type, and whether data should be rescaled (normalised):

    -t TYPE, --type TYPE  Output data type (default: same as input file datatype)

    -f FORMAT, --format FORMAT  Output file format such as mhd, tiff (default: same as input file format)

    -r [RESCALE [RESCALE ...]], --rescale [RESCALE [RESCALE ...]]
        Rescale image between the specified min and max
        values. If no values are specified, use the volume limits.

    -z [COMPRESS], --compress [COMPRESS]
        Enables compression (default no compression). Valid
        values depend on the output file format. -z with no
        extra argument will choose a suitable compression for
        this file format. For TIFF files, the default is Adboe
        deflat and other valid values are those supported by PIL.


Specify output orientation:

    -s SLICE, --slice SLICE
        Divide image into slices along the specified axis.
        Choose 1, 2, 3 etc to select an axis relative to the
        current image orientation, or c, s, a to select an
        absolute orientation.This argument cannot be used with --axis, --max or --overlap.

    -a AXIS [AXIS ...], --axis AXIS [AXIS ...]
        Axis ordering (default 1 2 3). Specifies the global
        axis corresponding to each dimension in the image
        file. The first value is the global axis represented
        by the first dimension in the file, and so on. One
        value for each dimension, dimensions are numbered
        1,2,3,... and a negative value means that axis is
        flipped. This cannot be used with --slice



Help and testing:

    --test      If set, No writing will be performed to the output files
    -h, --help  Show this help message and exit


Contributing
^^^^^^^^^^^^

Please see the `contributing guidelines`_.


Useful links
^^^^^^^^^^^^

`Source code repository`_


Licensing and copyright
-----------------------

Copyright 2017 University College London.
ImageSplit is released under the BSD-3 licence. Please see the `license file`_ for details.


Acknowledgements
----------------

Supported by `Wellcome`_ and `EPSRC`_.


.. _`Wellcome EPSRC Centre for Interventional and Surgical Sciences`: http://www.ucl.ac.uk/weiss
.. _`source code repository`: https://cmiclab.cs.ucl.ac.uk/GIFT-Surg/ImageSplit
.. _`University College London (UCL)`: http://www.ucl.ac.uk/
.. _`Translational Imaging Group (TIG)`: http://cmictig.cs.ucl.ac.uk/
.. _`Centre for Medical Image Computing (CMIC)`: http://cmic.cs.ucl.ac.uk
.. _`Wellcome`: https://wellcome.ac.uk/
.. _`GIFT-Surg`: https://www.gift-surg.ac.uk
.. _`EPSRC`: https://www.epsrc.ac.uk/
.. _`contributing guidelines`: https://cmiclab.cs.ucl.ac.uk/GIFT-Surg/ImageSplit/blob/master/CONTRIBUTING.rst
.. _`license file`: https://cmiclab.cs.ucl.ac.uk/GIFT-Surg/ImageSplit/blob/master/LICENSE


.. toctree::
   :maxdepth: 4
   :caption: Contents:
















