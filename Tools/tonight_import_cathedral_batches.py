# -*- coding: utf-8 -*-
"""Import Cathedral kit FBX in small batches via the already-open editor."""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from mcp_client import monolith  # noqa: E402

FBX_DIR = HERE.parent / "KitbashExport" / "CathedralKit"
CHUNK = 8
TIMEOUT = 300


def chunks(items, n):
    for i in range(0, len(items), n):
        yield i // n, items[i : i + n]


def run_batch(batch_i: int, stems: list[str]) -> str:
    only = ",".join(stems)
    code = f"""
import json, sys
from pathlib import Path
py = Path(r"{HERE.parent / 'Content' / 'Python'}")
if str(py) not in sys.path:
    sys.path.insert(0, str(py))
import import_cathedral_fbx as m
rc = m.main(["--only", {only!r}])
print("__T2B__" + json.dumps({{"rc": rc, "batch": {batch_i}, "n": {len(stems)}}}))
"""
    return monolith(
        "editor_query",
        {"action": "run_python", "params": {"command": code}},
        timeout=TIMEOUT,
    )


def main() -> int:
    stems = sorted(p.stem for p in FBX_DIR.glob("SM_Cathedral_*.fbx"))
    print(f"stems={len(stems)} chunk={CHUNK}", flush=True)
    failed = 0
    for i, group in chunks(stems, CHUNK):
        print(f"BATCH {i} {group}", flush=True)
        raw = run_batch(i, group)
        text = raw if isinstance(raw, str) else json.dumps(raw)
        print(text[:2000], flush=True)
        if text.startswith("ERROR:") or '"ok":false' in text.replace(" ", "").lower():
            failed += 1
    return 1 if failed else 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    raise SystemExit(main())
