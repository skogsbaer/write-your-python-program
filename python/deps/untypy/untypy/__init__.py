import ast
import inspect
import sys
from types import ModuleType
from typing import Optional, Any, Union, Callable

from .patching import wrap_function, patch_class, wrap_class, DefaultConfig
from .patching.ast_transformer import UntypyAstTransformer, did_no_code_run_before_untypy_enable, \
    UntypyAstImportTransformer
from .patching.import_hook import install_import_hook
from .patching.standalone_checker import StandaloneChecker
from .util.condition import FunctionCondition
from .util.return_traces import ReturnTracesTransformer, before_return, GlobalReturnTraceManager
from .util.tranformer_combinator import TransformerCombinator

GlobalConfig = DefaultConfig

"""
This function is called before any return statement, to store which was the last return.
For this the AST is transformed using ReturnTracesTransformer.
Must be in untypy so it can be used in transformed module.
Must also be in other module, so it can be used from inside (No circular imports).
"""
_before_return = before_return

_importhook_transformer_builder = lambda path, file: TransformerCombinator(UntypyAstTransformer(),
                                                                           ReturnTracesTransformer(file))

def just_install_hook(prefixes=[]):
    global GlobalConfig

    def predicate(module_name):
        for p in prefixes:
            if module_name == p:
                return True
            elif module_name.startswith(p + "."):
                return True
        return False

    GlobalConfig = DefaultConfig._replace(checkedprefixes=[*prefixes])
    install_import_hook(predicate, _importhook_transformer_builder)


def transform_tree(tree, file):
    UntypyAstTransformer().visit(tree)
    ReturnTracesTransformer(file).visit(tree)
    ast.fix_missing_locations(tree)


def enable(*, recursive: bool = True, root: Union[ModuleType, str, None] = None, prefixes: list[str] = []) -> None:
    global GlobalConfig
    caller = _find_calling_module()
    exit_after = False

    if root is None:
        root = caller
        exit_after = True
    if caller is None:
        raise Exception("Couldn't find loading Module. This is a Bug.")

    rootname = root
    if hasattr(rootname, '__name__'):
        rootname = root.__name__

    GlobalConfig = DefaultConfig._replace(checkedprefixes=[rootname])

    def predicate(module_name):
        if recursive:
            # Patch if Submodule
            if module_name.startswith(rootname + "."):
                return True
            else:
                for p in prefixes:
                    if module_name == p:
                        return True
                    elif module_name.startswith(p + "."):
                        return True
            return False
        else:
            raise AssertionError("You cannot run 'untypy.enable()' twice!")

    transformer = _importhook_transformer_builder
    install_import_hook(predicate, transformer)
    _exec_module_patched(root, exit_after, transformer(caller.__name__.split("."), caller.__file__))


def enable_on_imports(*prefixes):
    print("!!!! THIS FEATURE HAS UNEXPECTED SIDE EFFECTS WHEN IMPORTING ABSOLUTE SUBMODULES !!!")
    # TODO: Fix import of submodules should not change parent module.
    global GlobalConfig
    GlobalConfig = DefaultConfig._replace(checkedprefixes=[*prefixes])
    caller = _find_calling_module()

    def predicate(module_name: str):
        module_name = module_name.replace('__main__.', '')
        for p in prefixes:
            if module_name == p:
                return True
            elif module_name.startswith(p + "."):
                return True
            else:
                return False

    transformer = _importhook_transformer_builder
    install_import_hook(predicate, transformer)
    _exec_module_patched(caller, True, transformer(caller.__name__.split("."), caller.__file__))


def _exec_module_patched(mod: ModuleType, exit_after: bool, transformer: ast.NodeTransformer):
    source = inspect.getsource(mod)
    tree = compile(source, mod.__file__, 'exec', ast.PyCF_ONLY_AST,
                   dont_inherit=True, optimize=-1)

    if not did_no_code_run_before_untypy_enable(tree):
        raise AssertionError("Please put 'untypy.enable()' at the start of your module like so:\n"
                             "\timport untypy\n"
                             "\tuntypy.enable()")

    transformer.visit(tree)
    ReturnTracesTransformer(mod.__file__).visit(tree)
    ast.fix_missing_locations(tree)
    patched_mod = compile(tree, mod.__file__, 'exec', dont_inherit=True, optimize=-1)
    stack = list(map(lambda s: s.frame, inspect.stack()))
    try:
        exec(patched_mod, mod.__dict__)
    except Exception as e:
        while e.__traceback__.tb_frame in stack:
            e.__traceback__ = e.__traceback__.tb_next
        sys.excepthook(type(e), e, e.__traceback__)
        if exit_after: sys.exit(-1)
    if exit_after: sys.exit(0)


def _find_calling_module() -> Optional[ModuleType]:
    for caller in inspect.stack():
        if caller.filename != __file__:
            mod = inspect.getmodule(caller.frame)
            if mod is not None:
                return mod
    return None


def _condgetfc(func):
    if hasattr(func, "__fc"):
        return getattr(func, "__fc")
    else:
        fc = FunctionCondition()
        setattr(func, "__fc", fc)
        fc.func = func
        return fc


def precondition(cond):
    def decorator(func):
        fc = _condgetfc(func)
        fc.precondition.append(cond)
        return func

    return decorator


def postcondition(cond):
    def decorator(func):
        fc = _condgetfc(func)
        fc.postcondition.append(cond)
        return func

    return decorator


def unchecked(fn):
    setattr(fn, "__unchecked", True)
    return fn


def patch(a: Any) -> Any:
    global GlobalConfig
    if hasattr(a, '__unchecked'):
        return a

    if inspect.isfunction(a):
        return wrap_function(a, GlobalConfig)
    elif inspect.isclass(a):
        patch_class(a, GlobalConfig)
        return a
    else:
        return a


typechecked = patch


def wrap_import(a: Any) -> Any:
    global GlobalConfig
    if inspect.isfunction(a):
        return wrap_function(a, GlobalConfig)
    elif inspect.isclass(a) or inspect.ismodule(a):
        return wrap_class(a, GlobalConfig)
    else:
        return a


def checker(annotation :  Callable[[], Any], location : Any) -> Callable[[Any], Any]:
    """
    :param annotation: A functions that returns the annotation lazily. (Needed for FowardRefs)
    :param location: Where was it declared?
    :return: A type checker function
    """
    return StandaloneChecker(annotation, location, DefaultConfig)
