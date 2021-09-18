from wypp import *

@record
class Cat:
    name: str
    weight: int

myCat = Cat('Pumpernickel', 2)

@record
class Parrot:
    name: str
    sentence: str

myParrot = Parrot('Mike', "Let's go to the punkrock show")

Animal = Union[Cat, Parrot]

def formatAnimal(a: Animal) -> str:
    if Cat.isSome(a):
        return "Cat " + a.name
    else:
        return "Parrot " + a.name + " says: " + a.sentence
