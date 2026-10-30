# WYPP_TEST_CONFIG: {"args": ["--check"]}
from wypp import *

def inc(x: int) -> int:
    return x + 1

# The failing check must not change the exit code: the exception wins
check(inc(41), 41)
raise ValueError('something went wrong')
