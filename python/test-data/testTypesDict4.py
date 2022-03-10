from wypp import *

def foo(d: dict[str, Callable[[], str]]) -> list[str]:
    d['x'] = lambda: 'x' # ok
    res = []
    for k, f in d.items():
        res.append(f())
    return res

def bar(d: dict[str, Callable[[], str]]) -> list[str]:
    return foo(d)

func = lambda: 42
bar({'y': func})  # error
