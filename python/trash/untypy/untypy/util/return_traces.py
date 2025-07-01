import ast
from typing import *


class ReturnTraceManager:
    """
    Stores file & line_no to every return idx
    """
    def __init__(self):
        self.lst = []

    def next_id(self, reti : ast.Return, file: str) -> int:
        i = len(self.lst)
        self.lst.append((file, reti.lineno))
        return i

    def get(self, idx : int) -> (str, int):
        return self.lst[idx]

GlobalReturnTraceManager = ReturnTraceManager()
reti_loc: int = -1


def before_return(idx : int):
    global reti_loc
    reti_loc = idx


def get_last_return() -> (str, int):
    global reti_loc
    if reti_loc < 0:
        return ("<nothing>", 0) # this will never match any real location

    # Note: this location is only used if it is in the span of the located function.
    # See ReturnExecutionContext
    return GlobalReturnTraceManager.get(reti_loc)


class ReturnTracesTransformer(ast.NodeTransformer):

    def __init__(self, file: str, manager=GlobalReturnTraceManager):
        self.file = file
        self.manager = manager

    def generic_visit(self, node) -> Any:
        # See https://docs.python.org/3/library/ast.html
        stmt_types = ["body", "orelse", "finalbody"]

        for stmt_type in stmt_types:
            if not hasattr(node, stmt_type):
                continue
            statements : list = getattr(node, stmt_type)

            if not isinstance(statements, Iterable):
                # skip lambda expressions
                continue

            inserts = []
            for i,s in enumerate(statements):
                if type(s) is ast.Return:
                    inserts.append((i, s))

            # start at end so the early indexes still fit
            inserts.reverse()

            for index, reti in inserts:
                n = ast.Expr(value=ast.Call(
                    func=ast.Attribute(value=ast.Name(id='untypy', ctx=ast.Load()), attr='_before_return', ctx=ast.Load()),
                    args=[ast.Constant(value=self.manager.next_id(reti, self.file))],
                    keywords=[])
                )
                statements.insert(index, n)

        super(ast.NodeTransformer, self).generic_visit(node)

