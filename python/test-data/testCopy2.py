# https://github.com/skogsbaer/write-your-python-program/issues/106
from wypp import *

def wrapDict(d: dict[str, int]) -> Any:
    return d

d1 = {"foo": 1, "bar": 2}
d2 = wrapDict(d1).copy()
check(d1 is d2, False)
check(d1 == d2, True)
print(f"d1: {d1}")
print(f"d2: {d2}")
