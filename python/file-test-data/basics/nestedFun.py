def bar(s: str) -> int:
    return len(s)

def foo(i: int) -> int:
    def bar(j: int) -> int:
        return j + 1
    return bar("foo")

foo(1)
