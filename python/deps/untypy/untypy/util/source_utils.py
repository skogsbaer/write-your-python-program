import ast
from typing import Optional, Tuple

from untypy.error import Location


class MarkException(Exception):
    pass


def mark_source(location: Location, path: list[str]) -> str:
    source = location.source()
    tree = ast.parse(source)

    n = None
    for fn in tree.body:
        if fn.lineno == location.line_no:
            n = find_loc(fn, path)

    display = DisplayMatrix(location.source_lines_span())
    display.write((n.col_offset, n.lineno - location.line_no + 2), "^" * (n.end_col_offset - n.col_offset))

    return str(display)


# Doc At:
# https://docs.python.org/3/library/ast.html
def find_loc(node: Optional[ast.FunctionDef], path):
    if node is None:
        return None
    if len(path) == 0:
        return node

    head = path[0]
    tail = path[1:]

    if type(node) == ast.FunctionDef:
        if head == 'return':
            return find_loc(node.returns, tail)
        for arg in (node.args.args or [] + node.args.vararg or [] + node.args.kwarg or []):
            if arg.arg == head:
                return find_loc(arg.annotation, tail)
        raise MarkException("Not Found!")

    if type(node) == ast.Subscript:
        # dict[A, B]
        type_arg = node.slice
        if type(type_arg) == ast.Tuple:
            return find_loc(type_arg.dims[int(head)], tail)
        else:
            # type_arg should be something like a name
            return find_loc(type_arg, tail)


class DisplayMatrix:
    chars: dict

    def __init__(self, src: str):
        self.chars = {}
        for y, line in enumerate(src.splitlines()):
            for x, char in enumerate(line):
                self.chars[(x, y)] = char

    def write(self, pos: Tuple[int, int], message: str):
        for y, line in enumerate(message.splitlines()):
            for x, char in enumerate(line):
                self.chars[(x + pos[0], y + pos[1])] = char

    def __str__(self):
        # Slow, but this is only in the "error" path
        max_y = 0
        max_x = 0
        for x, y in self.chars:
            max_y = max(max_y, y)
            max_x = max(max_x, x)

        out = ""
        for y in range(max_y + 1):
            for x in range(max_x + 1):
                if (x, y) in self.chars:
                    out += self.chars[(x, y)]
                else:
                    out += " "
            out += "\n"
        return out
