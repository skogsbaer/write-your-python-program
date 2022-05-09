import unittest
from typing import Tuple

from test.util import DummyExecutionContext, DummyDefaultCreationContext
from test.util_test.untypy_test_case import dummy_caller
import untypy
from untypy.error import UntypyTypeError
from untypy.impl.dummy_delayed import DummyDelayedType
from untypy.impl.tuple import TupleFactory


class TestTuple(unittest.TestCase):

    def test_wrap_lower_case(self):
        checker = TupleFactory().create_from(tuple[int, str], DummyDefaultCreationContext())
        res = checker.check_and_wrap((1, "2"), DummyExecutionContext())
        self.assertEqual((1, "2"), res)

    def test_wrap_upper_case(self):
        checker = TupleFactory().create_from(Tuple[int, str], DummyDefaultCreationContext())
        res = checker.check_and_wrap((1, "2"), DummyExecutionContext())
        self.assertEqual((1, "2"), res)

    def test_not_a_tuple(self):
        checker = TupleFactory().create_from(tuple[int, str], DummyDefaultCreationContext())

        with self.assertRaises(UntypyTypeError) as cm:
            res = checker.check_and_wrap(1, DummyExecutionContext())

        (t, i) = cm.exception.next_type_and_indicator()
        i = i.rstrip()

        self.assertEqual(t, "tuple[int, str]")
        self.assertEqual(i, "^^^^^^^^^^^^^^^")

        # This DummyExecutionContext is responsable
        self.assertEqual(cm.exception.last_responsable().file, "dummy")

    def test_negative(self):
        checker = TupleFactory().create_from(tuple[int, str], DummyDefaultCreationContext())

        with self.assertRaises(UntypyTypeError) as cm:
            res = checker.check_and_wrap((1, 2), DummyExecutionContext())

        (t, i) = cm.exception.next_type_and_indicator()
        i = i.rstrip()

        self.assertEqual(t, "tuple[int, str]")
        self.assertEqual(i, "           ^^^")

        # This DummyExecutionContext is responsable
        self.assertEqual(cm.exception.last_responsable().file, "dummy")

    def test_negative_delayed(self):
        checker = TupleFactory().create_from(tuple[int, DummyDelayedType], DummyDefaultCreationContext())

        res = checker.check_and_wrap((1, 2), DummyExecutionContext())
        with self.assertRaises(UntypyTypeError) as cm:
            res[1].use()

        (t, i) = cm.exception.next_type_and_indicator()
        i = i.rstrip()

        self.assertEqual(t, "tuple[int, DummyDelayedType]")
        self.assertEqual(i, "           ^^^^^^^^^^^^^^^^")

        # This DummyExecutionContext is responsable
        self.assertEqual(cm.exception.last_responsable().file, "dummy")

    def test_equiv_with_builtin_tuple(self):
        self.check(str)
        self.check(repr)
        self.check(lambda l: (42, 5) + l)
        self.check(lambda l: l + (42, 5))
        self.check(lambda l: 4 * l)
        self.check(lambda l: l * 3)
        self.check(lambda l: 2 in l)
        self.check(lambda l: 42 in l)
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
        self.check(lambda l: l.count(1))
        self.check(lambda l: sorted(l))
        self.check(lambda l: list(reversed(l)))
        # ==
        self.check(lambda l: l == (1,4,2,1))
        self.check(lambda l:  (1,4,2,1) == l)
        self.check2(lambda l1, l2: l1 == l2)
        self.check2(lambda l1, l2: l2 == l1)
        # !=
        self.check(lambda l: l != (1,4,2,1))
        self.check(lambda l:  (1,4,2,1) != l)
        self.check2(lambda l1, l2: l1 != l2)
        self.check2(lambda l1, l2: l2 != l1)
        # <
        self.check(lambda l: l < (1,4,2))
        self.check(lambda l:  (1,4,1) < l)
        self.check2(lambda l1, l2: l1 < l2)
        self.check2(lambda l1, l2: l2 < l1)
        # <=
        self.check(lambda l: l <= (1,4,2))
        self.check(lambda l:  (1,4,1) <= l)
        self.check2(lambda l1, l2: l1 <= l2)
        self.check2(lambda l1, l2: l2 <= l1)
        # >
        self.check(lambda l: l > (1,4,2))
        self.check(lambda l:  (1,4,1) > l)
        self.check2(lambda l1, l2: l1 > l2)
        self.check2(lambda l1, l2: l2 > l1)
        # >=
        self.check(lambda l: l >= (1,4,2))
        self.check(lambda l:  (1,4,1) >= l)
        self.check2(lambda l1, l2: l1 >= l2)
        self.check2(lambda l1, l2: l2 >= l1)

    def check(self, f):
        l1 = (1, 4, 2, 1)
        refRes = f(l1)
        checker = untypy.checker(lambda ty=tuple[int,...]: ty, dummy_caller)
        wrapped = checker(l1)
        res = f(wrapped)
        self.assertEqual(l1, wrapped)
        self.assertEqual(refRes, res)

    def check2(self, f):
        self.check21(f)
        self.check22(f)

    def check21(self, f):
        l1 = (1, 4, 2, 1)
        refRes11 = f(l1, l1)
        checker = untypy.checker(lambda ty=tuple[int,...]: ty, dummy_caller)
        wrapped1 = checker(l1)
        res11 = f(wrapped1, wrapped1)
        self.assertEqual(refRes11, res11)

    def check22(self, f):
        l1 = (1, 4, 2, 1)
        l2 = (1, 4, 1)
        refRes12 = f(l1, l2)
        checker = untypy.checker(lambda ty=tuple[int, ...]: ty, dummy_caller)
        wrapped1 = checker(l1)
        wrapped2 = checker(l2)
        res12 = f(wrapped1, wrapped2)
        self.assertEqual(refRes12, res12)
