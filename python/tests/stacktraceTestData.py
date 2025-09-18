f1ReturnLine = 6
f2ReturnLine = 9
f3ReturnLine = 13

def f1():
    return 42

def f2():
    f1()

def f3():
    f1()
    return 0
