from wypp import *
from typing import Protocol
import abc

class Animal(Protocol):
    @abc.abstractmethod
    def makeSound(self, loadness: float):
        pass

class Dog:
    def makeSound(self, loadness: float) -> None:
        pass

class Cat:
    def makeSound(self, loadness: float):
        pass

def foo(animal: Animal):
    animal.makeSound(1.0)

foo(Dog())
foo(Cat())
