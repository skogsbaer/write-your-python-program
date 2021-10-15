from wypp import *

def foo(l: list[Callable[[], str]]) -> list[str]:
    l.append(lambda: 42) # error
    res = []
    for f in l:
        res.append(f())
    return res

func = lambda: "xxx"
foo([func])
