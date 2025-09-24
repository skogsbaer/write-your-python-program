import types
import traceback
import utils
import inspect
from typing import Optional, Any
import os
import sys
from collections import deque

def tbToFrameList(tb: types.TracebackType) -> list[types.FrameType]:
    cur = tb
    res: list[types.FrameType] = []
    while cur:
        res.append(cur.tb_frame)
        cur = cur.tb_next
    return res

def isCallWithFramesRemoved(frame: types.FrameType):
    return frame.f_code.co_name == utils._call_with_frames_removed.__name__

def isCallWithNextFrameRemoved(frame: types.FrameType):
    return frame.f_code.co_name == utils._call_with_next_frame_removed.__name__

def isWyppFrame(frame: types.FrameType):
    modName = frame.f_globals.get("__name__") or '__wypp__'
    fname = frame.f_code.co_filename
    directDir = os.path.basename(os.path.dirname(fname))
    if '__wypp_runYourProgram' in frame.f_globals:
        return True
    for prefix in ['wypp', 'typeguard']:
        if modName == prefix or modName.startswith(prefix + '.') or directDir == prefix:
            return True
    return False

def isRunpyFrame(frame: types.FrameType) -> bool:
    f = frame.f_code.co_filename
    return f == '<frozen runpy>' or f.startswith('<frozen importlib.')

# Returns a StackSummary object. Filters the trackback by removing leading wypp or typeguard
# frames and by removing trailing frames behind _call_with_frames_removed.
# The first entry is the outermost frame, the last entry in the frame list is the frame
# where the exception happened.
def limitTraceback(frameList: list[types.FrameType],
                   extraFrames: list[inspect.FrameInfo],
                   filter: bool) -> traceback.StackSummary:
    if filter:
        # Step 1: remove all frames that appear after the first _call_with_frames_removed
        endIdx = len(frameList)
        for i in range(len(frameList)):
            if isCallWithFramesRemoved(frameList[i]):
                endIdx = i - 1
                break
        frameList = frameList[:endIdx]
        # Step 2: remove those frames directly after _call_with_next_frame_removed
        toRemove = []
        for i in range(len(frameList)):
            if isCallWithNextFrameRemoved(frameList[i]):
                toRemove.append(i)
        for i in reversed(toRemove):
            frameList = frameList[:i-1] + frameList[i+1:]
        # Step 3: remove leading wypp or typeguard frames
        frameList = utils.dropWhile(frameList, lambda f: isWyppFrame(f) or isRunpyFrame(f))
    frameList = frameList + [f.frame for f in extraFrames]
    frames = [(f, f.f_lineno) for f in frameList]
    return traceback.StackSummary.extract(frames)

def callerOutsideWypp() -> Optional[inspect.FrameInfo]:
    stack = inspect.stack()
    d = os.path.dirname(stack[0].filename)
    for f in stack:
        if not isWyppFrame(f.frame) and not d == os.path.dirname(f.filename):
            return f
    return None

class ReturnTracker:
    def __init__(self, entriesToKeep: int):
        self.__returnFrames = deque(maxlen=entriesToKeep)   # a ring buffer
    def __call__(self, frame: types.FrameType, event: str, arg: Any):
        # event is one of 'call', 'return', 'c_call', 'c_return', or 'c_exception'
        match event:
            case 'call':
                pass
            case 'return':
                # print(f'appending {frame} to return tracker')
                self.__returnFrames.append(frame) # overwrite oldest when full
            case 'c_call':
                pass
            case 'c_return':
                pass
            case 'c_exception':
                pass
    def getReturnFrame(self, idx: int) -> Optional[inspect.FrameInfo]:
        try:
            f = self.__returnFrames[idx]
        except IndexError:
            return None
        if f:
            tb = inspect.getframeinfo(f, context=1)
            fi = inspect.FrameInfo(f, tb.filename, tb.lineno, tb.function, tb.code_context, tb.index)
            del f
            return fi
        else:
            return None

# when using _call_with_next_frame_removed, we have to take the second-to-last
# return. Hence, we keep the two most recent returns byn setting entriesToKeep = 2.
def installProfileHook(entriesToKeep: int=2) -> ReturnTracker:
    obj = sys.getprofile()
    if isinstance(obj, ReturnTracker):
        return obj
    obj = ReturnTracker(entriesToKeep)
    sys.setprofile(obj)
    return obj

def getReturnTracker():
    obj = sys.getprofile()
    if isinstance(obj, ReturnTracker):
        return obj
    else:
        raise ValueError(f'No ReturnTracker set, must use installProfileHook before')
