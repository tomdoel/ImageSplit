# coding=utf-8
"""
Support multiple imaging data types

Author: Tom Doel
Copyright UCL 2017

"""


class DataTypeTemplate(object):
    """Data format paramaters for standard data types"""

    def __init__(self,
                 bytes_per_voxel,
                 numpy_base=None,
                 metaio_type=None,
                 vge_type=None,
                 is_rgb=False):
        self.numpy_base = numpy_base
        self.vge_type = vge_type
        self.bytes_per_voxel = bytes_per_voxel
        self.metaio_type = metaio_type
        self.is_rgb = is_rgb


class DataType(object):
    """Return required factory for image file formats"""

    # File format constants
    RGB_TYPE = "rgb"
    CHAR_TYPE = "char"
    UCHAR_TYPE = "uchar"
    SHORT_TYPE = "short"
    USHORT_TYPE = "ushort"
    LONG_TYPE = "long"
    ULONG_TYPE = "ulong"
    LONG_LONG_TYPE = "longlong"
    ULONG_LONG_TYPE = "ulonglong"
    FLOAT_TYPE = "float"
    DOUBLE_TYPE = "double"

    types = {
        RGB_TYPE: DataTypeTemplate(metaio_type='MET_UCHAR',
                                   numpy_base='u1',
                                   bytes_per_voxel=1,
                                   is_rgb=True),
        CHAR_TYPE: DataTypeTemplate(metaio_type='MET_CHAR',
                                    numpy_base='i1',
                                    bytes_per_voxel=1),
        UCHAR_TYPE: DataTypeTemplate(metaio_type='MET_UCHAR',
                                     numpy_base='u1',
                                     bytes_per_voxel=1),
        SHORT_TYPE: DataTypeTemplate(metaio_type='MET_SHORT',
                                     numpy_base='i2',
                                     bytes_per_voxel=2),
        USHORT_TYPE: DataTypeTemplate(metaio_type='MET_USHORT',
                                      numpy_base='u2',
                                      bytes_per_voxel=2),
        LONG_TYPE: DataTypeTemplate(metaio_type='MET_LONG',
                                    numpy_base='i4',
                                    vge_type='VolumeDataType_Float',
                                    bytes_per_voxel=4),
        ULONG_TYPE: DataTypeTemplate(metaio_type='MET_ULONG',
                                     numpy_base='u4',
                                     bytes_per_voxel=4),
        LONG_LONG_TYPE: DataTypeTemplate(metaio_type='MET_LONG_LONG',
                                         numpy_base='i8',
                                         bytes_per_voxel=8),
        ULONG_LONG_TYPE: DataTypeTemplate(metaio_type='MET_ULONG_LONG',
                                          numpy_base='u8',
                                          bytes_per_voxel=8),
        FLOAT_TYPE: DataTypeTemplate(metaio_type='MET_FLOAT',
                                     numpy_base='f4',
                                     bytes_per_voxel=4),
        DOUBLE_TYPE: DataTypeTemplate(metaio_type='MET_DOUBLE',
                                      numpy_base='f8',
                                      bytes_per_voxel=8)
    }

    def __init__(self, template_name, byte_order_msb, compression=None,
                 is_imagej=False):
        self.template = DataType.types[template_name.lower()]
        self.is_rgb = self.template.is_rgb
        self.byte_order_msb = byte_order_msb
        self.compression = compression
        self.is_imagej = is_imagej

    def get_numpy_format(self):
        """Create a numpy data format string for this data type"""
        prefix = '>' if self.byte_order_msb else '<'
        return prefix + self.template.numpy_base

    def get_is_rgb(self):
        """True if this datatype is an RGB format"""
        return self.is_rgb

    def get_is_imagej(self):
        """True if this datatype is an RGB format"""
        return self.is_imagej

    def __get_type(self, type_string):
        return self.types[type_string]

    @classmethod
    def from_metaio(cls, metaio_type_name, byte_order_msb):
        """Create a DataType from a MetaIO data type string"""
        for name, data_type in cls.types.items():
            if data_type.metaio_type == metaio_type_name:
                return cls(template_name=name,
                           byte_order_msb=byte_order_msb)
        raise ValueError("Unknown type: " + metaio_type_name)

    @classmethod
    def from_vge(cls, vge_type_name):
        """Create a DataType from a vge header data type string"""
        for name, data_type in cls.types.items():
            if data_type.vge_type == vge_type_name:
                return cls(template_name=name,
                           byte_order_msb=True)
        raise ValueError("Unknown type: " + vge_type_name)

    @classmethod
    def name_from_metaio(cls, metaio_type_name):
        """Get a DataType string from a MetaIO data type string"""
        for name, data_type in cls.types.items():
            if data_type.metaio_type == metaio_type_name:
                return name

        raise ValueError("Unknown type: " + metaio_type_name)

    @classmethod
    def metaio_from_name(cls, name):
        """Return the MetaIO name string from a DataType string"""
        return cls.types[name].metaio_type

    @classmethod
    def name_from_vge(cls, vge_type_name):
        """Get a DataType string from a vge data type string"""
        for name, data_type in cls.types.items():
            if data_type.vge_type == vge_type_name:
                return name

        raise ValueError("Unknown type: " + vge_type_name)
