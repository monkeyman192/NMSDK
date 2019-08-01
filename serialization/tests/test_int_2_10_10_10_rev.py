from formats import write_int_2_10_10_10_rev, bytes_to_int_2_10_10_10_rev


def test_consistency():
    """ Ensure that values written to the format are encoded/decoded correctly.
    """
    byte_data = b'\xb3\x61\x43\x76'
    data = bytes_to_int_2_10_10_10_rev(byte_data)
    assert write_int_2_10_10_10_rev(data) == byte_data
