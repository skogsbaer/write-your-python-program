import ast
import unittest

from untypy.util.return_traces import ReturnTraceManager, ReturnTracesTransformer


class TestAstTransform(unittest.TestCase):

    def test_ast_transform(self):
        src = """
def foo(flag: bool) -> int:
    print('Hello World')
    if flag:
        return 1
    else:
        return 'you stupid'
        """
        target = """
def foo(flag: bool) -> int:
    print('Hello World')
    if flag:
        untypy._before_return(0)
        return 1
    else:
        untypy._before_return(1)
        return 'you stupid'
        """

        tree = ast.parse(src)
        mgr = ReturnTraceManager()
        ReturnTracesTransformer("<dummyfile>", mgr).visit(tree)
        ast.fix_missing_locations(tree)
        self.assertEqual(ast.unparse(tree).strip(), target.strip())
        self.assertEqual(mgr.get(0), ("<dummyfile>", 5))
        self.assertEqual(mgr.get(1), ("<dummyfile>", 7))

