"""

A module for writing shell scripts in Python.

Assumes Python 3.

"""
import os
import os.path
import subprocess
import re
import sys
import atexit
import tempfile
import shutil
import types
import fnmatch
import shutil

_pyshell_debug = os.environ.get('PYSHELL_DEBUG', 'no').lower()
PYSHELL_DEBUG = _pyshell_debug in ['yes', 'true', 'on']

DEV_NULL = open('/dev/null')

def debug(s):
    if PYSHELL_DEBUG:
        sys.stderr.write('[DEBUG] ' + str(s) + '\n')

def fatal(s):
    sys.stderr.write('ERROR: ' + str(s) + '\n')

def resolveProg(*l):
    """Return the first program in the list that exist and is runnable.
    >>> resolveProg()
    >>> resolveProg('foobarbaz', 'python', 'grep')
    'python'
    >>> resolveProg('foobarbaz', 'padauz')
    """
    for x in l:
        ecode = run('command -v %s' % quote(x), captureStdout=DEV_NULL,
                    onError='ignore').exitcode
        if ecode == 0:
            return x
    return None

def gnuProg(x):
    prog = resolveProg('g' + x, x)
    if not prog:
        raise ShellError('Program ' + str(x) + ' not found at all')
    res = run('%s --version' % prog, captureStdout=True, onError='ignore')
    if 'GNU' in res.stdout:
        debug('Resolved program %s as %s' % (x, prog))
        return prog
    else:
        raise ShellError('No GNU variant found for program ' + str(x))

class RunResult:
    def __init__(self, stdout, exitcode):
        self.stdout = stdout
        self.exitcode = exitcode
    def __repr__(self):
        return 'RunResult(exitcode=%d, stdout=%r) '% (self.exitcode, self.stdout)
    def __eq__(self, other):
        if type(other) is type(self):
            return self.__dict__ == other.__dict__
        return False
    def __ne__(self, other):
        return not self.__eq__(other)
    def __hash__(self):
        return hash(self.__dict__)

class ShellError(BaseException):
    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
        return self.msg

class RunError(ShellError):
    def __init__(self, cmd, exitcode, stderr=None):
        self.cmd = cmd
        self.exitcode = exitcode
        self.stderr = stderr
        msg = 'Command ' + repr(self.cmd) + " failed with exit code " + str(self.exitcode)
        if stderr:
            msg = msg + '\nstderr:\n' + str(stderr)
        super(RunError, self).__init__(msg)

def splitOn(splitter):
    """Return a function that splits a string on the given splitter string.

    The function returned filters an empty string at the end of the result list.

    >>> splitOn('X')("aXbXcX")
    ['a', 'b', 'c']
    >>> splitOn('X')("aXbXc")
    ['a', 'b', 'c']
    >>> splitOn('X')("abc")
    ['abc']
    >>> splitOn('X')("abcX")
    ['abc']
    """
    def f(s):
        l = s.split(splitter)
        if l and not l[-1]:
            return l[:-1]
        else:
            return l
    return f

def splitLines(s):
    return s.strip().split('\n')

