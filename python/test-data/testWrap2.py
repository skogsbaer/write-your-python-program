from wypp import *

@record
class Car:
    licensePlate: str
    color: str

@record
class Street:
    name: str
    cars: list[Car]

def removeElem(seq: Sequence, x: Any) -> Sequence:
    i = seq.index(x)
    return seq[:i] + seq[i+1:]

rotesAuto = Car('OG PY 123', 'rot')
blauesAuto = Car(licensePlate='OG HS 130', color='blau')
grünesAuto = Car('FR XJ 252', 'grün')

hauptstraße = Street('Hauptstraße', [rotesAuto, blauesAuto])

def leaveStreet(street: Street, car: Car) -> Street:
    newCars = removeElem(street.cars, car)
    return Street(street.name, newCars)

s = leaveStreet(hauptstraße, blauesAuto)
print(s)
