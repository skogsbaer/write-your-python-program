from wypp import *

@record
class Person:
    name: str
    age: int

def incAge(p: Person) -> Person:
   Person(p.name, p.age + 1)

# mutability
