import atexit
import json
import os

# The PID file allows the VS Code extension to terminate a still-running program
# (and all processes it started) before it starts a new one in the same terminal.
# The file stays open while the program runs: on Windows, an open file cannot be
# deleted, so a failing delete tells the extension that the program is still alive.

_openPidFile = None

def writePidFile(path: str):
    global _openPidFile
    if _openPidFile is not None:
        raise Exception('pid file already created')
    pgid = os.getpgid(0) if hasattr(os, 'getpgid') else None
    f = open(path, 'w', encoding='utf-8')
    json.dump({'pid': os.getpid(), 'pgid': pgid}, f)
    f.flush()
    _openPidFile = f
    atexit.register(removePidFile)

def removePidFile():
    global _openPidFile
    f = _openPidFile
    if f is None:
        return
    _openPidFile = None
    try:
        f.close()
    except OSError:
        pass
    try:
        os.remove(f.name)
    except OSError:
        pass
