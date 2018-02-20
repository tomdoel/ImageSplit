ImageSplit
==========

.. image:: https://cmiclab.cs.ucl.ac.uk/GIFT-Surg/ImageSplit/raw/master/giftsurg-icon.png
    :height: 128px
    :width: 128px
    :target: https://cmiclab.cs.ucl.ac.uk/GIFT-Surg/ImageSplit


.. image:: https://cmiclab.cs.ucl.ac.uk/GIFT-Surg/ImageSplit/badges/master/build.svg
    :target: https://cmiclab.cs.ucl.ac.uk/GIFT-Surg/ImageSplit/commits/master
    :alt: GitLab-CI test status

.. image:: https://travis-ci.org/gift-surg/ImageSplit.svg?branch=master
    :target: https://travis-ci.org/gift-surg/ImageSplit
    :alt: Travis test status

.. image:: https://cmiclab.cs.ucl.ac.uk/GIFT-Surg/ImageSplit/badges/master/coverage.svg
    :target: https://cmiclab.cs.ucl.ac.uk/GIFT-Surg/ImageSplit/commits/master
    :alt: Test coverage

.. image:: https://readthedocs.org/projects/imagesplit/badge/?version=latest
    :target: http://imagesplit.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

ImageSplit is a utility for splitting very large image volumes into slices or multiple overlapping sub-volumes, and for recombining sub-volumes into a one or more volumes. ImageSplit can also convert the underlying data types.

ImageSplit is designed to prioritise low memory usage over performance, so that large volumes can be easily processed with limited memory resources.

Author: Tom Doel

ImageSplit was developed as part of the `GIFT-Surg`_ project, at the `Translational Imaging Group (TIG)`_ in the `Centre for Medical Image Computing (CMIC)`_ at `University College London (UCL)`_.


Installing
~~~~~~~~~~

::

    pip install imagesplit

Notes:
    * We recommend you use pip to install ImageSplit.
    * Ensure you have Python 2.7 or 3.5 or later installed
    * (especially for macOS users): we suggest you do not modify the system installation of Python 2.7. Instead install a separate version of Python for development purposes (for example, using Homebrew), or use `virtualenv` to create a python virtual environment which you can safely modify without affecting the system installation.
    * If you have Python 2 and Python 3 insatlled, `pip2` may map to Python 2 and `pip3` may map to Python 3. This will depend on your installation
    * If you get permission errors when using `pip`, you may be trying to modify the system Python installation. This is not recommended. Instead install a local version of Python for development, or use a virtual environment (`virtualenv`).


Example usage
~~~~~~~~~~~~~

Please see detailed usage below.

Here is an example:

::

    imagesplit --input input_data/image.vge --out output_data/split_image -s c --format tiff -z --rescale -50 350 --type uchar



This command will:
    * split the volume file with header `input_data/image.vge`
    * into coronal slices (`-s c`)
    * saving them in the `output_data` folder with the filenames `split_image_0000.tiff`, `split_image_0001.tiff` etc
    * The file format is tiff (`--format tiff`)
    * with default compression (`-z`)
    * and data type unsigned char (`--type uchar`)
    * The data will be normalised (rescaled) between minimum and maximum values `-50` and `350` (`--rescale -50 350`)



Detailed Usage
~~~~~~~~~~~~~~

::

    imagesplit.py [-h] -i INPUT [-o OUT] [-l OVERLAP] [-m MAX [MAX ...]] [-x STARTINDEX] [-t TYPE] [-f FORMAT] [-r [RESCALE [RESCALE ...]]] [-z [COMPRESS]] [-s SLICE] [-a AXIS [AXIS ...]] [--test]


:warning: ImageSplit will overwrite existing output files. Make sure you have your images backed up before you use this utility, to prevent accidental data loss.



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

    -m MAX, --max MAX
                             Maximum number of voxels in each dimension in each
                             output file. MAX can be a scalar or vector corresponding
                             to each image dimension. The file will be optimally
                             split such that each file output dimension is less
                             than or equal to this maximum.


Specify file format, data type, and whether data should be rescaled (normalised):

    -t TYPE, --type TYPE  Output data type (default: same as input file datatype)

    -f FORMAT, --format FORMAT  Output file format such as mhd, tiff (default: same as input file format)

    -r RESCALE, --rescale RESCALE
        Rescale image between the specified min and max
        values. If no RESCALE values are specified, use the volume limits.

    -z COMPRESS, --compress COMPRESS
        Enables compression (default if -Z not specified: no compression). Valid
        values depend on the output file format. -z with no
        COMPRESS argument will choose a suitable compression for
        this file format. For TIFF files, the default is Adboe
        deflat and other valid values are those supported by PIL.


Specify output orientation:

    -s SLICE, --slice SLICE
        Divide image into slices along the specified axis.
        Choose 1, 2, 3 etc to select an axis relative to the
        current image orientation, or c, s, a to select an
        absolute orientation.This argument cannot be used with --axis, --max or --overlap.

    -a AXIS, --axis AXIS
        Axis ordering (default 1 2 3). Specifies the global
        axis corresponding to each dimension in the image
        file. The first value is the global axis represented
        by the first dimension in the file, and so on. One
        value for each dimension, dimensions are numbered
        1,2,3,... and a negative value means that axis is
        flipped. This cannot be used with --slice



Help and testing:

    --test      If set, no writing will be performed to the output files
    -h, --help  Show this help message and exit


Contributing
^^^^^^^^^^^^

Please see the `contributing guidelines`_.


Useful links
^^^^^^^^^^^^

`Source code repository`_
`Documentation`_


Licensing and copyright
-----------------------

Copyright 2017 University College London.
ImageSplit is released under the BSD-3 licence. Please see the `license file`_ for details.


Acknowledgements
----------------

Supported by `Wellcome`_ and `EPSRC`_.


.. _`Wellcome EPSRC Centre for Interventional and Surgical Sciences`: http://www.ucl.ac.uk/weiss
.. _`source code repository`: https://cmiclab.cs.ucl.ac.uk/GIFT-Surg/ImageSplit
.. _`Documentation`: https://imagesplit.readthedocs.io
.. _`University College London (UCL)`: http://www.ucl.ac.uk/
.. _`Translational Imaging Group (TIG)`: http://cmictig.cs.ucl.ac.uk/
.. _`Centre for Medical Image Computing (CMIC)`: http://cmic.cs.ucl.ac.uk
.. _`Wellcome`: https://wellcome.ac.uk/
.. _`GIFT-Surg`: https://www.gift-surg.ac.uk
.. _`EPSRC`: https://www.epsrc.ac.uk/
.. _`contributing guidelines`: https://cmiclab.cs.ucl.ac.uk/GIFT-Surg/ImageSplit/blob/master/CONTRIBUTING.rst
.. _`license file`: https://cmiclab.cs.ucl.ac.uk/GIFT-Surg/ImageSplit/blob/master/LICENSE










