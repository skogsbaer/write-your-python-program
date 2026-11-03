# WYPP_TEST_CONFIG: {"args": ["--check"]}
from wypp import *

def inc(x: int) -> int:
    return x + 1

check(inc(1), 2)
check(inc(41), 42)
