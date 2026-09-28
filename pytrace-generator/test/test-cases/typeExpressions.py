from abc import ABC
from typing import Any, Callable, Literal, Optional, Union


class Meta(ABC):
    pass


Color = Literal["red", "green"]
Number = Union[int, float]
Modern = int | str
Maybe = Optional[int]
Items = list[int]
Fun = Callable[[int], str]
Anything = Any

c: Color = "red"
n: Number = 1
