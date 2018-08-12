# coding=utf-8
"""
Support multiple imaging formats

Author: Tom Doel
Copyright UCL 2017

"""

from imagesplit.file.file_formats import FileFormats
from imagesplit.file.metaio_reader import MetaIoFile
from imagesplit.file.tiff_file_reader import TiffFileReader
from imagesplit.file.vol_reader import VolFile


class FormatFactory(object):
    """Return required factory for image file formats"""

    _factories = {FileFormats.METAIO_FORMAT: MetaIoFile,
                  FileFormats.VOL_FORMAT: VolFile,
                  FileFormats.TIFF_FORMAT: TiffFileReader}

    @classmethod
    def get_factory(cls, format_string):
        """Get the file factory for this format"""

        format_string = cls.simplify_format(format_string)
        if format_string in cls._factories:
            return cls._factories[format_string]

        raise ValueError("Unknown file format: " + format_string)

    @classmethod
    def extension_to_format(cls, file_extension):
        """Get the format name for this file"""

        # Remove leading and trailing spaces and leading period if it exists
        ext = file_extension.lower().strip().lstrip('.')

        if ext in ("mhd", "mha"):
            return FileFormats.METAIO_FORMAT

        elif ext == "vge":
            return FileFormats.VOL_FORMAT

        elif ext in ("tif", "tiff"):
            return FileFormats.TIFF_FORMAT

        raise ValueError("Unknown file format: " + file_extension)

    @classmethod
    def simplify_format(cls, format_name):
        """Get the standard format name for a format name which should be
        standard but may have been modified"""

        # Remove leading and trailing spaces and leading period if it exists
        name = format_name.lower().strip().lstrip('.')

        if name in ("mhd", "mha"):
            return FileFormats.METAIO_FORMAT

        elif name in ("vge", "vol"):
            return FileFormats.VOL_FORMAT

        elif name in ("tif", "tiff"):
            return FileFormats.TIFF_FORMAT

        raise ValueError("Unknown file format: " + format_name)

    @classmethod
    def get_extension_for_format(cls, file_format):
        """Returns the output file extension for this file format"""

        file_format = cls.simplify_format(file_format)
        if file_format == "mhd":
            return ".mhd"
        elif file_format == "tiff":
            return ".tiff"

        raise ValueError("Format " + file_format + " not supported")
