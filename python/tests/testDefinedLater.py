import unittest
from writeYourProgram import *

setDieOnCheckFailures(True)

class TestDefinedLater(unittest.TestCase):

    def test_isSome(self):
        ty = DefinedLater('Name')
        Name = Record("Name", "firstName", str, "lastName", str)
        myName = Name("Stefan", "Wehr")
        self.assertTrue(ty.isSome(myName))
        self.assertFalse(ty.isSome(42))
        List[Name] # just use it
        List[ty] # just use it
        List[DefinedLater('foo')]

