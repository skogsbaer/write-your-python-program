from wypp import *

def foo(seq: Sequence):
    pass

foo([1,2,3])
foo( ("bar", "baz") )
foo("Hello!")
foo(1) # should fail
