# Test data

def bar():
    pass

def foo():
    pass

class C:
    x: int
    y: str

class D:
    x: int
    z: str

import unittest
import parsecache

class TestParseCache(unittest.TestCase):

    def test_parseCacheFunDef(self):
        a = parsecache.getAST('tests/test_parsecache.py')
        assert(a is not None)
        defFoo = a.getFunDef('foo')
        assert(defFoo is not None)
        self.assertEqual(defFoo.lineno, 6)
        defBar = a.getFunDef('bar')
        assert(defBar is not None)
        self.assertEqual(defBar.lineno, 3)
        x = a.getFunDef('spam')
        self.assertIsNone(x)

    def test_parseCacheRecordAttr(self):
        a = parsecache.getAST('tests/test_parsecache.py')
        assert(a is not None)

        # Test getting attributes from class C
        attrX_C = a.getRecordAttr('C', 'x')
        assert(attrX_C is not None)
        self.assertEqual(attrX_C.lineno, 10)

        attrY_C = a.getRecordAttr('C', 'y')
        assert(attrY_C is not None)
        self.assertEqual(attrY_C.lineno, 11)

        # Test getting attributes from class D
        attrX_D = a.getRecordAttr('D', 'x')
        assert(attrX_D is not None)
        self.assertEqual(attrX_D.lineno, 14)

        attrZ_D = a.getRecordAttr('D', 'z')
        assert(attrZ_D is not None)
        self.assertEqual(attrZ_D.lineno, 15)

        # Test non-existent attribute
        nonExistent = a.getRecordAttr('C', 'z')
        self.assertIsNone(nonExistent)

        # Test non-existent class
        nonExistentClass = a.getRecordAttr('NonExistentClass', 'x')
        self.assertIsNone(nonExistentClass)



