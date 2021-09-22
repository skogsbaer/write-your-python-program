from wypp import *

def appendSomething(l: list[int], l2: list[int]) -> None:
    l.append("foo")

l = [1,2,3]
appendSomething(l, [])
print(l)
