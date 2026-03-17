import wypp
import threading

def foo(i: int) -> int:
    return str(i)

def doWork():
    try:
        foo(1)
    except wypp.WyppTypeError as e:
        print(e)

t = threading.Thread(target=doWork)
print('START')
t.start()
print('started')
t.join()

