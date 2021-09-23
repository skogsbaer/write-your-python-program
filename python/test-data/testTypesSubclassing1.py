from wypp import *

class AnimalFood:
    def __init__(self, name: str):
        self.name = name

class Animal:
    def feed(self, food: AnimalFood) -> None:
        print(f'Tasty animal food: {food.name}')

class DogFood(AnimalFood):
    def __init__(self, name: str, weight: float):
        super().__init__(name)
        self.weight = weight

class Dog(Animal):
    # Dog provides an invalid override for feed
    def feed(self, food: DogFood) -> None:
        print(f'Tasty dog food: {food.name} ({food.weight}g)')

def feedAnimal(a: Animal) -> None:
    a.feed(AnimalFood('some cat food'))

dog = Dog()
feedAnimal(dog)
