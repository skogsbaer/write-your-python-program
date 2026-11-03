from wypp import *

# The failing check must not change the exit code: the exception wins
check(incByOne(41), 41)
raise ValueError('bug in the tests')
