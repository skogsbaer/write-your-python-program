from wypp import *

class C:
    def foo(self, other: Self) -> Self:
        return other

c = C()
check(c.foo(c), c)
