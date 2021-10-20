from wypp import *

def foo(d: dict[str, Callable[[], str]]) -> list[str]:
    d['x'] = lambda: 'x' # ok
    res = []
    for k, f in d.items():
        res.append(f())
    return res

func = lambda: 42
foo({'y': func})  # error
