def foo(l: tuple[int, ...]) -> int:
    return len(l)

print(foo((1,2,3)))
foo(1)
