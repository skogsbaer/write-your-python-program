from abc import ABC
from typing import Any, Callable, Literal, Optional, Union


class Meta(ABC):
    pass


Color = Literal["red", "green"]
# The legacy spellings of a union. Both must come out in the `int | float` form, the
# same as `Modern` below: their repr changed in 3.14 and the expectation here is shared
# by every version the CI matrix runs.
Number = Union[int, float]
Modern = int | str
Maybe = Optional[int]
Items = list[int]
Fun = Callable[[int], str]
Anything = Any

# PEP 695 aliases, which are shown unwrapped: what the alias stands for, not "<TypeAlias>".
type OnOff = Literal["on", "off"]
type Recursive = int | list[Recursive]
# Forward reference: the right-hand side is evaluated lazily, so this is unspellable
# until Leaf exists and is shown as "<TypeAlias>" for the steps before that.
type Tree = Leaf | None


class Leaf:
    pass


c: Color = "red"
n: Number = 1
