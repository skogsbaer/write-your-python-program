from wypp import *

@record
class Test:
    foo: 'FooX'

class Foo:
    def __repr__(self):
        return 'Foo'

t = Test(Foo())
print(t)
