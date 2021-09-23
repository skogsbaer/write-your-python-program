import wypp
import printModuleName
print(__name__)

class C:
    pass

import sys
print(sys.modules.get(C.__module__) is not None)
print(sys.modules.get(printModuleName.C.__module__) is not None)

