import unittest

import untypy
from untypy.error import Location


def dummy_caller_2(ch, arg):
    return ch(arg)


def dummy_caller(typ, arg):
    """
    Sets up callstack so that this function is blamed for creation.
    untypy.checker uses the function that called the function that
    invokes the checker.
    """
    ch = untypy.checker(lambda ty=typ: ty, dummy_caller)
    return dummy_caller_2(ch, arg)


class UntypyTestCase(unittest.TestCase):

    def assertBlame(self, cm, blamed):
        ok = cm.exception.last_responsable() in Location.from_code(blamed)
        if not ok:
            print(cm.exception.last_responsable())
            print("not in")
            print(Location.from_code(blamed))
        self.assertTrue(ok)
