import sys
from inspect import stack, getframeinfo


def assert_or_exit(stmt):
    try:
        assert stmt
    except AssertionError:
        line_num = getframeinfo(stack()[1][0]).lineno
        sys.exit(line_num)
