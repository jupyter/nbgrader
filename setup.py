import subprocess as sp
import sys

print('Warning: this setup.py uses flit, not setuptools.')
print('Behavior may not be exactly what you expect. Use at your own risk!')

cmd = [sys.executable, '-m', 'flit', 'install', '--deps', 'production']
print(" ".join(cmd))
sp.check_call(cmd)
