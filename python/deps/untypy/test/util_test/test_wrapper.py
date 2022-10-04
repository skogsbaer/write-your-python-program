from untypy.util.wrapper import wrap
import unittest
import collections

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
        self.assertEqual(3, len(l))
        l.append(4)
        self.assertEqual(4, len(l))
        self.assertEqual([1,2,3,4], l)
        f = l.append
        flag = False
        def myAppend(x):
            nonlocal flag
            flag = True
            f(x)
        setattr(l, 'append', myAppend)
        l.append(5)
        self.assertEqual(5, len(l))
        self.assertEqual([1,2,3,4,5], l)
        self.assertTrue(flag)

    def test_wrapList2(self):
        # This is what happens in the protocol checker: the function is called on the original
        # value
        orig = [1,2,3]
        l = wrap(orig, {'append': lambda self, x: orig.append(x)})
        self.assertTrue([1,2,3] == l)
        self.assertEqual(3, len(l))
        l.append(4)
        self.assertEqual(4, len(l))
        self.assertEqual([1,2,3,4], l)

    def _test_api_complete(self, obj, ignore=[]):
        wrapped = wrap(obj, {})
        expectedModule = 'untypy.util.wrapper'
        blacklist = ['__class__', '__delattr__', '__class_getitem__', '__dict__', '__dir__',
                     '__doc__', '__extra__', '__format__', '__getattribute__', '__init__',
                     '__init_subclass__', '__module__', '__setattr__', '__subclasshook__',
                     '__weakref__', '__wrapped__', '_DictWrapper__marker', '__setstate__',
                     '__getstate__'
                     ] + ignore
        for x in dir(wrapped):
            if x in blacklist: continue
            m = getattr(wrapped, x)
            if not hasattr(m, '__module__'):
                self.fail(f'Attribute {x} not defined')
            elif m.__module__ != expectedModule:
                self.fail(f'Attrribute {x} not defined in {expectedModule}')

    def test_list_api_complete(self):
        self._test_api_complete([])

    def test_set_api_complete(self):
        self._test_api_complete(set())

    def test_dict_api_complete(self):
        self._test_api_complete({}, ignore=['fromkeys'])

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
        self.assertEqual(d.copy(), {'1': 1, '2': 2, '3': 3})

    def test_wrapViews(self):
        d = {'1': 1, '2': 2}
        # keys
        self.assertTrue(isinstance(d.keys(), collections.abc.KeysView))
        kv = wrap(d.keys(), {})
        self.assertTrue(isinstance(kv, collections.abc.KeysView))
        acc = []
        for x in kv:
            acc.append(x)
        self.assertEqual(['1','2'], acc)
        # items
        iv = wrap(d.items(), {})
        self.assertTrue(isinstance(iv, collections.abc.ItemsView))
        acc = []
        for x in iv:
            acc.append(x)
        self.assertEqual([('1', 1),('2', 2)], acc)
        # values
        vv = wrap(d.values(), {})
        self.assertTrue(isinstance(vv, collections.abc.ValuesView))
        acc = []
        for x in vv:
            acc.append(x)
        self.assertEqual([1,2], acc)

    def test_name(self):
        l = wrap([1,2,3], {}, "NameOfWrapper")
        self.assertEqual(str(type(l)), "<class 'NameOfWrapper'>")
        c = wrap(C(1), {}, "blub")
        self.assertEqual(str(type(c)), "<class 'test.util_test.test_wrapper.blub'>")
