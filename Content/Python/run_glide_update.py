import sys
sys.path.insert(0, r'G:/EnvironmentPortfolio/BS_GodFile/Content/Python')
from gmm.core import MonolithClient

# Load the gliding update script
script_path = r'G:/EnvironmentPortfolio/BS_GodFile/Content/Python/update_glide_melusina.py'
with open(script_path, 'r') as f:
    script = f.read()

mc = MonolithClient()
result = mc.run_python(script)
print(result)
