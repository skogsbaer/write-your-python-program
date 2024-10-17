from __future__ import annotations
from wypp import *

@record
class Bar:
    baz: str

def generate_bar():
    return Bar("baz value")

obj1 = Bar("baz value")
obj2 = generate_bar()

check(obj1, obj2)
