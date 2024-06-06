from io import BufferedWriter
import struct

from .structdata import datatype, Field


class boolean(datatype):
    _format = "<?"
    _alignment = 1


class int16(datatype):
    _format = "<h"
    _alignment = 2


class uint16(datatype):
    _format = "<H"
    _alignment = 2


class int32(datatype):
    _format = "<i"
    _alignment = 4


class uint32(datatype):
    _format = "<I"
    _alignment = 4


class int64(datatype):
    _format = "<q"
    _alignment = 8


class uint64(datatype):
    _format = "<Q"
    _alignment = 8


class single(datatype):
    _format = "f"
    _alignment = 4


class double(datatype):
    _format = "d"
    _alignment = 8


class string(datatype):
    _format = "{length}s"
    _alignment = 1

    @classmethod
    def _read(cls, buf: BufferedWriter, meta: Field) -> str:
        cls._skip_padding(buf)
        fmt = cls._format.format(length=meta.length)
        encoding = meta.encoding or "utf-8"
        return struct.unpack(fmt, buf.read(meta.length))[0].decode(encoding).strip("\x00")

    @classmethod
    def _write(cls, buf: BufferedWriter, value: str, meta: Field):
        cls._write_padding(buf)
        fmt = cls._format.format(length=meta.length)
        encoding = meta.encoding or "utf-8"
        buf.write(struct.pack(fmt, value.encode(encoding)))