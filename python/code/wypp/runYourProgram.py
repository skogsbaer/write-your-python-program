# coding=utf-8
# This is the entry point into running a python file via wypp.
# NOTE: this file must have valid python 2 syntax. We want to display an error message
# when running with python 2.
import sys
pythonVersion = sys.version.split()[0]
if not pythonVersion.startswith('3.'):
    sys.stderr.write("\nERROR: Python 3 is required, not " + pythonVersion + ".\n\n")
    if sys.flags.interactive:
        import os
        os._exit(1)
    else:
        sys.exit(1)

if __name__ == '__main__':
    import os
    sourceDir = os.path.normpath(os.path.dirname(__file__))
    codeDir = os.path.abspath(os.path.dirname(sourceDir))
    if codeDir not in sys.path:
        sys.path.insert(0, codeDir)
    import wypp.runner as r
    r.main(globals())
