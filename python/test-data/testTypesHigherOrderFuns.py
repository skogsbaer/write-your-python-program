from wypp import *

def map(container: Iterable[str], fun: Callable[[str], int]) -> list[int]:
    res = []
    for x in container:
        res.append(fun(x))
    return res

print(map(["hello", "1"], len))
map(["hello", "1"], lambda x: x)
