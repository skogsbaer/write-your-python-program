import unittest

import untypy
from untypy.error import UntypyTypeError, Location


def dummy_caller_2(ch, arg):
    return ch(arg)


# Sets up callstack so that this function is blamed for creation.
# untypy.checker uses the function that called the function that
# invokes the checker.
def dummy_caller(ch, arg):
    return dummy_caller_2(ch, arg)


class TestInterfaceDict(unittest.TestCase):
    """
    Test's that the signatures match the implementation.
    """

    def setUp(self) -> None:
        ch1 = untypy.checker(lambda: dict[int, str], dummy_caller)

        # A: No Errors
        self.good = dummy_caller(ch1, {
            1: "one",
            2: "two",
            3: "three",
        })

        # B: Value error on 2
        self.valerr = dummy_caller(ch1, {
            1: "one",
            2: 2,
            3: "three",
        })

        # B: Key error on 2
        self.keyerr = dummy_caller(ch1, {
            1: "one",
            "two": 2,
            3: "three",
        })

    def assertBlame(self, cm, caller):
        self.assertTrue(cm.exception.last_responsable() in Location.from_code(caller))

    def test_get(self):
        self.assertEqual(self.good.get(1), "one")
        self.assertEqual(self.good.get(4), None)
        self.assertEqual(self.good.get(4, "four"), "four")

        with self.assertRaises(UntypyTypeError) as cm:
            # 42 must be str
            self.good.get(1, 42)
        self.assertBlame(cm, TestInterfaceDict.test_get)

        with self.assertRaises(UntypyTypeError) as cm:
            # key must be int
            self.good.get("two")
        self.assertBlame(cm, TestInterfaceDict.test_get)

        with self.assertRaises(UntypyTypeError) as cm:
            # value err
            self.valerr.get(2)
        self.assertBlame(cm, dummy_caller)

    def test_items(self):
        self.assertEqual(
            list(self.good.items()),
            [(1, "one"), (2, "two"), (3, "three")]
        )

        with self.assertRaises(UntypyTypeError) as cm:
            list(self.keyerr.items())

        with self.assertRaises(UntypyTypeError) as cm:
            list(self.valerr.items())

    def test_keys(self):
        self.assertEqual(
            list(self.good.keys()),
            [1, 2, 3]
        )

        with self.assertRaises(UntypyTypeError):
            list(self.keyerr.keys())

        # values stay unchecked
        self.assertEqual(
            list(self.valerr.keys()),
            [1, 2, 3]
        )

    def test_pop(self):
        self.assertEqual(self.good.pop(1), "one")
        self.assertEqual(self.good.pop(4), None)
        self.assertEqual(self.good.pop(4, "four"), "four")

        with self.assertRaises(UntypyTypeError):
            self.good.pop("one")

        with self.assertRaises(UntypyTypeError):
            self.valerr.pop(2)

    def test_popitem(self):
        self.assertEqual(self.good.popitem(), (3, "three"))
        self.assertEqual(self.good.popitem(), (2, "two"))
        self.assertEqual(self.good.popitem(), (1, "one"))

        with self.assertRaises(KeyError):
            self.good.popitem()

        self.assertEqual(self.keyerr.popitem(), (3, "three"))
        with self.assertRaises(UntypyTypeError):
            self.keyerr.popitem()

        self.assertEqual(self.valerr.popitem(), (3, "three"))
        with self.assertRaises(UntypyTypeError):
            self.valerr.popitem()

    def test_setdefault(self):
        self.assertEqual(self.good.setdefault(1, "xxx"), "one")

        with self.assertRaises(UntypyTypeError):
            # Untypy does not support setdefault w/o default=XXX
            # https://github.com/skogsbaer/write-your-python-program/issues/19
            self.good.setdefault(5)

        self.assertEqual(self.good.setdefault(4, "four"), "four")
        self.assertEqual(self.good.get(4), "four")

        with self.assertRaises(UntypyTypeError):
            # 42 must be str
            self.good.setdefault(4, 42)

        with self.assertRaises(UntypyTypeError):
            self.valerr.setdefault(2)

    def test_values(self):
        self.assertEqual(
            list(self.good.values()),
            ["one", "two", "three"]
        )

        with self.assertRaises(UntypyTypeError):
            # This failes also, but I don't know why.
            # However the keys violate the annotation,
            # So this is fine.
            self.assertEqual(
                list(self.keyerr.values()),
                ["one", "two", "three"]
            )

        with self.assertRaises(UntypyTypeError):
            list(self.valerr.values())

    def test_contains(self):
        self.assertTrue(1 in self.good)
        self.assertFalse(4 in self.good)

        with self.assertRaises(UntypyTypeError):
            # Cannot be in if Key : str.
            "42" in self.good

    def test_delitem(self):
        del self.good[1]

        with self.assertRaises(KeyError):
            del self.good[4]

        with self.assertRaises(UntypyTypeError):
            del self.good["four"]

        self.assertEqual(self.good, {2: "two", 3: "three"})

    def test_iter(self):
        for k in self.good:
            pass

        for k in self.valerr:
            pass

        with self.assertRaises(UntypyTypeError):
            for k in self.keyerr:
                pass

    def test_len(self):
        self.assertEqual(len(self.good), 3)

    def test_reversed(self):
        self.assertEqual(list(reversed(self.good)), [3, 2, 1])
        self.assertEqual(list(reversed(self.valerr)), [3, 2, 1])

        with self.assertRaises(UntypyTypeError):
            list(reversed(self.keyerr))

    def test_getitem(self):
        self.assertEqual(self.good[1], "one")

        with self.assertRaises(UntypyTypeError):
            self.good["two"]

        with self.assertRaises(UntypyTypeError):
            self.valerr[2]

    def test_setiem(self):
        self.good[1] = "not one"

        with self.assertRaises(UntypyTypeError):
            # key err
            self.good["key"] = "one"

        with self.assertRaises(UntypyTypeError):
            # val err
            self.good[4] = 44
