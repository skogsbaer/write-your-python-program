import unittest
from writeYourProgram import *
import testSample

setDieOnCheckFailures(True)

class C:
    pass

def abcGenerator():
    yield("a")
    yield("b")
    yield("c")

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

    def assertType(self, ty, yesVal, noVal=None):
        self.assertTrue(isType(ty))
        self.assertTrue(hasType(ty, yesVal))
        if noVal is not None:
            self.assertFalse(hasType(ty, noVal))

    def test_isType(self):
        self.assertType(int, 2, '2')
        #self.assertType(complex, 2, '2')
        self.assertType(str, '2', 2)
        self.assertType(float, 2.3, 'foo')
        self.assertType(List[float], [2.3, 1.0], 'foo')
        self.assertType(List, [1, 'bar'], ('foo',))
        self.assertType(list, [1, 'bar'], ('foo',))
        self.assertType(tuple, (1, 'bar'), [1])
        self.assertType(dict, {1: 'foo'}, [])
        self.assertType(Tuple, (1, 'bar'), [])
        self.assertType(Tuple[str, ...], ('bar',), [])
        self.assertType(Tuple[int, Tuple[List[int], str]], (1, ([1], 'foo')), 'foo')
        self.assertType(Dict, {1: 'foo'}, [])
        self.assertType(Dict[str, List[int]], {'1': [1]}, [])
        self.assertType(Mapping, {'1': [1]}, [])
        self.assertType(Mapping[str, List[int]], {'1': [1]}, [])
        self.assertType(C, C(), 1)
        self.assertType(None, None, 1)
        self.assertType(Any, 'foobar')
        self.assertType(Iterable, [1,2], 1)
        self.assertType(Iterable[int], [1,2], 1)
        self.assertType(Iterator, reversed([1]), 1)
        self.assertType(Iterator[int], reversed([1]), 1)
        self.assertType(Generator, abcGenerator(), 1)
        self.assertType(Generator[int, float, str], abcGenerator(), 1)
        self.assertType(Sequence, [1,2,3], 1)
        self.assertType(Sequence[int], [1,2,3], 1)
        self.assertType(Set, set([1]), 1)
        self.assertType(Set[int], set([1]), 1)
        self.assertType(Optional, None)
        self.assertType(Optional[int], 1)
        self.assertType(Callable, lambda x: x, 1)
        self.assertType(Callable[[int, str], int], lambda x,y: x, 1)
        self.assertType(testSample.Point, testSample.Point(1,2), 1)
        self.assertType(testSample.Circle, testSample.Circle(testSample.Point(1,2), 3.1), 1)
        self.assertType(testSample.Shape, testSample.Circle(testSample.Point(1,2), 3.1), 1)
        self.assertType(testSample.Drink, 'Tea', 'foo')

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

