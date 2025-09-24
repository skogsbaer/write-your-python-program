from wypp import *

def foo(seq: Sequence) -> None:
    print(seq)
    pass

foo([1,2,3])
foo( ("bar", "baz") )
foo("Hello!")
foo(1) # should fail
