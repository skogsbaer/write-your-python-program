import inspect
# no other imports here (put them below) to keep the line number for myFun stable

lineNoMyFunDef = 12
lineNoMyFunCall = lineNoMyFunDef + 2
lineNoMyFunNoResultDef = 19
lineNoTestRecordDef = 26

def blub(i: int) -> int:
    return i + 1

def myFun(a: str, b: list[int], depth: int=0) -> inspect.FrameInfo:
    if depth == 0:
        return myFun("blub", [42, 0], 1)  # that's the call
    else:
        stack = inspect.stack()
        return stack[1]

def myFunNoResult(depth: int=0):
    if depth == 0:
        return myFunNoResult(1)
    else:
        stack = inspect.stack()
        return stack[1]

class TestRecord:
    x: int
    y: str
    z: float = 3.14

lineFooBase = 35
lineFooSub = 39

class Base:
    def foo(self, x: int, y: str):
        pass

class Sub(Base):
    def foo(self, y: int, x: float):
        pass
