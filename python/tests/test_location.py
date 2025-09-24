import unittest
import os
import location
from locationTestData import *

class TestLocation(unittest.TestCase):

    def assertLocation(self,
                       loc: location.Loc | None,
                       startLine: int, startCol: int, endLine: int, endCol: int):
        if loc is None:
            self.fail("loc is None")
        self.assertEqual('locationTestData.py', os.path.basename(loc.filename))
        self.assertEqual(startLine, loc.startLine)
        self.assertEqual(endLine, loc.endLine)
        self.assertEqual(startCol, loc.startCol)
        self.assertEqual(endCol, loc.endCol)

    def test_locationOfArgument(self):
        fi = myFun("foo", [1,2,3])
        loc = location.locationOfArgument(fi, 0)
        colNo = 21
        self.assertLocation(loc, lineNoMyFunCall,
                            colNo,
                            lineNoMyFunCall,
                            colNo + len("blub") + 2)

    def test_StdCallableInfo(self):
        info = location.StdCallableInfo(myFun, 'function')
        self.assertEqual('locationTestData.py', os.path.basename(info.file))
        resultLoc = info.getResultTypeLocation()
        argLoc = info.getParamSourceLocation("depth")
        self.assertLocation(resultLoc, lineNoMyFunDef, 49, lineNoMyFunDef, 66)
        self.assertLocation(argLoc, lineNoMyFunDef, 32, lineNoMyFunDef, 42)

    def test_StdCallableInfo2(self):
        info = location.StdCallableInfo(myFunNoResult, 'function')
        self.assertEqual('locationTestData.py', os.path.basename(info.file))
        resultLoc = info.getResultTypeLocation()
        self.assertIsNone(resultLoc)
        argLoc = info.getParamSourceLocation("depth")
        self.assertLocation(argLoc, lineNoMyFunNoResultDef, 18, lineNoMyFunNoResultDef, 28)

    def test_StdCallableInfoSub(self):
        sub = Sub()
        info = location.StdCallableInfo(sub.foo, location.ClassMember('method', 'Sub'))
        self.assertEqual('locationTestData.py', os.path.basename(info.file))
        argLoc = info.getParamSourceLocation("y")
        self.assertLocation(argLoc, lineFooSub, 18, lineFooSub, 24)

    def test_StdCallableInfoBase(self):
        b = Base()
        info = location.StdCallableInfo(b.foo, location.ClassMember('method', 'Base'))
        self.assertEqual('locationTestData.py', os.path.basename(info.file))
        argLoc = info.getParamSourceLocation("y")
        self.assertLocation(argLoc, lineFooBase, 26, lineFooBase, 32)

    def test_RecordConstructorInfo(self):
        info = location.RecordConstructorInfo(TestRecord)
        # Test getting parameter source locations with precise line/column numbers
        argLocX = info.getParamSourceLocation("x")
        argLocY = info.getParamSourceLocation("y")
        argLocZ = info.getParamSourceLocation("z")
        self.assertLocation(argLocX, lineNoTestRecordDef + 1, 4, lineNoTestRecordDef + 1, 10)
        self.assertLocation(argLocY, lineNoTestRecordDef + 2, 4, lineNoTestRecordDef + 2, 10)
        self.assertLocation(argLocZ, lineNoTestRecordDef + 3, 4, lineNoTestRecordDef + 3, 19)
        # Test non-existent parameter
        nonExistentLoc = info.getParamSourceLocation("nonexistent")
        self.assertIsNone(nonExistentLoc)
        # Test result type location (should be None for constructors)
        resultLoc = info.getResultTypeLocation()
        self.assertIsNone(resultLoc)
