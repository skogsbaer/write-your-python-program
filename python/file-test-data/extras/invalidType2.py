# from __future__ import annotations
# Leave the comment, it's needed for tests with python versions <= 3.13

from wypp import *
# See https://github.com/skogsbaer/write-your-python-program/issues/61

T = Union(list(int), list[float])

# Tests 'return'
def foo() -> T:
    pass

foo()
