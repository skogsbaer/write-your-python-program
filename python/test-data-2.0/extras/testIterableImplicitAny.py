from wypp import *
# See: https://github.com/skogsbaer/write-your-python-program/issues/75

class NotIterable:
    def __repr__(self): return 'NotIterable'

def foo(it: Iterable) -> int:
    for i in it:
        print(i)
    return 42

foo([1, "stefan"])
foo(NotIterable())
