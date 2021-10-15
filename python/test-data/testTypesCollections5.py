from wypp import *

def foo(l: list[Callable[[], str]]) -> list[str]:
    l.append(lambda: 'x') # ok
    res = []
    for f in l:
        res.append(f())
    return res

foo([lambda: 42])  # error
