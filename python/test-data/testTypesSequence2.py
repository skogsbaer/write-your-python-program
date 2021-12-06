from wypp import *

def foo(seq: Sequence[int]) -> None:
    for item in seq:
        print(item)
    pass

foo([1,2,3])
foo( (4,5)  )
foo("Hello!") # should fail
