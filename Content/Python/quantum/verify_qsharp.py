import os
import sys
sys.path.insert(0, os.getcwd())
import qsharp
from pathlib import Path
proj = Path('qsharp_project')
qs_file = proj / 'Program.qs'
print('qsharp version:', getattr(qsharp, '__version__', 'unknown'))
print('compiling', qs_file)
try:
    qsharp.compile(str(qs_file))
    print('compile ok')
except Exception as e:
    print('compile failed:', repr(e))
