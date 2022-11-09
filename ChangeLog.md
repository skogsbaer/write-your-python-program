# Write Your Python Program - CHANGELOG

* 1.0.2 (2022-11-09)
  * Fix | syntax for union
* 1.0.1 (2022-10-05)
  * Include changelog
* 1.0.0 (2022-10-05)
  * Fix bug with generators
* 0.17.1 (2022-06-14)
  * Fix bug with higher-order functions
* 0.17.0 (2022-05-30)
  * Rework wrapping, fixes several bugs
* 0.16.7 (2022-05-05)
  * Improve performance with type annotations for common cases #101
* 0.16.6 (2022-05-04)
  * Fix several iterator bugs
* 0.16.5 (2022-04-26)
  * Bugfix for equality for wrapped classes
* 0.16.4 (2022-04-22)
  * Bugfix for classes inheriting from ABC
* 0.16.3 (2022-03-18)
  * Bugfix for callable type
* 0.16.2 (2022-03-17)
  * Bugfix for index method of lists #92
* 0.16.1 (2022-03-15)
  * Bugfix: AttributeError: 'DistutilsMetaFinder' object has no attribute '__name__'
  * Setting for --debug option
* 0.16.0 (2022-03-10)
  * Unify code dealing with lists, sets and dicts
  * Fix equality bug fur functions #78
  * Several smaller bugfixes and improvements
* 0.15.0 (2022-01-20)
  * Assume None if no return type is given
  * Improve error messages when types are writting like "list(int)" #61
  * Fix bug with dictionary types #68
  * Fix bug with forward refs #67
  * Fix bug with relpath under Windows
* 0.14.4
  * Fix bug for deep equality in check function
* 0.14.3
  * Fix bug with spaces in python commands
* 0.14.2
  * Allow forwards refs in generic types
  * Explictly require Python 3.9.2 or greater in setup.py
* 0.14.1 (2021-11-10)
  * Fix hashable for literals
  * Document that Python 3.9.0 and 3.9.1 are not working
  * Use quoted strings in check error messages #59
* 0.14.0 (2021-11-09)
  * Allow literals to be used in isinstance tests #55
  * Fix typechecking for complex numbers
* 0.13.3
  * Fix blame assignment for functions without return
  * Support record inheritance #11
  * Remove unnecessary "caused by parts" #43
  * Do not display location from untypy #17
* 0.13.2 (2021-10-23)
  * Better error message when number of args do not match #48
  * Fix class recursion bug #47
* 0.13.1 (2021-10-15)
  * Types for negative and positive numbers #39
* 0.13.0 (2021-10-15)
  * Improve error messages #37
  * Support for stacktraces #40
  * Better support for untyped methods #33
  * Better error message when self parameter is missing #8
  * Detect invalid method override #10
  * Detect type errors when writing record fields #12
  * Fix another encoding bug under Windows #38
* 0.12.5 (2021-10-06)
  * Fix encoding bug under Windows
  * Fix for #9
* 0.12.4 (2021-09-30)
  * Improve error message when return type hint is violated
* 0.12.1 - 0.12.3 (2021-09-29)
  * several bug fixes
* 0.12.0 (2021-09-28)
  * **Breaking change:** type annotations are now checked dynamically when the code is executed.
  This behavior can be deactivated in the settings of the extension.
* 0.11.0 (2021-03-11)
  * **Breaking change:** wypp is no longer automatically imported. You need an explicit
    import statement such as `from wypp import *`.
* 0.10.X (2021-03-10)
  * Module name is now `'__wypp__'` when executed via RUN button.
  * Fix scoping bug
  * Hitting the RUN button now changes to the directory of the current file.
* 0.9.1 (2020-12-07)
  * Fix equality for records.
* 0.9.0 (2020-12-04)
  * Enable `from __future__ import annotations` for all code executed via the RUN button.
* 0.8.2 (2020-12-01)
  * Raise an error if a field of an old-style record is mutated.
* 0.8.1 (2020-11-24)
  * Fix command execution under windows and powershell
  * Allow `List[T]` if `T` is an `Enum`, `Mixed` or `DefinedLater`
  * Better formatting of tracebacks
* 0.8.0 (2020-11-22)
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
