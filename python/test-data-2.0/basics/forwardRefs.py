from __future__ import annotations

class A:
    def foo(self, b: B):
        pass

class B:
    def bar(self, a: A):
        pass

a = A()
a.foo(a)
