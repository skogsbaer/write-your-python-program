import unittest
from testSample import *

setDieOnCheckFailures(True)

PointOrFloat = Mixed(Point, float)

class TestMixed(unittest.TestCase):

    def test_isSome(self):
        self.assertTrue(PointOrFloat.isSome(Point.make(1, 2)))
        self.assertTrue(PointOrFloat.isSome(3.14))
        self.assertFalse(PointOrFloat.isSome("Stefan"))
