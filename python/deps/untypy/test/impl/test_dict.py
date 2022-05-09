import unittest
import collections

# For running with the debugger
#import sys
#sys.path.insert(0, '/Users/swehr/devel/write-your-python-program/python/deps/untypy/')

import untypy
from test.util import DummyExecutionContext
from test.util_test.untypy_test_case import dummy_caller
from untypy.error import UntypyTypeError
from untypy.impl.dummy_delayed import DummyDelayedType


class TestDict(unittest.TestCase):
    def test_equiv_with_builtin_dict(self):
        self.check(str)
        self.check(repr)
        def inPlaceAdd1(l):
            l["foo"] = 3
            (l, len(l))
        self.check(inPlaceAdd1)
        self.check(lambda l: "2" in l)
        self.check(lambda l: "42" in l)
        self.check(lambda l: l["2"])
        self.check(lambda l: l["42"])
        def update(l):
            l.update({"foo": 3})
            (l, len(l))
        self.check(update)
        def update2(l):
            l.update({"foo": 3}, chaos=100)
            (l, len(l))
        self.check(update2)
        def delete(l):
            del l["2"]
            (l, len(l))
        self.check(delete)
        def iter(d):
            acc = []
            for x in d:
                acc.append(x)
            return x
        self.check(iter)
        self.check(lambda d: d.copy())
        self.check(lambda d: d | {"42": 42, "2": 100})
        self.check(lambda d: {"42": 42, "2": 100} | d)
        self.check(lambda d: len(d))
        self.check(lambda d: d.pop("2"))
        self.check(lambda d: d.pop("42", 100))
        self.check(lambda d: d.popitem())
        self.check(lambda d: d.clear())
        self.check(lambda d: d.setdefault("1"))
        self.check(lambda d: d.setdefault("1", 50))
        self.check(lambda d: d.get("1"))
        self.check(lambda d: d.get("1", 50))
        self.check(lambda d: d.get("100"))
        self.check(lambda d: d.get("100", 50))
        self.check(lambda d: d.keys())
        self.check(lambda d: d.items())
        self.check(lambda d: d.values())
        self.check(lambda l: list(reversed(l)))

    def check(self, f):
        l1 = {"1": 1, "2": 2}
        l2 = l1.copy()
        try:
            refRes = f(l1)
        except Exception as e:
            refRes = e
        checker = untypy.checker(lambda ty=dict[str, int]: ty, dummy_caller)
        wrapped = checker(l2)
        self.assertFalse(l2 is wrapped)
        try:
            res = f(wrapped)
        except Exception as e:
            res = e
        if isinstance(refRes, Exception) and isinstance(res, Exception):
            self.assertEqual(str(refRes), str(res))
        elif not isinstance(refRes, Exception) and  not isinstance(res, Exception):
            if isinstance(refRes, collections.abc.ValuesView):
                refRes = list(refRes)
            if isinstance(res, collections.abc.ValuesView):
                res = list(res)
            self.assertEqual(refRes, res)
        else:
            self.fail(f"resRef={refRes}, res={res}")
        self.assertEqual(l1, wrapped)
        self.assertEqual(l1, l2)
