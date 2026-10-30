# WYPP_TEST_CONFIG: {"args": ["--check"]}
from wypp import *

def inc(x: int) -> int:
    return x + 1

# The failing check must not change the exit code: the type error wins
check(inc(41), 41)
check(inc('41'), 42)
