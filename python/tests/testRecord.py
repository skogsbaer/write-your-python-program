import unittest
from writeYourProgram import *
import sys
import traceback
import dataclasses

setDieOnCheckFailures(True)

@record
class Point:
    x: float
    y: float

@record
class Square:
    center: Point
    size: float

@record
class Name:
    firstName: str
    lastName: str

@record(mutable=True)
class Box:
    x: int

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
        list[Point] # just use it
        list[Literal['foo', 'bar']] # just use it

    def test_createErrorArity(self):
        pass # FIXME

    def test_createErrorTypes(self):
        pass # FIXME

    def test_toString(self):
        p1 = Point(1, 2)
        self.assertEqual(str(p1), 'Point(x=1, y=2)')
        square = Square(p1, 5)
        self.assertEqual(str(square), 'Square(center=Point(x=1, y=2), size=5)')
        name = Name("Stefan", "Wehr")
        self.assertEqual(str(name), "Name(firstName='Stefan', lastName='Wehr')")

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

    def test_eq2(self):
        p1 = Point(0.3, 2)
        p2 = Point(0.1 + 0.1 + 0.1, 2)
        # general equality must not use special logic for floats, otherwise == is not transitive
        self.assertEqual(p1 == p2, False)
        # check should use special logic for floats
        check(p1, p2)


    def test_hash(self):
        p1 = Point(1, 2)
        p2 = Point(1, 4)
        p3 = Point(1, 2)
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
        self.assertTrue("'Point' object has no attribute 'foo'" in excMsg)

    def test_immutable(self):
        p1 = Point(1, 2)
        try:
            p1.x = 5
            self.fail('Expected FrozenInstanceError')
        except dataclasses.FrozenInstanceError:
            pass

    def test_mutable(self):
        b = Box(4)
        self.assertEqual(b.x, 4)
        b.x = 5
        self.assertEqual(b.x, 5)

    def test_addField(self):
        b = Box(5)
        try:
            b.foobar = 'foobar'
            self.fail("Expected AttributeError")
        except AttributeError:
            pass
        p1 = Point(1, 2)
        try:
            p1.z = 5
            self.fail('Expected FrozenInstanceError')
        except dataclasses.FrozenInstanceError:
            pass
