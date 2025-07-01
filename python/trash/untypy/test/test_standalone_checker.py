import unittest
import untypy
from untypy.error import UntypyTypeError, Location


class TestStandaloneChecker(unittest.TestCase):

    def test_standalone(self):
        ch = untypy.checker(lambda: int, TestStandaloneChecker.test_standalone)

        self.assertEqual(ch(42), 42)

        def myfunc(x):
            ch(x)

        with self.assertRaises(UntypyTypeError) as cm:
            myfunc("hello")

        self.assertEqual(cm.exception.expected, 'int')
        self.assertEqual(cm.exception.last_declared(), Location.from_code(TestStandaloneChecker.test_standalone))
        self.assertIn('myfunc("hello")', cm.exception.last_responsable().source_lines)