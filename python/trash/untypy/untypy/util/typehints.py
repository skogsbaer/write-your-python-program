import ast
import inspect
import typing

from untypy.error import UntypyNameError, UntypyAttributeError
from untypy.interfaces import CreationContext, WrappedFunction
from untypy.util.source_utils import DisplayMatrix

RULES = []


def _default_resolver(item):
    return typing.get_type_hints(item, include_extras=True)


def get_type_hints(item, ctx: CreationContext, resolver=_default_resolver):
    try:
        # SEE: https://www.python.org/dev/peps/pep-0563/#id7
        return resolver(item)
    except NameError as ne:
        org = WrappedFunction.find_original(item)
        if inspect.isclass(org):
            raise ctx.wrap(UntypyNameError(
                f"{ne}.\nType annotation inside of class '{qualname(org)}' could not be resolved."
            ))
        else:
            raise ctx.wrap(UntypyNameError(
                f"{ne}.\nType annotation of function '{qualname(org)}' could not be resolved."
            ))
    except Exception as e:
        # Try to find better cause in analyse
        raise analyse(item, ctx, e)


def analyse(item, ctx: CreationContext, e) -> UntypyAttributeError:
    org = WrappedFunction.find_original(item)
    what = 'function'
    if inspect.isclass(org):
        what = 'class'
    try:
        source = inspect.getsource(item)
    except OSError:
        return ctx.wrap(
            UntypyAttributeError(f"Type annotation of {what} '{qualname(org)}' could not be resolved.")
        )
    fn_ast = ast.parse(source)

    for node in map_str_to_ast(fn_ast.body[0].args, fn_ast.body[0].returns):
        for rule in RULES:
            rule_result = rule(node)
            if rule_result:
                # Got a Match
                (n, message) = rule_result
                display = DisplayMatrix(source)
                display.write((n.col_offset - 1, n.lineno),
                              " " + "^" * (n.end_col_offset - n.col_offset) + " - " + message)
                return ctx.wrap(
                    UntypyAttributeError(f"Type annotation of {what} '{qualname(org)}' could not be resolved:\n"
                                         f"{e}\n"
                                         f"\n{display}")
                )

    return ctx.wrap(
        UntypyAttributeError(f"Type annotation of {what} '{qualname(org)}' could not be resolved:\n"
                             f"{e}\n"))


# some type annotations may repr. as strings
def map_str_to_ast(*nodes):
    for outer_node in nodes:
        for node in ast.walk(outer_node):
            yield node
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                try:
                    for inode in ast.walk(ast.parse(node.value, mode='eval').body):
                        if hasattr(inode, 'lineno'):
                            inode.lineno += node.lineno - 1
                            inode.col_offset += node.col_offset + 1
                            inode.end_col_offset += node.col_offset + 1
                        yield inode
                except SyntaxError:
                    # may not a forward ref
                    pass


# Rules
# For Ast-Nodes see: https://docs.python.org/3/library/ast.html
def rule_wrong_parentheses(item):
    if isinstance(item, ast.Call) and _traverse(item, 'func.id') and _traverse(item, 'args.0'):
        inner = ", ".join(map(ast.unparse, _traverse(item, 'args')))
        return (item, f"Did you mean: '{_traverse(item, 'func.id')}[{inner}]'?")


RULES.append(rule_wrong_parentheses)


# Helpers
def _traverse(item, path):
    """
    Traverse item.
    Else return None.
    Path is a str separated by '.'
    """

    if isinstance(path, str):
        return _traverse(item, path.split("."))

    if len(path) == 0:
        return item

    head = path[0]
    tail = path[1:]

    if hasattr(item, head):
        return _traverse(getattr(item, head), tail)
    elif isinstance(item, list):
        try:
            idx = int(head)
            if len(item) > idx >= 0:
                return _traverse(item[idx], tail)
        except ValueError:
            return None
    else:
        return None


def qualname(typ):
    if hasattr(typ, '__qualname__'):
        return typ.__qualname__
    elif hasattr(typ, '__name__'):
        return typ.__name__
    else:
        return str(typ)
