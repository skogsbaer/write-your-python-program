from wypp import *

@record(mutable=True)
class StreetM:
    name: str
    cars: list[CarM]
    # Einbiegen eines Auto auf eine Straße
    # SEITENEFFEKT: Liste der Autos wird geändert.
    def turnIntoStreet(self: StreetM, car: Car) -> None:
        if car not in self.cars:
            self.cars.append(car)
    # Verlassen einer Straße
    # SEITENEFFEKT: Liste der Autos wird geändert.
    def leaveStreet(self: StreetM, car: Car) -> None:
        if car in self.cars:
            self.cars.remove(car)

@record(mutable=True)
class CarM:
    licensePlate: str
    color: str

@record
class Car:
    licensePlate: str
    color: str

redCarM = CarM('OG PY 123', 'rot')
mainStreetM = StreetM('Hauptstraße', [redCarM])
mainStreetM.turnIntoStreet(redCarM)
