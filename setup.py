import subprocess as sp

print('Warning: this setup.py uses flit, not setuptools.')
print('Behavior may not be exactly what you expect. Use at your own risk!')

sp.check_call(['flit', 'install', '--deps', 'production'])
