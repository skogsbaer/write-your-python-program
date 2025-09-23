* Fix file tests in test-data
* proper error messages for invalid @record
* Avoid absolute paths in error messages
* Integration tests
* Installation
* Typechecked console
* Debug slow startup times
* show "@record\nclass C" for record attributes


Problematic tests:

  test-data-2.0/failing/testTypesProtos3.py  # non-static methods without self

  test-data-2.0/failing/testHintParentheses3.py  # Union(list, str)

  test-data-2.0/failing/testWrongKeywordArg2.py  # problem with keyword args
  test-data-2.0/failing/testWrongKeywordArg.py  # problem with keyword args

  test-data-2.0/failing/main.py  # modules

  test-data-2.0/failing/testGetSource.py  # Literal
  test-data-2.0/failing/testLiteral1.py   # Literal



  test-data-2.0/failing/testArgs_ok.py  # absolute filenames



