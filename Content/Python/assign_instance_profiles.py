"""Assign TP_* profiles to portfolio material instances."""
import sys

sys.argv = ["assign_instance_profiles.py", "--assign-profiles", "--batch", "none", "--paths"]
import time
import unreal

time.sleep(15)

from convert_masters_to_substrate_toon import _assign_instance_profiles

results = _assign_instance_profiles()
unreal.log(f"[Profiles] assigned {len(results)} instances")
for r in results:
    unreal.log(f"  {r['path']} -> {r['profile']}")
