import unittest
from testSample import *
from writeYourProgram import *

PointOrFloat = Mixed(Point, Float)

class Name(Record):
    firstName: String
    lastName: String

class TestMixed(unittest.TestCase):

    def test_isSome(self):
        ty = DefinedLater('Point')
        self.assertTrue(ty.isSome(Point.make(1, 2)))
        self.assertTrue(PointOrFloat.isSome(3.14))
        self.assertFalse(PointOrFloat.isSome("Stefan"))
