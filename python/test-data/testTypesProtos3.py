from wypp import *

from typing import Protocol
import abc

class Animal(Protocol):
    @abc.abstractmethod
    def makeSound(self, loadness: float) -> str:
        pass

class Dog:
    # incorrect implementation of the Animal protocol
    def makeSound(loadness: int) -> str: # self parameter omitted!
        return f"{loadness} wuffs"

def doSomething(a: Animal) -> None:
    print(a.makeSound(3.14))

doSomething(Dog())
