"""
Functions to convert a quaternion to the 6-byte representation used by NMS
in the animation files.
"""
# Author: monkeyman192

import math


def convert(qi):
    return int(0x3FFF * (math.sqrt(2) * qi + 1))


def determineDropComponent(arr):
    max_loc = 0
    doubled_elements = set()
    condensed_arr = set()
    for i in arr:
        if i in condensed_arr:
            doubled_elements.add(i)
        condensed_arr.add(i)

    print(condensed_arr)

    if len(condensed_arr) == 4:
        max_loc = arr.index(max(condensed_arr))
    else:
        if 0x3FFF not in doubled_elements:
            max_loc = 0
        else:
            max_loc = arr.index(max(condensed_arr))
    return max_loc


def quat_to_hex(q):
    """ converts a quaternion to it's hexadecimal representation """
    q = [convert(i) for i in q]
    drop_index = determineDropComponent(q)
    print(drop_index)
    del q[drop_index]
    drop_index = 3 - drop_index
    i_x = drop_index >> 1
    i_y = drop_index & 1

    q[0] = (i_x << 0xF) + q[0]
    q[1] = (i_y << 0xF) + q[1]

    # TODO: change to just return the list
    hex_out = [hex(i) for i in q]
    return hex_out


q = [0, 0, -0.10186, 0.9947987]

print(quat_to_hex(q))
