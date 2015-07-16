import subprocess as sp
import sys
import os

print('Warning: this setup.py uses flit, not setuptools.')
print('Behavior may not be exactly what you expect. Use at your own risk!')

flit = os.path.join(os.path.dirname(sys.executable), 'flit')
cmd = [flit, 'install', '--deps', 'production']
print(" ".join(cmd))
sp.check_call(cmd)
