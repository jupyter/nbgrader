import os
print("COVERAGE_PROCESS_START={}".format(os.environ.get('COVERAGE_PROCESS_START', '')))
# import coverage for when testing subprocesses
import coverage
coverage.process_startup()
