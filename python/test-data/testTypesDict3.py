from wypp import *

def foo(d: dict[str, Callable[[], str]]) -> list[str]:
    d['x'] = lambda: 42 # error
    res = []
    for _, f in d.items():
        res.append(f())
    return res

func = lambda: "xxx"
foo({'y': func})
