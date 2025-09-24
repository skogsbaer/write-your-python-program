import sys
import runner

# Use this file if you want to the some test file under the debugger
if __name__ == '__main__':
    sys.argv = ['python', 'test-data/testIndexError.py']
    runner.main(globals())
