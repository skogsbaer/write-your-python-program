import unittest
from writeYourProgram import *
import sys
import traceback

setDieOnCheckFailures(True)

# A point has a
# - x (float)
# - y (float)
Point = Record("Point", "x", float, "y", float)

# Point: (float, float) ->  Point
# Point.isSome: any -> boolean
# Point.x: (Point) -> float
# Point.y: (Point) -> float

Square = Record("Square", "center", Point, "size", float)

Name = Record("Name", "firstName", str, "lastName", str)

@record
class PointNewstyle:
    x: float
    y: float

@record
class SquareNewstyle:
    center: PointNewstyle
    size: float

@record
class NameNewstyle:
    firstName: str
    lastName: str

class TestRecords(unittest.TestCase):

    def test_create(self):
        p1 = Point(1, 2)
        p2 = Point(3, 4)
        self.assertEqual(p1.x, 1)
        self.assertEqual(p1.y, 2)
        self.assertEqual(p2.x, 3)
        self.assertEqual(p2.y, 4)
        square = Square(p1, 5)
        self.assertEqual(square.center, p1)
        self.assertEqual(square.size, 5)

    def test_createNewsystyle(self):
        p1 = PointNewstyle(1, 2)
        p2 = PointNewstyle(3, 4)
        self.assertEqual(p1.x, 1)
        self.assertEqual(p1.y, 2)
        self.assertEqual(p2.x, 3)
        self.assertEqual(p2.y, 4)
        square = SquareNewstyle(p1, 5)
        self.assertEqual(square.center, p1)
        self.assertEqual(square.size, 5)

    def test_createErrorArity(self):
        pass # FIXME

    def test_createErrorTypes(self):
        pass # FIXME

    def test_isSome(self):
        p1 = Point(1, 2)
        square = Square(p1, 5)
        self.assertTrue(Point.isSome(p1))
        self.assertFalse(Point.isSome(42))
        self.assertFalse(Point.isSome(square))
        self.assertTrue(Square.isSome(square))
        self.assertFalse(Square.isSome(42))
        self.assertFalse(Square.isSome(p1))

    def test_isSomeNewstyle(self):
        p1 = PointNewstyle(1, 2)
        square = SquareNewstyle(p1, 5)
        self.assertTrue(PointNewstyle.isSome(p1))
        self.assertFalse(PointNewstyle.isSome(42))
        self.assertFalse(PointNewstyle.isSome(square))
        self.assertTrue(SquareNewstyle.isSome(square))
        self.assertFalse(SquareNewstyle.isSome(42))
        self.assertFalse(SquareNewstyle.isSome(p1))

    def test_toString(self):
        p1 = Point(1, 2)
        self.assertEqual(str(p1), 'Point(x=1, y=2)')
        square = Square(p1, 5)
        self.assertEqual(str(square), 'Square(center=Point(x=1, y=2), size=5)')
        name = Name("Stefan", "Wehr")
        self.assertEqual(str(name), "Name(firstName='Stefan', lastName='Wehr')")

    def test_toStringNewstyle(self):
        p1 = PointNewstyle(1, 2)
        self.assertEqual(str(p1), 'PointNewstyle(x=1, y=2)')
        square = SquareNewstyle(p1, 5)
        self.assertEqual(str(square), 'SquareNewstyle(center=PointNewstyle(x=1, y=2), size=5)')
        name = NameNewstyle("Stefan", "Wehr")
        self.assertEqual(str(name), "NameNewstyle(firstName='Stefan', lastName='Wehr')")

    def test_eq(self):
        p1 = Point(1, 2)
        p2 = Point(1, 4)
        p3 = Point(1, 2)
        self.assertEqual(p1, p1)
        self.assertEqual(p1, p3)
        self.assertNotEqual(p1, p2)
        s1 = Square(p1, 5)
        s2 = Square(p3, 5)
        s3 = Square(p3, 6)
        s4 = Square(p2, 5)
        self.assertEqual(s1, s1)
        self.assertEqual(s1, s2)
        self.assertNotEqual(s1, s3)
        self.assertNotEqual(s1, s4)

    def test_eqNewstyle(self):
        p1 = PointNewstyle(1, 2)
        p2 = PointNewstyle(1, 4)
        p3 = PointNewstyle(1, 2)
        self.assertEqual(p1, p1)
        self.assertEqual(p1, p3)
        self.assertNotEqual(p1, p2)
        s1 = SquareNewstyle(p1, 5)
        s2 = SquareNewstyle(p3, 5)
        s3 = SquareNewstyle(p3, 6)
        s4 = SquareNewstyle(p2, 5)
        self.assertEqual(s1, s1)
        self.assertEqual(s1, s2)
        self.assertNotEqual(s1, s3)
        self.assertNotEqual(s1, s4)

    def test_hash(self):
        p1 = Point(1, 2)
        p2 = Point(1, 4)
        p3 = Point(1, 2)
        self.assertEqual(hash(p1), hash(p3))
        self.assertNotEqual(hash(p1), hash(p2))

    def test_hash(self):
        p1 = PointNewstyle(1, 2)
        p2 = PointNewstyle(1, 4)
        p3 = PointNewstyle(1, 2)
        self.assertEqual(hash(p1), hash(p3))
        self.assertNotEqual(hash(p1), hash(p2))

    def test_unknownSelector(self):
        p1 = Point(1, 2)
        excMsg = None
        # p1.bar
        try:
            p1.foo
        except AttributeError:
            excMsg = traceback.format_exc()
        if excMsg is None:
            self.fail("Expected an AttributeError")
        if "KeyError" in excMsg:
            self.fail("Did no expect a KeyError")

    def test_unknownSelectorNewstyle(self):
        p1 = PointNewstyle(1, 2)
        excMsg = None
        # p1.bar
        try:
            p1.foo
        except AttributeError:
            excMsg = traceback.format_exc()
        if excMsg is None:
            self.fail("Expected an AttributeError")
        self.assertTrue("'PointNewstyle' object has no attribute 'foo'" in excMsg)

