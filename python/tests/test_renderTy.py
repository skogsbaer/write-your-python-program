import unittest
from typing import *
from renderTy import renderTy

class MyClass:
    pass

class TestRenderTy(unittest.TestCase):

    def test_basics(self):
        self.assertEqual(renderTy(int), 'int')
        self.assertEqual(renderTy(list[str]), 'list[str]')
        self.assertEqual(renderTy(dict[str, list[int]]), 'dict[str, list[int]]')
        self.assertEqual(renderTy(Optional[dict[str, int]]), 'Optional[dict[str, int]]')
        self.assertEqual(renderTy(tuple[int, ...]), 'tuple[int, ...]')
        self.assertEqual(renderTy(Union[int, str, bool]), 'Union[int, str, bool]')
        self.assertEqual(renderTy(Callable[[int, str, list[float]], bool]),
                         'Callable[[int, str, list[float]], bool]')

    def test_advanced_types(self):
        # Nested generics
        self.assertEqual(renderTy(dict[str, list[tuple[int, str]]]), 'dict[str, list[tuple[int, str]]]')
        self.assertEqual(renderTy(list[dict[str, Optional[int]]]), 'list[dict[str, Optional[int]]]')

        # Complex Union types
        self.assertEqual(renderTy(Union[int, str, None]), 'Union[int, str, None]')
        self.assertEqual(renderTy(Union[list[int], dict[str, int], tuple[int, ...]]),
                         'Union[list[int], dict[str, int], tuple[int, ...]]')
        self.assertEqual(renderTy(int | str), 'Union[int, str]')
        self.assertEqual(renderTy(list[int] | dict[str, int] | None),
                         'Union[list[int], dict[str, int], None]')

        # Callable with complex signatures
        self.assertEqual(renderTy(Callable[[dict[str, int], Optional[list[str]]], Union[int, str]]),
                         'Callable[[dict[str, int], Optional[list[str]]], Union[int, str]]')
        self.assertEqual(renderTy(Callable[[], None]), 'Callable[[], None]')

        # Literal types
        self.assertEqual(renderTy(Literal['red', 'green', 'blue']), "Literal['red', 'green', 'blue']")
        self.assertEqual(renderTy(Literal[1, 2, 3]), 'Literal[1, 2, 3]')

    def test_special_forms(self):
        # Any and NoReturn
        self.assertEqual(renderTy(Any), 'Any')
        self.assertEqual(renderTy(NoReturn), 'NoReturn')

        # Forward references (if supported)
        self.assertEqual(renderTy(ForwardRef('SomeClass')), 'SomeClass')


    def test_edge_cases(self):
        # Empty tuple
        self.assertEqual(renderTy(tuple[()]), 'tuple[()]')

        # Single element tuple
        self.assertEqual(renderTy(tuple[int]), 'tuple[int]')

        # Very nested types
        self.assertEqual(renderTy(dict[str, dict[str, dict[str, int]]]),
                         'dict[str, dict[str, dict[str, int]]]')

        # Union with single type
        self.assertEqual(renderTy(Union[int]), 'int')

        # Complex Callable with nested types
        self.assertEqual(renderTy(Callable[[Callable[[int], str], list[int]], dict[str, Any]]),
                         'Callable[[Callable[[int], str], list[int]], dict[str, Any]]')

    def test_custom_classes(self):
        # Custom class types

        self.assertEqual(renderTy(MyClass), 'tests.test_renderTy.MyClass')
        self.assertEqual(renderTy(list[MyClass]), 'list[tests.test_renderTy.MyClass]')
        self.assertEqual(renderTy(Optional[MyClass]), 'Optional[tests.test_renderTy.MyClass]')

