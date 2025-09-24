from wypp import *

def mapReduce(inputs: list[T], mapFun: Callable[[T], U]) -> V:
    mapResults = []
    def processMapInput(input: T):
        mapResults.append(mapFun(input))
    processMapInput(inputs[0])
    return mapResults

def inc(x: int) -> int:
    return x + 1

print(mapReduce([1], inc))
