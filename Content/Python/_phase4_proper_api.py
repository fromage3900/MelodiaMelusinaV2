"""Use proper MonolithClient API to continue Phase 4."""
import sys, json
sys.path.insert(0, "G:/EnvironmentPortfolio/BS_GodFile/Content/Python")
from gmm.core.mcp_client import MonolithClient

mc = MonolithClient()

# 1. Discover animation actions
print("=== Animation actions ===")
r = mc.discover("animation")
print(json.dumps(r, indent=2)[:5000])
