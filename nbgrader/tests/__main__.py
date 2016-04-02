import sys
import os
import pytest
testdir = os.path.dirname(__file__)
pytest.main(["-x", testdir] + sys.argv[1:])
