from __future__ import annotations
from wypp import *
# See https://github.com/skogsbaer/write-your-python-program/issues/61

T = Union(list(int), list[float])

# Tests 'return' 
def foo() -> T:
    pass

foo()
