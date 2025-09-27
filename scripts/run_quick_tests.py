# Quick test runner that imports the test module and runs its test function
import sys
sys.path.append('.')
from tests import test_utils

try:
    test_utils.test_normalize_and_classify_basic()
    print('TESTS PASSED')
except AssertionError as e:
    print('TEST FAILED:', e)
    raise
except Exception as e:
    print('ERROR RUNNING TESTS:', e)
    raise
