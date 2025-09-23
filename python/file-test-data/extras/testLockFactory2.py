from wypp import *
import wypp
import threading
# See: https://github.com/skogsbaer/write-your-python-program/issues/77

def foo(l: wypp.Lock) -> None:
    l.acquire()
    # ...
    l.release()
    pass

foo(threading.Lock())
# ...
foo("not a lock")
