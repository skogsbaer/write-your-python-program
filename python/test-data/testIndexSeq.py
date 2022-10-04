from wypp import *

def foo(seq: Sequence) -> int:
    i = seq.index("foo")
    return i

print(foo(["bar", "foo", "baz"])) # should print 1
