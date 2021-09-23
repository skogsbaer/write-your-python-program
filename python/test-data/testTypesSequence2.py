from wypp import *

def foo(seq: Sequence[int]):
    pass

foo([1,2,3])
foo( (4,5)  )
foo("Hello!") # should fail
