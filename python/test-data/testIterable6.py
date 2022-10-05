from wypp import *
import sys

def foo(i: int) -> Iterable[int]:
    print('start of foo')
    yield i
    print('end of foo')

i = iter(foo(15))
print(list(i))
