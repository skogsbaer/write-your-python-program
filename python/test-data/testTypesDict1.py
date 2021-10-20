from wypp import *

def appendSomething(d: dict[str, int]) -> None:
    d['x'] = "foo"

d = {'1': 1, '2': 2}
appendSomething(d)
print(d)
