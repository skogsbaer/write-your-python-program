from typing import *
from dataclasses import dataclass
import abc

@dataclass
class Pos:
    line: int
    col: int

@dataclass
class Location:
    file: str
    startPos: Pos
    endPos: Pos

class WyppError(abc.ABC):
    pass

# DeliberateError instances are not reported as bugs
class DeliberateError(WyppError, abc.ABC):
    pass

class WyppTypeError(TypeError, DeliberateError):

    # def __init__(self, expectedTy: Any, givenValue: Any)
    pass

class WyppAttributeError(AttributeError, DeliberateError):
    pass
