# The tests will be executed from /tmp, so we need to inject the directory of the current
# into sys.path in order to import testTypes2
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
import testTypes2

print('END')