def run(cmd,
        captureStdout=False,
        onError='raise',
        input=None,
        encoding='utf-8',
        stderrToStdout=False,
        cwd=None,
        env=None,
        freshEnv=None
        ):
    """Run the given command.

    Parameters:
      cmd: the command, either a list (command with raw args)
         or a string (subject to shell exansion)
      captureStdout: what to do with stdout of the child process. Possible values:
        * False: stdout is not captured and goes to stdout of the parent process (the default)
        * True: stdout is captured and returned
        * A function: stdout is captured and the result of applying the function to the captured
          output is returned. Use splitLines as this function to split the output into lines
        * An existing file descriptor or a file object: stdout goes to the file descriptor or file
      onError: what to do if the child process finishes with an exit code different from 0
        * 'raise': raise an exception (the default)
        * 'die': terminate the whole process
        * 'ignore'
      input: string that is send to the stdin of the child process.
      encoding: the encoding for stdin and stdout. If encoding == 'raw',
        then the raw bytes are passed/returned.
      env: additional environment variables
      freshEnv: completely fresh environment
    Return value:
      A `RunResult` value, given access to the captured stdout of the child process (if it was
      captured at all) and to the exit code of the child process.

    >>> run('/bin/echo foo') == RunResult(exitcode=0, stdout='')
    True
    >>> run('/bin/echo -n foo', captureStdout=True) == RunResult(exitcode=0, stdout='foo')
    True
    >>> run('/bin/echo -n foo', captureStdout=lambda s: s + 'X') == \
        RunResult(exitcode=0, stdout='fooX')
    True
    >>> run('/bin/echo foo', captureStdout=False) == RunResult(exitcode=0, stdout='')
    True
    >>> run('cat', captureStdout=True, input='blub') == RunResult(exitcode=0, stdout='blub')
    True
    >>> try:
    ...     run('false')
    ...     raise 'exception expected'
    ... except RunError:
    ...     pass
    ...
    >>> run('false', onError='ignore') == RunResult(exitcode=1, stdout='')
    True
    """
    if type(cmd) != str and type(cmd) != list:
        raise ShellError('cmd parameter must be a string or a list')
    if type(cmd) == str:
        cmd = cmd.replace('\x00', ' ')
        cmd = cmd.replace('\n', ' ')
    stdoutIsFileLike = type(captureStdout) == int or hasattr(captureStdout, 'write')
    stdoutIsProcFun = not stdoutIsFileLike and hasattr(captureStdout, '__call__')
    shouldReturnStdout = (stdoutIsProcFun or
                            (type(captureStdout) == bool and captureStdout))
    stdout = None
    if shouldReturnStdout:
        stdout = subprocess.PIPE
    elif stdoutIsFileLike:
        stdout = captureStdout
    stdin = None
    if input:
        stdin = subprocess.PIPE
    stderr = None
    if stderrToStdout:
        stderr = subprocess.STDOUT
    input_str = 'None'
    if input:
        input_str = '<' + str(len(input)) + ' characters>'
        if encoding != 'raw':
            input = input.encode(encoding)
    debug('Running command ' + repr(cmd) + ' with captureStdout=' + str(captureStdout) +
          ', onError=' + onError + ', input=' + input_str)
    popenEnv = None
    if env:
        popenEnv = os.environ.copy()
        popenEnv.update(env)
    elif freshEnv:
        popenEnv = freshEnv.copy()
        if env:
            popenEnv.update(env)
    pipe = subprocess.Popen(
        cmd, shell=(type(cmd) == str),
        stdout=stdout, stdin=stdin, stderr=stderr,
        cwd=cwd, env=popenEnv
    )
    (stdoutData, stderrData) = pipe.communicate(input=input)
    if stdoutData is not None and encoding != 'raw':
        stdoutData = stdoutData.decode(encoding)
    if stderrData is not None and encoding != 'raw':
        stderrData = stderrData.decode(encoding)
    exitcode = pipe.returncode
    if onError == 'raise' and exitcode != 0:
        d = stderrData
        if stderrToStdout:
            d = stdoutData
        err = RunError(cmd, exitcode, d)
        raise err
    if onError == 'die' and exitcode != 0:
        sys.exit(exitcode)
    stdoutRes = stdoutData
    if stdoutRes is None:
        stdoutRes = ''
    if stdoutIsProcFun:
        stdoutRes = captureStdout(stdoutData)
    return RunResult(stdoutRes, exitcode)

# the quote function is stolen from https://hg.python.org/cpython/file/3.5/Lib/shlex.py
_find_unsafe = re.compile(r'[^\w@%+=:,./-]').search
def quote(s):
    """Return a shell-escaped version of the string *s*.
    """
    if not s:
        return "''"
    if _find_unsafe(s) is None:
        return s
    # use single quotes, and put single quotes into double quotes
    # the string $'b is then quoted as '$'"'"'b'
    return "'" + s.replace("'", "'\"'\"'") + "'"

def listAsArgs(l):
    return ' '.join([quote(x) for x in l])

def mergeDicts(*l):
    res = {}
    for d in l:
        res.update(d)
    return res

THIS_DIR = os.path.dirname(os.path.realpath(sys.argv[0]))

basename = os.path.basename
filename = os.path.basename
dirname = os.path.dirname

exists = os.path.exists

isfile = os.path.isfile # DEPRECATED
isFile = os.path.isfile

isdir = os.path.isdir # DEPRECATED
isDir = os.path.isdir

islink = os.path.islink # DEPRECATED
isLink = os.path.islink

