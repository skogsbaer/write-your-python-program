import ast


class TransformerCombinator(ast.NodeTransformer):

    def __init__(self, *inner: ast.NodeTransformer):
        self.inner = inner

    def visit(self, node):
        for inner in self.inner:
            inner.visit(node)
