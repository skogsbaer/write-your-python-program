import unittest
from writeYourProgram import *

setDieOnCheckFailures(True)

class TestMixed(unittest.TestCase):

    def test_isSome(self):
        ty = DefinedLater('Name')
        Name = Record("Name", "firstName", str, "lastName", str)
        myName = Name.make("Stefan", "Wehr")
        self.assertTrue(ty.isSome(myName))
        self.assertFalse(ty.isSome(42))
