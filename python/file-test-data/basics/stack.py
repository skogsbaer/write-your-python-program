def factorial(n: int) -> int:
    if n == 0:
        raise ValueError('kein Bock')
    else:
        return factorial(n - 1) * n

factorial(5)
