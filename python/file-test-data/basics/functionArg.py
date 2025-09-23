def bar(s: str) -> str:
    return s

def foo(i: int, j: int) -> int:
    return i + 1

if True:
    print(foo(foo(1, "1"), 42))
