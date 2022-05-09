import unittest
from typing import Iterable

from test.util import DummyExecutionContext, DummyDefaultCreationContext
from test.util_test.untypy_test_case import dummy_caller
import untypy
from untypy.error import UntypyTypeError
from untypy.impl.dummy_delayed import DummyDelayedType
from untypy.impl.tuple import TupleFactory


class TestStr(unittest.TestCase):

    def test_equiv_with_builtin_tuple(self):
        self.check(str)
        self.check(repr)
        self.check(lambda l: "foo" + l)
        self.check(lambda l: l + "foo")
        self.check(lambda l: 4 * l)
        self.check(lambda l: l * 3)
        self.check(lambda l: "sp" in l)
        self.check(lambda l: "xxx" in l)
        self.check(lambda l: l[0])
        self.check(lambda l: l[-2])
        self.check(lambda l: l[1:2])
        def iter(l):
            acc = []
            for x in l:
                acc.append(l)
            return acc
        self.check(iter)
        self.check(lambda l: len(l))
        self.check(lambda l: l.count("s"))
        self.check(lambda l: sorted(l))
        self.check(lambda l: list(reversed(l)))
        # ==
        self.check(lambda l: l == "spam")
        self.check(lambda l:  "spam" == l)
        self.check2(lambda l1, l2: l1 == l2)
        self.check2(lambda l1, l2: l2 == l1)
        # !=
        self.check(lambda l: l != "spam")
        self.check(lambda l:  "spam" != l)
        self.check2(lambda l1, l2: l1 != l2)
        self.check2(lambda l1, l2: l2 != l1)
        # <
        self.check(lambda l: l < "egg")
        self.check(lambda l:  "egg" < l)
        self.check2(lambda l1, l2: l1 < l2)
        self.check2(lambda l1, l2: l2 < l1)
        # <=
        self.check(lambda l: l <= "egg")
        self.check(lambda l:  "egg" <= l)
        self.check2(lambda l1, l2: l1 <= l2)
        self.check2(lambda l1, l2: l2 <= l1)
        # >
        self.check(lambda l: l > "egg")
        self.check(lambda l:  "egg" > l)
        self.check2(lambda l1, l2: l1 > l2)
        self.check2(lambda l1, l2: l2 > l1)
        # >=
        self.check(lambda l: l >= "egg")
        self.check(lambda l:  "egg" >= l)
        self.check2(lambda l1, l2: l1 >= l2)
        self.check2(lambda l1, l2: l2 >= l1)

    def check(self, f):
        l1 = "spam"
        refRes = f(l1)
        checker = untypy.checker(lambda ty=Iterable[str]: ty, dummy_caller)
        wrapped = checker(l1)
        self.assertFalse(l1 is wrapped)
        res = f(wrapped)
        self.assertEqual(l1, wrapped)
        self.assertEqual(refRes, res)

    def check2(self, f):
        self.check21(f)
        self.check22(f)

    def check21(self, f):
        l1 = "spam"
        refRes11 = f(l1, l1)
        checker = untypy.checker(lambda ty=Iterable[str]: ty, dummy_caller)
        wrapped1 = checker(l1)
        self.assertFalse(l1 is wrapped1)
        res11 = f(wrapped1, wrapped1)
        self.assertEqual(refRes11, res11)

    def check22(self, f):
        l1 = "spam"
        l2 = "spa"
        refRes12 = f(l1, l2)
        checker = untypy.checker(lambda ty=Iterable[str]: ty, dummy_caller)
        wrapped1 = checker(l1)
        wrapped2 = checker(l2)
        self.assertFalse(l1 is wrapped1)
        self.assertFalse(l2 is wrapped2)
        res12 = f(wrapped1, wrapped2)
        self.assertEqual(refRes12, res12)
