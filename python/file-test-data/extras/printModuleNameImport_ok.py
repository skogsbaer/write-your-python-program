# WYPP_TEST_CONFIG: {"typecheck": "both"}
import wypp
import printModuleName_ok
print(__name__)

class C:
    pass

import sys
print(sys.modules.get(C.__module__) is not None)
print(sys.modules.get(printModuleName_ok.C.__module__) is not None)

