def bar(i: int) -> int:
    if i == 0:
        return 1/0
    else:
        x = bar(i - 1)
        res = i + x
        return res

try:
    bar(2)
except:
    pass
