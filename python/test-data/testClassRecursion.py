from wypp import *

class C:
    def foo(self, other: C) -> C:
        return other

c = C()
check(c.foo(c), c)

class D1:
    def foo(self, other: 'D2') -> 'D2':
        return other

class D2:
    def bar(self, other: D1) -> D1:
        return other

d1 = D1()
d2 = D2()
check(d1.foo(d2), d2)
check(d2.bar(d1), d1)
