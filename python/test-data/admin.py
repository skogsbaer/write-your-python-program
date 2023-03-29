import unittest
from abc import *
from wypp import *

CostType = Literal["PERSONNEL", "MATERIAL","OTHER"]
class Costing(ABC):
    def __init__(self) -> None:
        pass

    @abstractmethod
    def getCostType(self):
        pass
    @abstractmethod
    def calcTotalCosts(self):
        pass
    @abstractmethod
    def getOverhead(self):
        pass

class Staff(Costing,ABC):
    def __init__(self, name:str, overhead:float) -> None:
        super().__init__()
        self.name = name
        self.overhead = overhead

    def calcTotalCosts(self):
        return self.calcIncome()* (self.overhead+1)

    @property
    def getCostType(self):
        return "PERSONNEL"
    @property
    def getOverhead(self):
        return self.overhead

    @abstractmethod

    def calcIncome(self):
        pass


class Employee(Staff):
    def __init__(self, name:str,wage:float, overhead:float = 1) -> None:
        super().__init__(name, overhead)
        self.wage = wage
    def setWage(self,wage:float):
        self.wage = wage
    def calcIncome(self):
        return self.wage
    @property
    def getWage(self):
        return self.wage

class Worker(Staff):
    def __init__(self, name: str, hoursWorked:float, hourlyRate:float= 9.50, overhead: float = 0.4) -> None:
        super().__init__(name, overhead)
        self.hoursWorked = hoursWorked
        self.hourlyRate = hourlyRate
    def setHourlyRate(self,rate:float):
        self.hourlyRate = rate
    def calcIncome(self):
        return self.hoursWorked * self.hourlyRate

    @property
    def getHourlyRate(self):
        return self.hourlyRate

    @property
    def getHoursWorked(self):
        return self.hoursWorked


class Consultant(Costing):
    def __init__(self, name:str, dailyRate:float, workdays:int=0) -> None:
        super().__init__()
        self.name = name
        self.dailyRate = dailyRate
        self.workdays = workdays

    def addWorkday(self):
        self.workdays+=1

    def calcTotalCosts(self):
        return self.dailyRate*self.workdays

    @property
    def getCostType(self):
        return "OTHER"
    @property
    def getOverhead(self):
        return 0

class OfficeMaterial(Costing):
    def __init__(self, description:str, price:float) -> None:
        super().__init__()
        self.description = description
        self.price = price


    def calcTotalCosts(self):
        return self.price* (self.getOverhead()+1)

    @property
    def getCostType(self):
        return "MATERIAL"
    @property
    def getOverhead(self):
        return 0.1



def calcTotalCosts(l:list[Costing])->float:
    p = 0
    for i in l:
        p += i.calcTotalCosts()
    return p

if __name__ == '__wypp__' or __name__ == '__main__':
    w = Worker("Carla Cara", 30)
    print(calcTotalCosts([w]))
