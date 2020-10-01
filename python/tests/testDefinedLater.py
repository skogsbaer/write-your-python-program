import unittest
from writeYourProgram import *

class TestMixed(unittest.TestCase):

    def test_isSome(self):
        ty = DefinedLater('Name')
        Name = Record("Name", "firstName", str, "lastName", str)
        myName = Name.make("Stefan", "Wehr")
        print(f"isSome={ty.isSome}")
        self.assertTrue(ty.isSome(myName))
        self.assertFalse(ty.isSome(42))
