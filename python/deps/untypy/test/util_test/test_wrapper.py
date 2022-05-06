from untypy.util.wrapper import wrap
import unittest

class C:
    def __init__(self, content):
        self.content = content
    def __eq__(self, other):
        if not isinstance(other, C):
            return False
        else:
            return self.content == other.content
    def __repr__(self):
        return f'C({self.content})'
    def __str__(self):
        return self.__repr__()
    def foo(self):
        return 1

class WrapperTests(unittest.TestCase):
    def test_wrapObject(self):
        c1 = C(42)
        c2 = wrap(C(42), {'foo': lambda self: 0})
        self.assertEqual(str(c2), 'C(42)')
        self.assertTrue(c1 == c2)
        self.assertTrue(c2 == c1)
        self.assertTrue(isinstance(c2, C))
        self.assertEqual(c2.foo(), 0)
        self.assertEqual(c1.foo(), 1)

    def test_wrapList(self):
        l = wrap([1,2,3], {'__str__': lambda self: 'XXX'})
        self.assertEqual(repr(l), '[1, 2, 3]')
        self.assertEqual(str(l), 'XXX')
        self.assertTrue(isinstance(l, list))
        acc = []
        for x in l:
            acc.append(x+1)
        self.assertEqual(acc, [2,3,4])
        self.assertEqual([0] + l, [0,1,2,3])
        self.assertEqual(l + [4], [1,2,3,4])
        self.assertTrue(l == [1,2,3])
        self.assertTrue([1,2,3] == l)

    def test_wrapTuple(self):
        l = wrap((1,2,3), {'__str__': lambda self: 'XXX'})
        self.assertEqual(repr(l), '(1, 2, 3)')
        self.assertEqual(str(l), 'XXX')
        self.assertTrue(isinstance(l, tuple))
        acc = []
        for x in l:
            acc.append(x+1)
        self.assertEqual(acc, [2,3,4])
        self.assertEqual((0,) + l, (0,1,2,3))
        self.assertEqual(l + (4,), (1,2,3,4))
        self.assertTrue(l == (1,2,3))
        self.assertTrue((1,2,3) == l)

    def test_wrapString(self):
        l = wrap("123", {'__str__': lambda self: 'XXX'})
        self.assertEqual(repr(l), "'123'")
        self.assertEqual(str(l), 'XXX')
        self.assertTrue(isinstance(l, str))
        acc = []
        for x in l:
            acc.append(x)
        self.assertEqual(acc, ['1', '2', '3'])
        self.assertEqual('0' + l, '0123')
        self.assertEqual(l + '4', '1234')
        self.assertTrue(l == "123")
        self.assertTrue("123" == l)

    def test_wrapDict(self):
        d = wrap({'1': 1, '2': 2, '3': 3}, {'__str__': lambda self: 'YYY', 'foo': lambda self: 11})
        self.assertEqual(repr(d), "{'1': 1, '2': 2, '3': 3}")
        self.assertEqual(str(d), 'YYY')
        self.assertTrue(isinstance(d, dict))
        acc = []
        for x in d:
            acc.append(x)
        self.assertEqual(acc, ['1', '2', '3'])
        self.assertEqual(len(d), 3)
        self.assertTrue(d == {'1': 1, '2': 2, '3': 3})
        self.assertTrue({'1': 1, '2': 2, '3': 3} == d)
        self.assertEqual(d.foo(), 11)

    def test_name(self):
        l = wrap([1,2,3], {}, "NameOfWrapper")
        self.assertEqual(str(type(l)), "NameOfWrapper")
        c = wrap(C(1), {}, "blub")
        self.assertEqual(str(type(c)), "blub")
