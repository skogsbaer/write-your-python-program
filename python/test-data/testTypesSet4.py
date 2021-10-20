from wypp import *

def foo(l: set[Callable[[], str]]) -> list[str]:
    l.add(lambda: 'x') # ok
    res = []
    for f in l:
        res.append(f())
    return res

func = lambda: 42
foo(set([func]))  # error
