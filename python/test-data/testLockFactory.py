from wypp import *

import threading
# See: https://github.com/skogsbaer/write-your-python-program/issues/77

def foo(lock: LockFactory) -> None:
    l = lock()
    l.acquire()
    # ...
    l.release()
    pass

foo(threading.Lock)
# ...
foo("not a lock")