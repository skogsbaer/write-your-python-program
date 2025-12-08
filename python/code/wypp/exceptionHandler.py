import sys
import traceback
import re
from dataclasses import dataclass

# local imports
from constants import *
import stacktrace
import paths
from myLogging import *
import errors
import utils

_tbPattern = re.compile(r'(\s*File\s+")([^"]+)(".*)')
def _rewriteFilenameInTracebackLine(s: str) -> str:
    # Match the pattern: File "filename", line number, in function
    match = re.match(_tbPattern, s)
    if match:
        prefix = match.group(1)
        filename = match.group(2)
        suffix = match.group(3)
        canonicalized = paths.canonicalizePath(filename)
        return prefix + canonicalized + suffix
    else:
        return s

def _rewriteFilenameInTraceback(s: str) -> str:
    lines = s.split('\n')
    result = []
    for l in lines:
        result.append(_rewriteFilenameInTracebackLine(l))
    return '\n'.join(result)

def handleCurrentException(exit=True, removeFirstTb=False, file=sys.stderr):
    (etype, val, tb) = sys.exc_info()
    if isinstance(val, SystemExit):
        utils.die(val.code)
    isWyppError = isinstance(val, errors.WyppError)
    if isWyppError:
        extra = val.extraFrames
    else:
        extra = []
    frameList = (stacktrace.tbToFrameList(tb) if tb is not None else [])
    if frameList and removeFirstTb:
        frameList = frameList[1:]
    isSyntaxError = isinstance(val, SyntaxError)
    lastFrameIsWypp = len(frameList) > 0 and stacktrace.isWyppFrame(frameList[-1])
    isBug = not isWyppError and not isSyntaxError and lastFrameIsWypp
    stackSummary = stacktrace.limitTraceback(frameList, extra, not isBug and not isDebug())
    header = False
    for x in stackSummary.format():
        if not header:
            file.write('Traceback (most recent call last):\n')
            header = True
        file.write(_rewriteFilenameInTraceback(x))
    if isWyppError:
        s = str(val)
        if s and s[0] != '\n':
            file.write('\n')
        file.write(s)
        file.write('\n')
    else:
        for x in traceback.format_exception_only(etype, val):
            file.write(x)
    if isBug:
        debug(f'isWyppError={isWyppError}, isSyntaxError={isSyntaxError}, lastFrameIsWypp={lastFrameIsWypp}')
        file.write(f'BUG: the error above is most likely a bug in WYPP!')
    if exit:
        utils.die(1)
