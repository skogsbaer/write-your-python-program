from __future__ import annotations
from typing import Iterable

def myRange(n: int) -> Iterator[int]:
    i = 0
    while i < n:
        yield i
        i = i + 1


from wypp import *
check(list(myRange(5)), [0,1,2,3,4])
