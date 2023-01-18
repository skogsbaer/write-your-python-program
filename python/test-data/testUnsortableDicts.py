from wypp import *

def foo():
    pass
def bar():
    pass

check({bar: 2, foo: 1}, {foo: 1, bar: 2.00000000001})
