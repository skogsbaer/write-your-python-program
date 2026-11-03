def foo(x: int, y: int) -> int:
    return x + y

# Only keyword arguments, the keyword argument x must be highlighted
z = foo(y=2, x='eins')
