# Should print 'wypp' when loaded via the RUN button.
# When imported, it should print 'printModuleName'
print(__name__)

class C:
    pass

import sys
print(sys.modules.get(C.__module__) is not None)
