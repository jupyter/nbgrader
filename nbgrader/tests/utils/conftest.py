import pytest
import sys

notwindows = pytest.mark.skipif(
    sys.platform == 'win32',
    reason='This functionality of nbgrader is unsupported on Windows')
