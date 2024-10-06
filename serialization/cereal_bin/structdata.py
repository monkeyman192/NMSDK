from io import BytesIO, BufferedWriter, BufferedReader
import struct
import inspect
from typing import Optional, Any, TypeVar, get_type_hints, Annotated
from dataclasses import dataclass


class AlignedData(type):
    @property
    def alignment(cls):
        if hasattr(cls, "_alignment"):
            return cls._alignment
        alignment_ = 1
        for name, type_ in cls.__annotations__.items():
            if name.startswith("_"):
                continue
            meta: Field = type_.__metadata__[0]
            type_: datatype = meta.datatype
            if name.startswith("_"):
                continue
            if type_.alignment > alignment_:
                alignment_ = type_.alignment
            if alignment_ == 0x10:
                return alignment_
        return alignment_


class datatype(metaclass=AlignedData):
    _deferred_structs = []

    @property
    def alignment(self):
        if hasattr(self, "_alignment"):
            return self._alignment
        else:
            return type(self).alignment

    @property
    def size(self):
        if hasattr(self, "_size"):
            return self._size
        _size = 0
        for name, type_ in self.__annotations__.items():
            if name.startswith("_"):
                continue
            try:
                _size += type_.size
            except:
                print(name)
                raise

    @classmethod
    def deserialize(cls, buf: BufferedReader):
        raise NotImplementedError

    @classmethod
    def serialize(cls, buf: BufferedWriter, value: Any):
        raise NotImplementedError

    @classmethod
    def _write_padding(cls, buf: BufferedWriter):
        if (misalignment := buf.tell() % cls.alignment) != 0:
            padding = b"\x00" * (cls.alignment - misalignment)
            buf.write(padding)

    @classmethod
    def _skip_padding(cls, buf: BufferedReader):
        if (misalignment := buf.tell() % cls.alignment) != 0:
            buf.seek(cls.alignment - misalignment, 1)

    @classmethod
    def _write(cls, buf: BufferedWriter, value: Any, meta: Optional["Field"] = None):
        cls._write_padding(buf)
        try:
            if inspect.isgeneratorfunction(cls.serialize):
                gen = cls.serialize(buf, value)
                next(gen)
                cls._deferred_structs.append(gen)
            else:
                cls.serialize(buf, value)
            return
        except (NotImplementedError, AttributeError):
            pass
        if hasattr(cls, "_format"):
            if meta and meta.length is not None:
                fmt = cls._format.format(meta.length)
            else:
                fmt = cls._format
            try:
                if hasattr(value, "__iter__"):
                    buf.write(struct.pack(fmt, *value))
                else:
                    buf.write(struct.pack(fmt, value))
            except struct.error:
                print(f"Cannot write {value} with format {fmt}")
                raise
        elif isinstance(value, datatype):
            value.write(buf, False)

    def write(self, buf: Optional[BufferedWriter] = None, _is_top: bool = True) -> BufferedWriter:
        if buf is None:
            buf = BytesIO()
        for name, type_ in self.__annotations__.items():
            if name.startswith("_"):
                continue
            meta: Field = type_.__metadata__[0]
            type_: datatype = meta.datatype
            val = getattr(self, name)
            if meta.length is not None and meta.length > 0:
                if isinstance(val, list):
                    for v in val:
                        type_._write(buf, v)
                else:
                    type_._write(buf, val, meta)
            else:
                type_._write(buf, val)
        if _is_top:
            for dv in self._deferred_structs:
                try:
                    # Move to the end of the file every time
                    buf.seek(0, 2)
                    next(dv)
                except StopIteration:
                    pass
                dv.close()
        return buf

    @classmethod
    def _read(cls, buf: BufferedReader, meta: Optional["Field"] = None):
        # Align ourselves.
        cls._skip_padding(buf)
        try:
            return cls.deserialize(buf)
        except NotImplementedError:
            pass
        if hasattr(cls, "_format"):
            if meta and meta.length is not None:
                fmt = cls._format.format(length=meta.length)
            else:
                fmt = cls._format
            try:
                d = struct.unpack(fmt, buf.read(struct.calcsize(fmt)))
                if len(d) == 1:
                    return d[0]
                else:
                    return d
            except struct.error:
                raise
        else:
            return cls.read(buf)

    @classmethod
    def read(cls, buf: BufferedReader):
        cls_ = cls.__new__(cls)
        for name, pytype in cls_.__annotations__.items():
            if name.startswith("_"):
                continue
            try:
                meta: Field = pytype.__metadata__[0]
            except:
                print(name, pytype, type(pytype))
                raise
            type_: datatype = meta.datatype
            if isinstance(pytype.__origin__, list):
                data = []
                for _ in range(meta.length):
                    data.append(type_._read(buf, meta))
                setattr(cls_, name, data)
            else:
                try:
                    setattr(cls_, name, type_._read(buf, meta))
                except:
                    print(f"Error reading {name} ({pytype}) at offset 0x{buf.tell():X}")
                    raise
        return cls_


@dataclass
class Field:
    datatype: datatype
    length: Optional[int] = None
    encoding: Optional[str] = None
    deferred_loading: bool = False


T = TypeVar("T", bound=datatype)
N = TypeVar("N", bound=int)
