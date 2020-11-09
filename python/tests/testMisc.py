import unittest
from writeYourProgram import *
import testSample

setDieOnCheckFailures(True)

class TestMixed(unittest.TestCase):

    def test_types(self):
        # just check that the types are defined
        Mapping
        Dict
        Dict[str, int]

    def test_math(self):
        # just check that the functions are defined
        math.sqrt(2)
        math.sin(2)

    def test_isType(self):
        self.assertTrue(isType(int))
        self.assertTrue(isType(str))
        self.assertTrue(isType(float))
        self.assertTrue(isType(testSample.Point))
        self.assertTrue(isType(testSample.Shape))
        self.assertTrue(isType(testSample.Drink))

    def assertTypeError(self, thunk, msg):
        try:
            thunk()
        except TypeError as e:
            self.assertEqual(str(e), msg)

    def test_typechking(self):
        self.assertTypeError(lambda : Enum('Stefan', 1),
            'Das 2. Argument von Enum ist kein String sondern 1.')
        self.assertTypeError(lambda : Record(1, 'f', int),
            'Das 1. Argument von Record ist kein String sondern 1.')
        self.assertTypeError(lambda : Record('R', 1, int),
            'Das 2. Argument von Record ist kein String sondern 1. '\
            'Es wird aber der Name einer Eigenschaft erwartet.')
        self.assertTypeError(lambda : Record('R', 'x', 'foo'),
            'Das 3. Argument von Record ist kein Typ sondern \'foo\'. ' \
            'Es wird aber der Typ der Eigenschaft x erwartet.')
        self.assertTypeError(lambda : Mixed('R', Enum('1', '2')),
            'Das 1. Argument von Mixed ist kein Typ sondern \'R\'.')
        self.assertTypeError(lambda : DefinedLater(1),
            'Das 1. Argument von DefinedLater ist kein String sondern 1.')

