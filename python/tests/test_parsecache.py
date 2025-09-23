import unittest
import parsecache
from parsecache import FunMatcher
import ast

class TestParseCache(unittest.TestCase):

    def test_parseCacheFunDef(self):
        a = parsecache.AST('tests/parsecacheTestData.py')
        assert(a is not None)
        defFoo = a.getFunDef(FunMatcher('foo', 6))
        assert(defFoo is not None)
        self.assertEqual(defFoo.lineno, 6)
        defBar = a.getFunDef(FunMatcher('bar'))
        assert(defBar is not None)
        self.assertEqual(defBar.lineno, 3)
        x = a.getFunDef(FunMatcher('spam')) # conflicting def
        self.assertIsNone(x)
        defSpam = a.getFunDef(FunMatcher('spam', 22))
        assert(defSpam is not None)
        self.assertEqual(defSpam.lineno, 22)
        match defSpam.body[1]:
            case ast.Return(ast.Constant(2)):
                pass
            case stmt:
                self.fail(f'Invalid first statement of spam: {stmt}')
        x = a.getFunDef(FunMatcher('egg'))
        self.assertIsNone(x)

    def test_parseCacheNestedFunDef(self):
        a = parsecache.AST('tests/parsecacheTestData.py')
        assert(a is not None)
        defFoo = a.getFunDef(FunMatcher('foo', 23))
        assert(defFoo is not None)
        self.assertEqual(defFoo.lineno, 23)

    def test_parseCacheMethod(self):
        a = parsecache.AST('tests/parsecacheTestData.py')
        assert(a is not None)
        defFoo = a.getMethodDef('D', FunMatcher('foo', 16))
        assert(defFoo is not None)
        self.assertEqual(defFoo.lineno, 16)

    def test_parseCacheRecordAttr(self):
        a = parsecache.AST('tests/parsecacheTestData.py')
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



