from writeYourProgram import *
import unittest
import math

# A shape is one of the following:
# - a circle (Circle)
# - an overlay of two shapes (Overlay)
Shape = Mixed(DefinedLater('Circle'), DefinedLater('Overlay'), DefinedLater('Square'))

# Shape.isSome: any -> boolean

# A point consists of
# - x (Float)
# - y (Float)
class Point(Record):
    x: Float
    y: Float

# Point.make: (Float, Float) ->  Point
# Point.isSome: Any -> Bool
# Point.x: (Point) -> Float
# Point.y: (Point) -> Float

# point at x=10, y=20
p1 = Point.make(10, 20)

# point at x=30, y=50
p2 = Point.make(30, 50)

# point at x=40, y=30
p3 = Point.make(40, 30)

# A circle consists of
# - center (Point)
# - radius (float)
class Circle(Record):
    center: Point
    radius: Float

# Circle.make: (Point, Float) -> Circle
# Circle.isSome: Any -> Bool
# Circle.center: (Circle) -> Point
# Circle.radius: (Circle) -> Float

# circle at p2 with radius=20
c1 = Circle.make(p2, 20)

# circle at p3 with radius=15
c2 = Circle.make(p3, 15)

# A square (parallel to the coordinate system) consists of
# - lower-left corner (Point)
# - size (Float)
class Square(Record):
    corner: Point
    size: Float

# square at p1 with size=40
s1 = Square.make(p1, 40)

# Square.make: (Point, Float) -> Square
# Square.isSome: Any -> Bool
# Square.corner: Square -> Point
# Square.size: Square -> Float

# An overlay consists of
# - top (Shape)
# - bottom (Shape)
class Overlay(Record):
    top: Shape
    bottom: Shape

# Overlay.make: (Shape, Shape) -> Overlay
# Overlay.isSome: any -> boolean
# Overlay.top: (Overlay) -> Shape
# Overlay.bottom: (Overlay) -> Shape

# overlay of circle c1 and square s1
o1 = Overlay.make(c1, s1)
# Overlay of overlay o1 and circle c2
o2 = Overlay.make(o1, c2)

# Calculate the distance between two points
# distance: (Point, Point) -> Float
def distance(p1, p2):
    w = Point.x(p1) - Point.x(p2)
    h = Point.y(p1) - Point.y(p2)
    dist = math.sqrt(w**2 + h**2)
    return dist

# Is a point within a shape?
# pointInShape: (Point, Shape) -> Bool
def pointInShape(point, shape):
    px = Point.x(point)
    py = Point.y(point)
    if Circle.isSome(shape):
        return distance(point, Circle.center(shape)) <= Circle.radius(shape)
    elif Square.isSome(shape):
        corner = Square.corner(shape)
        size = Square.size(shape)
        return (
            px >= Point.x(corner) and
            px <= Point.x(corner) + size and
            py >= Point.y(corner) and
            py <= Point.y(corner) + size
        )
    elif Overlay.isSome(shape):
        return pointInShape(point, Overlay.top(shape)) or pointInShape(point, Overlay.bottom(shape))
    else:
        uncoveredCase()

class TestSample(unittest.TestCase):
    def test_sample(self):
        check(pointInShape(p2, c1), True)
        check(pointInShape(p3, c2), True)
        check(pointInShape(Point.make(51, 50), c1), False)
        check(pointInShape(Point.make(11, 21), s1), True)
        check(pointInShape(Point.make(49, 59), s1), True)
        check(pointInShape(Point.make(9, 21), s1), False)
        check(pointInShape(Point.make(11, 19), s1), False)
        check(pointInShape(Point.make(51, 59), s1), False)
        check(pointInShape(Point.make(49, 61), s1), False)
        check(pointInShape(Point.make(40, 30), c2), True)
        check(pointInShape(Point.make(40, 30), o2), True)
        check(pointInShape(Point.make(0, 0), o2), False)
        check(pointInShape(Point.make(30, 65), o2), True)
        check(pointInShape(Point.make(40, 17), o2), True)
