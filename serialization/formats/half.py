#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""Support for IEEE 754 half-precision binary floating-point format: binary16.

>>> [binary16(f) for f in [0.006534, -.1232]] == [b'\xb0\x1e', b'\xe2\xaf']
True
"""
from __future__ import division
import struct
from math import copysign, frexp, isinf, isnan, trunc

NEGATIVE_INFINITY = b'\x00\xfc'
POSITIVE_INFINITY = b'\x00\x7c'
POSITIVE_ZERO = b'\x00\x00'
NEGATIVE_ZERO = b'\x00\x80'
# exp=2**5-1 and significand non-zero
EXAMPLE_NAN = struct.pack('<H', (0b11111 << 10) | 1)


def binary16(f):
    """Convert Python float to IEEE 754-2008 (binary16) format.

    https://en.wikipedia.org/wiki/Half-precision_floating-point_format
    """
    if isnan(f):
        return EXAMPLE_NAN

    sign = copysign(1, f) < 0
    if isinf(f):
        return NEGATIVE_INFINITY if sign else POSITIVE_INFINITY

    #           1bit        10bits             5bits
    # f = (-1)**sign * (1 + f16 / 2**10) * 2**(e16 - 15)
    # f = (m * 2)                        * 2**(e - 1)
    m, e = frexp(f)
    assert not (isnan(m) or isinf(m))
    if e == 0 and m == 0:  # zero
        return NEGATIVE_ZERO if sign else POSITIVE_ZERO

    f16 = trunc((2 * abs(m) - 1) * 2**10)  # XXX round toward zero
    assert 0 <= f16 < 2**10
    e16 = e + 14
    if e16 <= 0:  # subnormal
        # f = (-1)**sign * fraction / 2**10 * 2**(-14)
        f16 = int(2**14 * 2**10 * abs(f) + .5)  # XXX round
        e16 = 0
    elif e16 >= 0b11111:  # infinite
        return NEGATIVE_INFINITY if sign else POSITIVE_INFINITY
    else:
        # normalized value
        assert 0b00001 <= e16 < 0b11111, (f, sign, e16, f16)
    """
    http://blogs.perl.org/users/rurban/2012/09/reading-binary-floating-point-numbers-numbers-part2.html
    sign    1 bit  15
    exp     5 bits 14-10     bias 15
    frac   10 bits 9-0

    (-1)**sign * (1 + fraction / 2**10) * 2**(exp - 15)

    +-+-----[1]+----------[0]+ # little endian
    |S| exp    |    fraction |
    +-+--------+-------------+
    |1|<---5-->|<---10bits-->|
    <--------16 bits--------->
    """
    return struct.pack('<H', (sign << 15) | (e16 << 10) | f16)


def bytes_to_half(bytes_):
    """ Read an array of bytes into a list of half's."""
    fmt = '<' + 'H' * (len(bytes_) // 2)
    data = struct.unpack(fmt, bytes_)
    return [_float_from_unsigned16(n) for n in data]


def _float_from_unsigned16(n):
    assert 0 <= n < 2**16
    sign = n >> 15
    exp = (n >> 10) & 0b011111
    fraction = n & (2**10 - 1)
    if exp == 0:
        if fraction == 0:
            return -0.0 if sign else 0.0
        else:
            return (-1)**sign * fraction / 2**10 * 2**(-14)  # subnormal
    elif exp == 0b11111:
        if fraction == 0:
            return float('-inf') if sign else float('inf')
        else:
            return float('nan')
    return (-1)**sign * (1 + fraction / 2**10) * 2**(exp - 15)


if __name__ == "__main__":
    print(bytes_to_half(b'\xa8\x3f'))
    print(bytes_to_half(b'\xb4\x5d\x12\xc2'))
