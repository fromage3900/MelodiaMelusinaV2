"""Test script for -ExecutePythonScript."""
from __future__ import annotations
import datetime
import json
import os

try:
    import unreal
    unreal.log("_test_exec: unreal imported OK")
except ImportError as e:
    unreal.log(f"_test_exec: unreal import FAILED: {e}")
    raise

report = {
    "timestamp": str(datetime.datetime.now()),
    "message": "Hello from execute script!",
}

audit_dir = "Saved/Audit"
os.makedirs(audit_dir, exist_ok=True)
path = os.path.join(audit_dir, "_test_exec.json")
with open(path, "w") as f:
    json.dump(report, f, indent=2)

print(f"_test_exec: wrote {path}")
unreal.log(f"_test_exec: wrote {path}")
