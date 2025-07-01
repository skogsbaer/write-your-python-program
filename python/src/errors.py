from typing import *
from dataclasses import dataclass

@dataclass
class Pos:
    line: int
    col: int

@dataclass
class Location:
    file: str
    startPos: Pos
    endPos: Pos

class WyppError:
    pass

# DeliberateError instances are not reported as bugs
class DeliberateError(WyppError):
    pass

class WyppTypeError(TypeError, DeliberateError, WyppError):

    # def __init__(self, expectedTy: Any, givenValue: Any)
    pass

class WyppAttributeError(AttributeError, DeliberateError, WyppError):
    pass
