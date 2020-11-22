# Write Your Python Program - CHANGELOG

0.8.0 (2020-11-22)
  * Alternative form for records
  * Fix bug when importing local modules
* 0.7.2 (2020-11-17)
  * Allow types such as `List[int]` in records and mixeds.
* 0.7.1. (2020-11-13)
  * Better error message when used with python 2.
* Version 0.7.0 (2020-11-13)
  * The path to the python interpreter is read from the configuration of the regular python
    extension (if not configured explicitly for wypp).
* Version 0.6.0 (2020-11-12)
  * The python support files are now installed to the user site path. This allows imports such
    as `from wypp import *` for better integration with tools like the debugger.
* Version 0.5.0 (2020-11-09)
  * better equality for floats contained in records and sequences.
* Version 0.4.0 (2020-10-30)
  * automatically deactivate pylint
  * add support for drawing simple geometric shapes (import drawingLib.py
    to use them)
