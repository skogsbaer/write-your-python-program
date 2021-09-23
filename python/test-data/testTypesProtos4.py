from wypp import *

from typing import Protocol
import abc

class Interface(Protocol):
    abc.abstractmethod
    def meth(self) -> Callable[[int], int]:
        pass

class ConcreteCorrect:
    def meth(self) -> Callable[[int], int]:
        return lambda x: x + 1

def bar(s: str) -> int:
    return len(s)

class ConcreteWrong:
    def meth(self) -> Callable[[int], int]:
        return lambda x: bar(x) # invalid call of bar with argument of type int

def foo(obj: Interface) -> int:
    fn = obj.meth()
    return fn(2)

print(foo(ConcreteCorrect()))
print(foo(ConcreteWrong()))
