from writeYourProgram import *
import unittest
from sample import *

setDieOnCheckFailures(True)

class TestSample(unittest.TestCase):
    def test_sample(self):
        check(pointInShape(p2, c1), True)
        check(pointInShape(p3, c2), True)
        check(pointInShape(Point(51, 50), c1), False)
        check(pointInShape(Point(11, 21), s1), True)
        check(pointInShape(Point(49, 59), s1), True)
        check(pointInShape(Point(9, 21), s1), False)
        check(pointInShape(Point(11, 19), s1), False)
        check(pointInShape(Point(51, 59), s1), False)
        check(pointInShape(Point(49, 61), s1), False)
        check(pointInShape(Point(40, 30), c2), True)
        check(pointInShape(Point(40, 30), o2), True)
        check(pointInShape(Point(0, 0), o2), False)
        check(pointInShape(Point(30, 65), o2), True)
        check(pointInShape(Point(40, 17), o2), True)
