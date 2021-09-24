from writeYourProgram import *
import math
from untypy import typechecked
import typing

Drink = Literal["Tea", "Coffee"]

# berechnet wieviele Tassen ich von einem Getränk trinken darf
@typechecked
def canDrink(d: Drink) -> int:
    if d == "Tea":
        return 5
    elif d == "Coffee":
        return 1

# A shape is one of the following:
# - a circle (Circle)
# - a square (Square)
# - an overlay of two shapes (Overlay)
Shape = typing.Union[typing.ForwardRef('Circle'), typing.ForwardRef('Square'), typing.ForwardRef('Overlay')]
Shape = typing.Union['Circle', 'Square', 'Overlay']

# A point consists of
# - x (float)
# - y (float)
@record
class Point:
    x: float
    y: float
# Point: (float, float) ->  Point
# For some Point p
# p.x: float
# p.y: float

# point at x=10, y=20
p1 = Point(10, 20)

# point at x=30, y=50
p2 = Point(30, 50)

# point at x=40, y=30
p3 = Point(40, 30)

# A circle consists of
# - center (Point)
# - radius (float)
@record
class Circle:
    center: Point
    radius: float

# Circle: (Point, float) -> Circle
# For some circle c
# c.center: Point
# c.radius: float

# circle at p2 with radius=20
c1 = Circle(p2, 20)

# circle at p3 with radius=15
c2 = Circle(p3, 15)

# A square (parallel to the coordinate system) consists of
# - lower-left corner (Point)
# - size (float)
@record
class Square:
    corner: Point
    size: float

# square at p1 with size=40
s1 = Square(p1, 40)

# Square: (Point, float) -> Square
# For some square s
# s.corner: Point
# s.size: float

# An overlay consists of
# - top (Shape)
# - bottom (Shape)
@record
class Overlay:
    top: Shape
    bottom: Shape

# Overlay: (Shape, Shape) -> Overlay
# For some overlay:
# o.top: Shape
# o.bottom: Shape

# overlay of circle c1 and square s1
o1 = Overlay(c1, s1)
# Overlay of overlay o1 and circle c2
o2 = Overlay(o1, c2)

# Calculate the distance between two points
@typechecked
def distance(p1: Point, p2: Point) -> float:
    w = p1.x - p2.x
    h = p1.y - p2.y
    dist = math.sqrt(w**2 + h**2)
    return dist

# Is a point within a shape?
@typechecked
def pointInShape(point: Point, shape: Shape) -> bool:
    px = point.x
    py = point.y
    if type(shape) == Circle:
        return distance(point, shape.center) <= shape.radius
    elif type(shape) == Square:
        corner = shape.corner
        size = shape.size
        return (
            px >= corner.x and
            px <= corner.x + size and
            py >= corner.y and
            py <= corner.y + size
        )
    elif type(shape) == Overlay:
        return pointInShape(point, shape.top) or pointInShape(point, shape.bottom)
    else:
        uncoveredCase()
