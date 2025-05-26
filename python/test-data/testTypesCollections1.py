from wypp import *

def appendSomething(l: list[int]):
    l.append("foo")

l = [1,2,3]
appendSomething(l)
print(l)
