import unittest
from writeYourProgram import *

setDieOnCheckFailures(True)

ty = ForwardRef('Name')

@record
class Name:
    firstName: str
    lastName: str

@record
class Point:
    x: float
    y: float

PointOrFloat = Union[Point, float]

WithNone = Union[str, None]

class C:
    pass

def abcGenerator():
    yield("a")
    yield("b")
    yield("c")

class TestMisc(unittest.TestCase):

    def test_types(self):
        # just check that the types are defined
        Mapping
        dict
        dict[str, int]
        myName = Name("Stefan", "Wehr")
        list[Name] # just use it
        list[ty] # just use it
        list[ForwardRef('foo')] # just use
        list[PointOrFloat]

    def test_math(self):
        # just check that the functions are defined
        math.sqrt(2)
        math.sin(2)

    def assertTypeError(self, thunk, msg):
        try:
            thunk()
            self.fail("no type error")
        except TypeError as e:
            self.assertEqual(str(e), msg)

    def test_checkEq(self):
        check(1.0000000000000001, 1)

    def test_typechking(self):
       self.assertTypeError(lambda : ForwardRef(1),
            'Forward reference must be a string -- got 1')
