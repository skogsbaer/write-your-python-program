from wypp import *

def foo(l: list[Callable[[], str]]) -> list[str]:
    res = []
    for f in l:
        res.append(f())
    return res

print(foo([lambda: "1", lambda: "2"]))
foo([lambda: "1", lambda: 42]) # error because the 2nd functions returns an int
