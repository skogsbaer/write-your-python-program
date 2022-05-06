import sys
import os

def getEnv(name, conv, default):
    s = os.getenv(name)
    if s is None:
        return default
    try:
        return conv(s)
    except:
        return default

_DEBUG = getEnv("WYPP_DEBUG", bool, False)

def enableDebug(debug: bool):
    global _DEBUG
    _DEBUG = debug

def debug(s):
    if _DEBUG:
        sys.stderr.write('[DEBUG] ' + s + '\n')
