from wypp import *

def appendSomething(l: set[int]) -> None:
    l.add("foo")

l = set([1,2,3])
appendSomething(l)
print(l)
