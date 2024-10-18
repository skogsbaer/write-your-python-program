# Write Your Python Program (WYPP)

A user-friendly python programming environment for beginners.

The ideas of this environment are based on the great ideas from
[Schreib dein Programm!](https://www.deinprogramm.de/sdp/).

WYPP consists of two parts:

- An extension for [Visual Studio Code](https://code.visualstudio.com).
- A python package named `wypp`.

This is the README for the python package. Usually, you install the python package together
with the extension for Visual Studio Code. The
[homepage of WYPP](https://github.com/skogsbaer/write-your-python-program) explains
how to install the extension and it contains extensive documentation on WYPP's features.

In case you want the use the `wypp` package *without* Visual Studio Code, you can install
the package via pip:

```
pip3 install wypp
```

This needs Python 3.12.x. After installation, you can use the `wypp` command
for running your python files, making all features explained below available.
Run `wypp --help` for usage information.

## Development

### Debugging

To debug a failing unit test, insert the following at top of the file (adjust path as needed):

```
import sys
sys.path.insert(0, '/Users/swehr/devel/write-your-python-program/python/deps/untypy')
```

Then insert at the end of the file:

```
def _debug():
    t = TestSimple()
    t.setUp()
    t.test_wrap_inheritance()
_debug()
```

Then debug in vscode
