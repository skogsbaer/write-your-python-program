from __future__ import annotations
# See: https://github.com/skogsbaer/write-your-python-program/issues/74

from wypp import *
import abc

class Shape(abc.ABC):
    def __init__(self, center: Point)->None:
        self.center = center
    @abc.abstractmethod
    def area(self) -> float:
        pass

class Circle(Shape):
    def __init__(self, center: Point, radius: float)->None:
        super().__init__(center)
        self.radius = float
    # no implementation of area!

@dataclass
class Point:
    x: float
    y: float
    def move(self, x: float, y: float)->None:
        self.x = self.x + x
        self.y = self.y + y

Circle(Point(0, 0), 1)