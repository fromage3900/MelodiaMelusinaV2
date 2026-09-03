"""Force-rebuild M_Master_Toon_Universal (sets --force for headless UE)."""
from __future__ import annotations

import sys

sys.argv = ["setup_master_universal.py", "--force"]

from setup_master_universal import build

if __name__ == "__main__":
    build()
