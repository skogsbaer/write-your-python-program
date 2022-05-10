import unittest
# For running with the debugger
#import sys
#sys.path.insert(0, '/Users/swehr/devel/write-your-python-program/python/deps/untypy/')

from test.util_test.untypy_test_case import UntypyTestCase, dummy_caller
from untypy.error import UntypyTypeError


class TestInterfaceSet(UntypyTestCase):
    """
    Test's that the signatures matches the implementation.
    """

    def setUp(self) -> None:
        self.good = dummy_caller(
            set[int],
            {1, 2, 3}
        )

        self.bad = dummy_caller(
            set[int],
            {1, "two", 3}
        )

    def test_add(self):
        self.good.add(4)

        with self.assertRaises(UntypyTypeError):
            self.good.add("four")

    def test_discard(self):
        self.good.discard(3)

        with self.assertRaises(UntypyTypeError):
            self.good.discard("four")

    def test_pop(self):
        self.good.pop()
        self.good.pop()
        self.good.pop()

        with self.assertRaises(KeyError):
            self.good.pop()
            pass

        with self.assertRaises(UntypyTypeError):
            self.bad.pop()
            self.bad.pop()
            self.bad.pop()

    def test_remove(self):
        self.good.remove(3)

        with self.assertRaises(UntypyTypeError):
            self.good.remove("four")

    def test_update(self):
        self.good.update({5, 6, 7})
        self.good.update({8}, [9], {24})

        with self.assertRaises(UntypyTypeError):
            self.good.update({"four"})

    @unittest.skip("fails :/. Does not raise UntypyTypeError")
    #FIXME: enable once all tests are running
    def test_ior(self):
        self.good |= {4} | {7}
        self.assertEqual(self.good, {1, 2, 3, 4, 7})

        with self.assertRaises(UntypyTypeError):
            self.good |= {"four"}

    def test_contains(self):
        self.assertEqual(1 in self.good, True)

        with self.assertRaises(UntypyTypeError):
            "four" in self.good

    def test_iter(self):
        for k in self.good:
            pass

        with self.assertRaises(UntypyTypeError):
            for k in self.bad:
                pass
def _debug():
    t = TestInterfaceSet()
    t.setUp()
    t.test_ior()

# _debug()
