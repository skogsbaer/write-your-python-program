from wypp import *

def foo(d: dict[str, Callable[[], str]]) -> list[str]:
    res = []
    for _, f in d.items():
        res.append(f())
    return res

print(foo({'x': lambda: "1", 'y': lambda: "2"}))
foo({'x': lambda: "1", 'y': lambda: 42}) # error because the 2nd functions returns an int