splitext = os.path.splitext # DEPRECATED
splitExt = os.path.splitext

def removeExt(p):
    return splitext(p)[0]

def getExt(p):
    return splitext(p)[1]

expandEnvVars = os.path.expandvars

pjoin = os.path.join
mv = os.rename

def cp(src, target):
    if isDir(target):
        fname = basename(src)
        targetfile = pjoin(target, fname)
    else:
        targetfile = target
    return shutil.copyfile(src, targetfile)

def abort(msg):
    sys.stderr.write('ERROR: ' + msg + '\n')
    sys.exit(1)

def mkdir(d, mode=0o777, create_parents=False):
    if create_parents:
        os.makedirs(d, mode)
    else:
        os.mkdir(d, mode)

def cd(x):
    debug('Changing directory to ' + x)
    os.chdir(x)

def pwd():
    return os.getcwd()

class workingDir:
    def __init__(self, new_dir):
        self.new_dir = new_dir
    def __enter__(self):
        self.old_dir = pwd()
        cd(self.new_dir)
    def __exit__(self, exc_type, value, traceback):
        cd(self.old_dir)
        return False # reraise expection

def rm(path):
    os.remove(path)

def rmdir(d, recursive=False):
    if recursive:
        shutil.rmtree(d)
    else:
        os.rmdir(d)

# See https://stackoverflow.com/questions/9741351/how-to-find-exit-code-or-reason-when-atexit-callback-is-called-in-python
class ExitHooks(object):
    def __init__(self):
        self.exitCode = None
        self.exception = None

    def hook(self):
        self._origExit = sys.exit
        self._origExcHandler = sys.excepthook
        sys.exit = self.exit
        sys.excepthook = self.exc_handler

    def exit(self, code=0):
        if code is None:
            myCode = 0
        elif type(code) != int:
            myCode = 1
        else:
            myCode = code
        self.exitCode = myCode
        self._origExit(code)

    def exc_handler(self, exc_type, exc, *args):
        self.exception = exc
        self._origExcHandler(exc_type, exc, *args)

    def isExitSuccess(self):
        return (self.exitCode is None or self.exitCode == 0) and self.exception is None

    def isExitFailure(self):
        return not self.isExitSuccess()

_hooks = ExitHooks()
_hooks.hook()

def registerAtExit(action, mode):
    def f():
        debug(f'Running exit hook, mode: {mode}')
        if mode is True:
            action()
        elif mode in ['ifSuccess'] and _hooks.isExitSuccess():
            action()
        elif mode in ['ifFailure'] and _hooks.isExitFailure():
            action()
        else:
            debug('Not running exit action')
    atexit.register(f)

# deleteAtExit is one of the following:
# - True: the file is deleted unconditionally
# - 'ifSuccess': the file is deleted if the program exists with code 0
# - 'ifFailure': the file is deleted if the program exists with code != 0
def mkTempFile(suffix='', prefix='', dir=None, deleteAtExit=True):
    f = tempfile.mktemp(suffix, prefix, dir)
    if deleteAtExit:
        registerAtExit(lambda: rm(f), deleteAtExit)
    return f

def mkTempDir(suffix='', prefix='tmp', dir=None, deleteAtExit=True):
    d = tempfile.mkdtemp(suffix, prefix, dir)
    if deleteAtExit:
        registerAtExit(lambda: rmdir(d, True), deleteAtExit)
    return d

class tempDir:
    def __init__(self, suffix='', prefix='tmp', dir=None):
        self.suffix = suffix
        self.prefix = prefix
        self.dir = dir
    def __enter__(self):
        self.dir_to_delete = mkTempDir(suffix=self.suffix,
                                       prefix=self.prefix,
                                       dir=self.dir,
                                       deleteAtExit=False)
        return self.dir_to_delete
    def __exit__(self, exc_type, value, traceback):
        rmdir(self.dir_to_delete, recursive=True)
        return False # reraise expection

def ls(d, *globs):
    """
    >>> ls('../src/', '*.py', '*')
    ['../src/shell.py']
    """
    res = []
    if not d:
        d = '.'
    for f in os.listdir(d):
        for g in globs:
            if fnmatch.fnmatch(f, g):
                res.append(os.path.join(d, f))
                break
    return res

if __name__ == "__main__":
    import doctest
    doctest.testmod(verbose=False)
