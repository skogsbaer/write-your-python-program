from wypp import *

@record
class Car:
    color: str

@record
class Garage:
    cars: list['Car']
