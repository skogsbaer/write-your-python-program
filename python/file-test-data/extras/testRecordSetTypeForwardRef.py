# from __future__ import annotations
# Leave the comment, it's needed for tests with python versions <= 3.13

from wypp import *

@record(mutable=True)
class Record:
    x: A

class A:
    pass

def m():
    r = Record(x=A())
    r.x = "hello"

m()

