# from __future__ import annotations
# Leave the comment, it's needed for tests with python versions <= 3.13

class A:
    def foo(self, b: B):
        pass

class B:
    def bar(self, a: A):
        pass

a = A()
b = B()
a.foo(b)
b.bar(a)
print('ok')
