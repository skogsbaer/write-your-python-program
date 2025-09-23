def foo(x: int, y: int, z: str) -> int:
    return x + y + len(z)

foo(1, z='foo', y=2)
print('ok')
