import types
import traceback
import utils
import inspect
from typing import Optional, Any
import os
import sys

def tbToFrameList(tb: types.TracebackType) -> list[types.FrameType]:
    cur = tb
    res: list[types.FrameType] = []
    while cur:
        res.append(cur.tb_frame)
        cur = cur.tb_next
    return res

def isCallWithFramesRemoved(frame: types.FrameType):
    return frame.f_code.co_name == '_call_with_frames_removed'

def isWyppFrame(frame: types.FrameType):
    modName = frame.f_globals.get("__name__") or '__wypp__'
    return '__wypp_runYourProgram' in frame.f_globals or \
        modName == 'typeguard' or modName.startswith('typeguard.') or \
        modName == 'wypp' or modName.startswith('wypp.')

def isRunpyFrame(frame: types.FrameType):
    return frame.f_code.co_filename == '<frozen runpy>'

# Returns a StackSummary object. Filters the trackback by removing leading wypp or typeguard
# frames and by removing trailing frames behind _call_with_frames_removed.
# The first entry is the outermost frame, the last entry in the frame list is the frame
# where the exception happened.
def limitTraceback(frameList: list[types.FrameType],
                   extraFrames: list[inspect.FrameInfo],
                   filter: bool) -> traceback.StackSummary:
    if filter:
        endIdx = len(frameList)
        for i in range(endIdx - 1, 0, -1):
            if isCallWithFramesRemoved(frameList[i]):
                endIdx = i - 1
                break
        frameList = utils.dropWhile(frameList[:endIdx], lambda f: isWyppFrame(f) or isRunpyFrame(f))
    frameList = frameList + [f.frame for f in extraFrames]
    frames = [(f, f.f_lineno) for f in frameList]
    return traceback.StackSummary.extract(frames)

def callerOutsideWypp() -> Optional[inspect.FrameInfo]:
    stack = inspect.stack()
    #for fi in stack:
    #    print(f'{fi.filename}:{fi.lineno}')
    d = os.path.dirname(stack[0].filename)
    for f in stack:
        if not isWyppFrame(f.frame) and not d == os.path.dirname(f.filename):
            return f
    return None

# FIXME: unit tests
class ReturnTracker:
    def __init__(self):
        self.__returnFrame: Optional[types.FrameType] = None
    def __call__(self, frame: types.FrameType, event: str, arg: Any):
        # event is one of 'call', 'return', 'c_call', 'c_return', or 'c_exception'
        match event:
            case 'call':
                pass # self.__returnFrame = None
            case 'return':
                self.__returnFrame = frame
            case 'c_call':
                pass
            case 'c_return':
                pass
            case 'c_exception':
                pass
    def getReturnFrame(self) -> Optional[inspect.FrameInfo]:
        f = self.__returnFrame
        if f:
            tb = inspect.getframeinfo(f, context=1)
            return inspect.FrameInfo(f, tb.filename, tb.lineno, tb.function, tb.code_context, tb.index)
        else:
            return None

def installProfileHook() -> ReturnTracker:
    obj = sys.getprofile()
    if isinstance(obj, ReturnTracker):
        return obj
    obj = ReturnTracker()
    sys.setprofile(obj)
    return obj
