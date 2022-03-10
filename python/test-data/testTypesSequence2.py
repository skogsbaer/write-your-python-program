from wypp import *

def foo(seq: Sequence[int]) -> None:
    print(repr(seq))
    print(seq)
    for x in seq:
        print(x)

foo([1,2,3])
foo( (4,5)  )
foo("Hello!") # should fail
