# See https://github.com/skogsbaer/write-your-python-program/issues/43
from wypp import *

def foo(l: list[Callable[[], str]]) -> list[str]:
    l.append(lambda: 42) # error
    res = []
    for f in l:
        res.append(f())
    return res

func = lambda: "xxx"
foo([func])