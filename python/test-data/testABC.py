from abc import ABC, abstractmethod

class A(ABC):
    @abstractmethod
    def foo(self):
        pass

class Sub(A):
    def __repr__(self):
        return "SUB"
    def foo(self):
        print("foo")

class B:
    def __init__(self, x: A):
        self.x = x
    def getX(self) -> A:
        return self.x

print(isinstance(Sub(), A))
b = B(Sub())
a = b.getX()
print(a)
