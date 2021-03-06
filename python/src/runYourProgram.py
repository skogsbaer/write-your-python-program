# coding=utf-8
# NOTE: this file must have valid python 2 syntax. We want to display an error message
# when running with python 2.

import sys
pythonVersion = sys.version.split()[0]
if not pythonVersion.startswith('3.'):
    sys.stderr.write("\nFEHLER: es wird Python 3 benoetigt, nicht " + pythonVersion + ".\n\n")
    if sys.flags.interactive:
        import os
        os._exit(ecode)
    else:
        sys.exit(ecode)

if __name__ == '__main__':
    import runner
    runner.main(globals())
