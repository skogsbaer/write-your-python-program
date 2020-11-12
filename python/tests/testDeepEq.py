import unittest
import writeYourProgram as wypp
import testSample
from writeYourProgram import deepEq

wypp.setDieOnCheckFailures(True)

class C:
    def __init__(self, x):
        self.x = x

class D:
    def __init__(self, x):
        self.x = x

class A:
    def __init__(self, x):
        self.x = x
    def __eq__(self, other):
        return self is other

Point = wypp.Record("MyPoint", "x", float, "y", float)

class TestDeepEq(unittest.TestCase):
    def test_eq(self):
        self.assertTrue(deepEq(1, 1.0))
        self.assertFalse(deepEq(1, 1.01))
        self.assertTrue(deepEq(1, 1.00000001))
        self.assertTrue(deepEq(1.0, 1.00000001))
        self.assertFalse(deepEq([1,2,3], [1,2]))
        self.assertTrue(deepEq('foo bar', 'foo ' + 'bar'))
        self.assertFalse(deepEq("foo", "bar"))
        self.assertFalse(deepEq('x', 'y'))
        self.assertTrue(deepEq([], []))
        self.assertFalse(deepEq([1], [2]))
        self.assertTrue(deepEq([1, 'foo'], [1.000000000000001, 'foo']))
        self.assertTrue(deepEq([(42.0, 32.0000000001)], [(42.00000000000000001, 32)]))
        self.assertTrue(deepEq({"foo": 42.0}, {"foo": 42.000000000000000001}))
        self.assertFalse(deepEq({"foo": 42.0}, {"foo": 42.1}))
        self.assertTrue(deepEq({"foo": [42.0]}, {"foo": [42.000000000000000001]}))
        self.assertTrue(deepEq({"foo": {'bar': [42.0]}}, {"foo": {'bar': [42.000000000000000001]}}))
        l1 = [1]
        l2 = [1]
        l1.append(l1)
        l2.append(l2)
        try:
            deepEq(l1, l2)
            self.fail("Exception expected")
        except RecursionError:
            pass
        self.assertFalse(deepEq(C(42.0), C(42.0000000000001), structuralObjEq=False))
        self.assertTrue(deepEq(C(42.0), C(42.0000000000001), structuralObjEq=True))
        self.assertFalse(deepEq(C(42.0), D(42.0000000000001), structuralObjEq=True))
        self.assertFalse(deepEq(C(42.0), D(42.0000000000001), structuralObjEq=False))
        self.assertTrue(deepEq(
            testSample.Point(1.0, 2.0), testSample.Point(1.00000000001, 2),
            structuralObjEq=True
        ))
        self.assertTrue(deepEq(
            testSample.Point(1.0, 2.0), testSample.Point(1.00000000001, 2),
            structuralObjEq=False
        ))
        self.assertFalse(deepEq(
            Point(1.0, 2.0), testSample.Point(1.0, 2.0), structuralObjEq=True)
        )
        self.assertFalse(deepEq(
            Point(1.0, 2.0), testSample.Point(1.0, 2.0), structuralObjEq=False)
        )
        self.assertFalse(deepEq(
            testSample.Point(1.0, 3.0), testSample.Point(1.00000000001, 2),
            structuralObjEq=True
        ))
        self.assertFalse(deepEq(
            testSample.Point(1.0, 3.0), testSample.Point(1.00000000001, 2),
            structuralObjEq=False
        ))
        self.assertTrue(deepEq(A(2), A(2), structuralObjEq=True))
        self.assertFalse(deepEq(A(2), A(2), structuralObjEq=False))
