import sys


def assert_or_exit(stmt, num):
    try:
        assert stmt
    except AssertionError:
        sys.exit(num)
