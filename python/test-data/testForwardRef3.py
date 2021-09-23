from wypp import *

@record
class Test:
    foo: 'Foo'

class Foo:
    def __repr__(self):
        return 'Foo'

t = Test(Foo())
print(t)
