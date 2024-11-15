from __future__ import annotations
from wypp import *
# See https://github.com/skogsbaer/write-your-python-program/issues/61

def foo(l: list(int)) -> int:
    return len(l)

check(foo([1,2,3]), 3)
