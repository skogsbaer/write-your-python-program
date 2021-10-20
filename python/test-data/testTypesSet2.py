from wypp import *

def foo(l: set[Callable[[], str]]) -> list[str]:
    res = []
    for f in l:
        res.append(f())
    return res

print(sorted(list(foo(set([lambda: "1", lambda: "2"])))))
foo(set([lambda: "1", lambda: 42])) # error because the 2nd functions returns an int
