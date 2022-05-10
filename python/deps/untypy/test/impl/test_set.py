import unittest
import collections

# For running with the debugger
#import sys
#sys.path.insert(0, '/Users/swehr/devel/write-your-python-program/python/deps/untypy/')

import untypy
from test.util_test.untypy_test_case import dummy_caller


class TestSet(unittest.TestCase):
    def test_update(self):
        checker = untypy.checker(lambda ty=set[str]: ty, dummy_caller)
        s1 = set(["foo", "bar"])
        s2 = set(["bar", "spam"])
        s3 = s1.copy()
        s4 = s2.copy()
        s3w = checker(s3)
        s4w = checker(s4)
        refRes = s1.update(s2)
        res = s3w.update(s4w)
        self.assertEqual(refRes, res)
        self.assertEqual(s1, s3)
        self.assertEqual(s1, s3w)
        self.assertEqual(s2, s4)
        self.assertEqual(s2, s4w)

    def test_equiv_with_builtin_set(self):
        self.check(str)
        self.check(repr)
        self.check(lambda s: s.add(3))
        self.check(lambda s: s.add(2))
        self.check(lambda s: s.clear())
        self.check(lambda s: s.copy())
        self.check(lambda s: s.discard(1))
        self.check(lambda s: s.discard(3))
        self.check(lambda s: s.pop())
        self.check(lambda s: s.remove(1))
        self.check(lambda s: s.remove(3))
        self.check(lambda s: 1 in s)
        self.check(lambda s: 3 in s)
        self.check(lambda s: len(s))
        self.checkM(lambda s, others: s.difference(*others))
        self.checkM(lambda s, others: s.difference_update(*others))
        self.checkM(lambda s, others: s.symmetric_difference(*others))
        self.checkM(lambda s, others: s.symmetric_difference_update(*others))
        self.checkM(lambda s, others: s.union(*others))
        self.checkM(lambda s, others: s.update(*others))
        self.checkSym(lambda s1, s2: s1.issubset(s2))
        self.checkSym(lambda s1, s2: s1.issuperset(s2))
        self.checkSym(lambda s1, s2: s1.isdisjoint(s2))
        self.checkSym(lambda s1, s2: s1 < s2)
        self.checkSym(lambda s1, s2: s1 <= s2)
        self.checkSym(lambda s1, s2: s1 > s2)
        self.checkSym(lambda s1, s2: s1 >= s2)
        self.checkSym(lambda s1, s2: s1 == s2)
        self.checkSym(lambda s1, s2: s1 != s2)
        self.checkSym(lambda s1, s2: s1 & s2)
        def addAssign(s1, s2): s1 &= s2
        self.checkSym(addAssign)
        self.checkSym(lambda s1, s2: s1 | s2)
        def orAssign(s1, s2): s1 |= s2
        self.checkSym(orAssign)
        self.checkSym(lambda s1, s2: s1 ^ s2)
        def xorAssign(s1, s2): s1 ^= s2
        self.checkSym(xorAssign)
        self.checkSym(lambda s1, s2: s1 - s2)
        self.checkSym(lambda s1, s2: s1 - s2)
        def subAssign(s1, s2): s1 -= s2
        self.checkSym(subAssign)
        def iter(s):
            acc = []
            for x in s:
                acc.append(x)
            return acc
        self.check(iter)

    def _check(self, act1, act2, eqs):
        try:
            refRes = act1()
        except Exception as e:
            refRes = e
        try:
            res = act2()
        except Exception as e:
            res = e
        if isinstance(refRes, Exception) and isinstance(res, Exception):
            self.assertEqual(str(refRes), str(res))
        elif not isinstance(refRes, Exception) and  not isinstance(res, Exception):
            self.assertEqual(refRes, res)
        else:
            self.fail(f"resRef={refRes}, res={res}")
        for (x, y) in eqs:
            self.assertEqual(x, y)

    def check(self, f):
        l1 = set([1,2])
        l2 = l1.copy()
        checker = untypy.checker(lambda ty=set[int]: ty, dummy_caller)
        wrapped = checker(l2)
        self.assertFalse(l2 is wrapped)
        self._check(lambda: f(l1), lambda: f(wrapped), [(l1, wrapped), (l1, l2)])

    def checkSym(self, f):
        s1 = None
        s2 = None
        s3 = None
        s4 = None
        s3w = None
        s4w = None
        eqs = None
        def setup():
            nonlocal s1,s2,s3,s4,s3w,s4w,eqs
            s1 = set(["foo", "bar"])
            s2 = set(["bar", "spam"])
            checker = untypy.checker(lambda ty=set[str]: ty, dummy_caller)
            s3 = s1.copy()
            s4 = s2.copy()
            s3w = checker(s3)
            s4w = checker(s4)
            eqs = [(s1, s3), (s2, s4), (s1, s3w), (s2, s4w)]
        setup()
        self._check(lambda: f(s1, s2), lambda: f(s3w, s4w), eqs)
        setup()
        self._check(lambda: f(s2, s1), lambda: f(s4w, s3w), eqs)
        setup()
        self._check(lambda: f(s1, s2), lambda: f(s3, s4w), eqs)
        setup()
        self._check(lambda: f(s2, s1), lambda: f(s4w, s3), eqs)
        setup()
        self._check(lambda: f(s1, s2), lambda: f(s3w, s4), eqs)
        setup()
        self._check(lambda: f(s2, s1), lambda: f(s4, s3w), eqs)

    def checkM(self, f):
        s1 = None
        s2 = None
        s3 = None
        s4 = None
        s5 = None
        s6 = None
        s4w = None
        s5w = None
        s6w = None
        eqs = None
        def setup():
            nonlocal s1,s2,s3,s4,s5,s6,s4w,s5w,s6w,eqs
            s1 = set(["foo", "bar"])
            s2 = set(["bar", "spam"])
            s3 = set(["foo", "egg"])
            checker = untypy.checker(lambda ty=set[str]: ty, dummy_caller)
            s4 = s1.copy()
            s5 = s2.copy()
            s6 = s3.copy()
            s4w = checker(s4)
            s5w = checker(s5)
            s6w = checker(s6)
            eqs = [(s1, s4), (s1, s4w), (s2, s5), (s2, s5w), (s3, s6), (s3, s6w)]
        setup()
        self._check(lambda: f(s1, [s2]), lambda: f(s4w, [s5w]), eqs)
        setup()
        self._check(lambda: f(s1, [s2]), lambda: f(s4w, [s5]), eqs)
        setup()
        self._check(lambda: f(s1, [s2]), lambda: f(s4, [s5w]), eqs)
        setup()
        self._check(lambda: f(s1, [s2,s3]), lambda: f(s4w, [s5w, s6w]), eqs)
        setup()
        self._check(lambda: f(s1, [s2,s3]), lambda: f(s4w, [s5, s6w]), eqs)
        setup()
        self._check(lambda: f(s1, [s2,s3]), lambda: f(s4, [s5w, s6]), eqs)
