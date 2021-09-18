from wypp import *

@record
class Person:
    name: str
    age: int

def incAge(p: Person) -> Person:
   return Person(p.name, p.age + 1)

@record(mutable=True)
class MutablePerson:
    name: str
    age: int

def mutableIncAge(p: MutablePerson) -> None:
    p.age = p.age + 1
