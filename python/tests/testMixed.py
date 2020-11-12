import unittest
from testSample import *

setDieOnCheckFailures(True)

PointOrFloat = Mixed(Point, float)

WithNone = Mixed(str, None)

class TestMixed(unittest.TestCase):

    def test_isSome(self):
        self.assertTrue(PointOrFloat.isSome(Point(1, 2)))
        self.assertTrue(PointOrFloat.isSome(3.14))
        self.assertFalse(PointOrFloat.isSome("Stefan"))
        self.assertTrue(WithNone.isSome('foo'))
        self.assertTrue(WithNone.isSome(None))
        self.assertFalse(WithNone.isSome(42))
