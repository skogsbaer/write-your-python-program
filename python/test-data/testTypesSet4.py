from wypp import *

def foo(l: set[Callable[[], str]]) -> list[str]:
    res = []
    for f in l:
        res.append(f())
    return res

print( foo(set([lambda: 'x']))) # ok
func = lambda: 42
foo(set([func]))  # error
