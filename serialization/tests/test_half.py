import struct
from formats.half import binary16, _float_from_unsigned16, EXAMPLE_NAN


def test_wp_half_precision_examples():
    """
    https://en.wikipedia.org/wiki/Half-precision_floating-point_format#Half_precision_examples
    """
    for n, f in [
            (0b0000000000000000, 0.),
            (0b1000000000000000, -0.),
            (0b0011110000000000, 1),
            (0b0011110000000001, 1.0009765625),
            (0b1011110000000001, -1.0009765625),
            (0b1100000000000000, -2),
            (0b0100000000000000, 2),
            (0b0111101111111111, 65504.),
            (0b1111101111111111, -65504.),
            (0b0000010000000000, 6.10352e-5),
            (0b0000001111111111, 6.09756e-5),  # subnormal
            (0b0000000000000001, 5.96046e-8),  # subnormal
            (0b0111110000000000, float('infinity')),
            (0b1111110000000000, float('-infinity')),
            (0b0011010101010101, 0.333251953125)]:
        assert binary16(f) == struct.pack(
            '<H', n), (bin(n)[2:].zfill(16), f, binary16(f))


def test_float64_outside_16bit_range():
    for f16, f64 in [
            (1, 1.0000000000000002),  # ≈ the smallest number > 1
            (0, 2**(-1022 - 52)),  # min subnormal positive double
            (0, 2**(-1022) - 2**(-1022 - 52)),  # max subnormal double
            (0, 2**(-1022)),  # min normal positive double
            (float('inf'), (1 + (1 - 2**(-52))) * 2**1023),  # max double
    ]:
        assert binary16(f16) == binary16(f64)


def test_all_bits(N=16):
    for unsigned in range(2**N):
        # make sure '<h' uses 2's complement representation
        # N-bit two's complement
        signed = (unsigned - 2**N) if unsigned & (1 << (N - 1)) else unsigned
        # stored least significant byte first
        binary = struct.pack('<h', signed)
        assert binary == struct.pack('<H', unsigned), (signed, unsigned)

        f = _float_from_unsigned16(unsigned)
        got = binary16(f)
        assert got == binary or got == EXAMPLE_NAN
