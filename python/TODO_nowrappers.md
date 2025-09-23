* Fix file tests in test-data-2.0
* proper error messages for invalid @record
* Avoid absolute paths in error messages

* Integration tests

* Installation
* Typechecked console
* Debug slow startup times
* show "@record\nclass C" for record attributes


Problematic tests:

  test-data-2.0/failing/testTypesProtos3.py  # non-static methods without self

  test-data-2.0/failing/testArgs_ok.py  # absolute filenames



