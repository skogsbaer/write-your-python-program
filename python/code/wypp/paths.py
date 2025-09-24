import os
from typing import *
from contextlib import contextmanager

_projectDir: Optional[str] = None

@contextmanager
def projectDir(d: str):
    """Context manager to temporarily set the _relDir global variable."""
    global _projectDir
    old = _projectDir
    _projectDir = _normPath(d)
    if _projectDir and not _projectDir[-1] == '/':
        _projectDir = _projectDir + '/'
    try:
        yield
    finally:
        _projectDir = old

def _normPath(s: str) -> str:
    return os.path.normpath(os.path.abspath(s))

def canonicalizePath(s: str) -> str:
    s = _normPath(s)
    if _projectDir and s.startswith(_projectDir):
        s = s[len(_projectDir):]
    return s
