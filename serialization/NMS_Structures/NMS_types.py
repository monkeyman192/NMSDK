from io import BufferedWriter, BufferedReader
import struct
from typing import Annotated, Type, TypeVar
import types

from serialization.utils import bytes_to_quat
from serialization.cereal_bin.structdata import datatype, Field
import serialization.cereal_bin.basic_types as bt


T = TypeVar("T", bound=datatype)


class VariableSizeString(datatype):
    _alignment = 8

    @classmethod
    def deserialize(cls, buf: BufferedReader) -> str:
        start = buf.tell()
        offset, size, _ = struct.unpack("<QII", buf.read(0x10))
        ret = buf.tell()
        buf.seek(start + offset)
        val = struct.unpack(f"{size}s", buf.read(size))[0].decode()
        val = val.rstrip("\x00")
        buf.seek(ret)
        return val
    
    @classmethod
    def serialize(cls, buf: BufferedWriter, value: str):
        ptr = buf.tell()
        buf.write(struct.pack("<QII", 0, 0, 0xAAAAAA01))
        yield
        offset = buf.tell()
        value = str(value)
        size = len(value)
        if size != 0:
            buf.write(struct.pack(f"{size + 1}s", value.encode() + b"\x00"))
            buf.seek(ptr)
            buf.write(struct.pack("<QI", offset - ptr, size + 1))


class NMS_list(datatype):
    _alignment = 8
    _list_type: datatype

    def __class_getitem__(cls: Type["NMS_list"], type_: Type[T]):
        _cls: Type[NMS_list[T]] = types.new_class(
            f"NMS_list[{type_}]", (cls,)
        )
        _cls._list_type = type_
        return _cls

    @classmethod
    def deserialize(cls, buf: BufferedReader) -> list[int]:
        start = buf.tell()
        offset, size, _ = struct.unpack("<QII", buf.read(0x10))
        ret = buf.tell()
        buf.seek(start + offset)
        data = []
        for _ in range(size):
            data.append(cls._list_type._read(buf))
        buf.seek(ret)
        return data

    @classmethod
    def serialize(cls, buf: BufferedWriter, value):
        ptr = buf.tell()
        buf.write(struct.pack("<QII", 0, 0, 0xAAAAAA01))
        yield
        cls._list_type._write_padding(buf)
        offset = buf.tell()
        size = len(value)
        if size != 0:
            for v in value:
                cls._list_type._write(buf, v)
            buf.seek(ptr)
            buf.write(struct.pack("<QI", offset - ptr, size))


class Vector4f(datatype):
    _alignment = 0x10
    _format = "ffff"


class Quaternion_list(datatype):
    @classmethod
    def deserialize(cls, buf: BufferedReader) -> list[int]:
        start = buf.tell()
        offset, size, _ = struct.unpack("<QII", buf.read(0x10))
        ret = buf.tell()
        buf.seek(start + offset)
        data = []
        for _ in range(size // 3):
            data.append(bytes_to_quat(buf))
        buf.seek(ret)
        return data

    # TODO: Write
    # @classmethod
    # def serialize(cls, buf: BufferedWriter, value):
    #     ptr = buf.tell()
    #     buf.write(struct.pack("<QII", 0, 0, 0xAAAAAA01))
    #     yield
    #     cls._list_type._write_padding(buf)
    #     offset = buf.tell()
    #     size = len(value)
    #     if size != 0:
    #         for v in value:
    #             cls._list_type._write(buf, v)
    #         buf.seek(ptr)
    #         buf.write(struct.pack("<QI", offset - ptr, size))


class MBINHeader(datatype):
    _size = 0x20
    header_magic: Annotated[int, Field(bt.uint64)] = 0xCCCCCCCCCCCCCCCC
    header_version: Annotated[int, Field(bt.uint16)] = 3300
    header_mbin_version: Annotated[int, Field(bt.uint16)] = 4
    header_namehash: Annotated[int, Field(bt.uint32)] = 0
    header_guid: Annotated[int, Field(bt.uint64)] = 0
    header_timestamp: Annotated[int, Field(bt.uint64)] = 0


class astring(bt.string):
    _alignment = 0x8
