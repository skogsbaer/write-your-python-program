from wypp import *

from typing import Protocol
import abc

class Animal(Protocol):
    @abc.abstractmethod
    def makeSound(loadness: float) -> str: # self parameter omitted!
        pass

class Dog:
    # incorrect implementation of the Animal protocol
    def makeSound(self, loadness: int) -> str:
        return f"{loadness} wuffs"
    def __repr__(self) -> str:
        return f"<{type(self).__qualname__}>"

def doSomething(a: Animal) -> None:
    print(a.makeSound(3.14))

doSomething(Dog())
