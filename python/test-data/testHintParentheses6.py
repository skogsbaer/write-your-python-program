from __future__ import annotations
from wypp import *
# See https://github.com/skogsbaer/write-your-python-program/issues/61

@record(mutable=True)
class C:
    x: list(int)

c = C([])
c.x = 1
