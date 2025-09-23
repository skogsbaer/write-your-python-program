# See https://github.com/skogsbaer/write-your-python-program/issues/62

from wypp import *

@record
class Car:
    color: str

@record
class Garage:
    cars: list['Car']

class CarManager:
    def store(self, car : set['Car'], garage :'Garage') -> 'CarManager':
        return self

garage = Garage(cars=[Car(color='red'), Car(color='blue')])
for car in garage.cars:
    pass

# trigger error
garage = Garage(cars=[Car(color='red'), "Not A Car"])
for car in garage.cars:
    pass
