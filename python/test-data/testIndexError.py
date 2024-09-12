def foo(l: list[int]) -> int:
    #raise IndexError('blub')
    x = l[42]
    return x

foo([1,2,3])
