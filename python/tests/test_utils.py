import unittest
from utils import dropWhile

class TestUtils(unittest.TestCase):

    def test_dropWhile(self):
        self.assertEqual(dropWhile([1, 2, 3, 4, 5], lambda x: x < 4), [4, 5])
        self.assertEqual(dropWhile([], lambda x: x < 10), [])
        # Test where no elements satisfy the condition
        self.assertEqual(dropWhile([5, 6, 7, 8], lambda x: x < 3), [5, 6, 7, 8])
        # Test where all elements satisfy the condition
        self.assertEqual(dropWhile([1, 2, 3, 4], lambda x: x < 10), [])
