from __future__ import annotations
from wypp import *
# See https://github.com/skogsbaer/write-your-python-program/issues/61

# Tests 'return' 
def foo() -> Union(list(int), list[float]):
    pass

foo()
