from writeYourProgram import *
import unittest
from testSample import *

setDieOnCheckFailures(True)

def incByOne(x: int) -> int:
    return x + 1

def incByOneWrong(x: int) -> str:
    return x + 1

def noResult():
    return 1

def takeFloat(f: float) -> float:
    return f

def consumeSequence(s: Sequence[str]):
    pass

def justUseIterable(i: Iterable[int]):
    pass

def consumeIterable(i: Iterable[int]):
    for x in i:
        pass

def consumeList(l: List[int]):
    pass

def consumeDict(d: Dict[str, int]):
    pass

def myMap(l: List[int], fun: Callable[[int], str]) -> List[str]):
    return [fun(x) for x in l]

def strId(x: str) -> str:
    return x

PointOrFloat = Mixed(Point, float)

def getPoint(pf: PointOrFloat) -> Point:
    if Point.isSome(pf):
        return pf
    else:
        return Point.make(pf, pf)

class TestTypeCheck(unittest.TestCase):
    def assertTypeError(self, msg, closure):
        with self.assertRaises(TypeError) as ctx:
            closure()
        exc = ctx.exception
        self.assertEqual(msg, str(exc))

    def test_funTypeCheck(self):
        incByOne(42)
        self.assertTypeError(
            "Funktion incByOne erwartet als ersten Parameter ein int kein str",
            lambda: incByOne("Stefan")
        )
        self.assertTypeError(
            "Funktion incByOne erwartet als ersten Parameter ein int kein float",
            lambda: incByOne(1.0)
        )
        takeFloat(1.0)
        self.assertTypeError(
            "Funktion takeFloat erwartet als ersten Parameter ein float kein int",
            lambda: takeFloat(1)
        )
        self.assertTypeError(
            "Funktion incByOneWrong soll ein int zurückgeben, liefert aber ein str"
            lambda: incByOneWrong(1)
        )
        self.assertTypeError(
            "Funktion noResult soll kein Ergebnis zurückgeben, liefert aber ein int"
            lambda: noResult
        )

    def test_mixedTypeCheck(self):
        p = Point.make(3.0, 1.0)
        self.assertTrue(p is getPoint(p))
        self.assertEqual(Point.make(1.0, 1.0), 1.0)
        self.assertTypeError(
            "Funktion getPoint erwartet als ersten Parameter ein PointOrFloat kein int",
            lambda: getPoint(1)
        )

    def test_recordTypeCheck(self):
        p = Point.make(3.0, 1.0)
        self.assertTypeError(
            "Funktion Point.make erwartet als zweiten Parameter ein float kein int",
            lambda: Point.make(3.0, 1)
        )
        self.assertTypeError(
            "Funktion Point.make erwartet als ersten Parameter ein float kein int",
            lambda: Point.make(3, 1.0)
        )
        Circle.make(p, 9.0)
        self.assertTypeError(
            "Funktion Circle.make erwartet als ersten Parameter ein Point kein int",
            lambda: Point.make(3, 1.0)
        )

    def test_listTypeCheck(self):
        consumeList([])
        consumeList([1])
        self.assertTypeError(
            "Funktion consumeList erwartet als ersten Parameter ein List[int] kein List[float]",
            lambda: consumeList([1.0])
        )

    def test_sequenceTypeCheck(self):
        consumeSequence(["1"])
        consumeSequence("foo")
        consumeSequence(("1", "2", "3"))
        self.assertTypeError(
            "Funktion consumeSequence erwartet als ersten Parameter ein Sequence[str] kein List[int]",
            lambda: consumeSequence([1])
        )

    def test_iterableTypeCheck(self):
        justUseIterable(["1"]) # type errors are detected on iteration
        consumeIterable([])
        consumeIterable([1,2,3])
        self.assertTypeError(
            "Funktion consumeIterable erwartet als ersten Parameter ein Iterable[Int], " +
            "das 2. Element des Iterable ist aber ein str"
            lambda: consumeIterable([1, "stefan"])
        )

    def test_higherOrderFunTypeCheck(self):
        origList = [1, 2, 3]
        l = myMap(origList, str)
        self.assertEqal(l, [1, 2, 3])
        self.assertTypeError(
            "Funktion myMap erwartet als zweiten Parameter ein Callable[[int], str], " +
            "die als zweiten Parameter übergebene Funktion float hat aber ein float " +
            "zurückgegeben."
            lambda: myMap([1, 2, 3], float)
        )
        self.assertTypeError(
            "Funktion myMap erwartet als zweiten Parameter ein Callable[[int], str], " +
            "die als zweiten Parameter übergebene Funktion float benötigt aber ein str " +
            "als Eingabe."
            lambda: myMap([1, 2, 3], strId)
        )

    def test_dictTypeCheck(self):
        pass # FIXME

    def test_objTypeCheck(self):
        pass # FIXME
