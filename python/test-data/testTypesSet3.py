from wypp import *

def foo(l: set[Callable[[], str]]) -> list[str]:
    l.add(lambda: 42) # error
    res = []
    for f in l:
        res.append(f())
    return res

func = lambda: "xxx"
foo(set([func]))
