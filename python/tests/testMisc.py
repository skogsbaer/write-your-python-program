import unittest
from writeYourProgram import *

setDieOnCheckFailures(True)

class TestMixed(unittest.TestCase):

    def test_types(self):
        # just check that the types are defined
        Mapping
        Dict
        Dict[str, int]

    def test_math(self):
        # just check that the functions are defined
        math.sqrt(2)
        math.sin(2)

