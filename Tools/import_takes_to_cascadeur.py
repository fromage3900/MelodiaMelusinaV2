"""Import the split Quaternius take FBX files into the running Cascadeur scene.

Each file is imported as a scene (skeleton + its clip). Skips files already
present (tracked by name in the report). Writes a per-run report next to the
takes and prints one line per file.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT))

from deploy.cascadeur_mcp_server import import_fbx  # noqa: E402

TAKES = PROJECT / "Imports" / "Animations" / "Cascadeur" / "Source" / "Quaternius" / "Takes"
REPORT = TAKES / "_cascadeur_import_report.json"


def main() -> int:
    report = {"ok": [], "failed": []}
    if REPORT.is_file():
        try:
            report = json.loads(REPORT.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError):
            report = {"ok": [], "failed": []}
    done = set(report["ok"])

    files = [fbx for fbx in sorted(TAKES.glob("CAS_Q_*.fbx")) if fbx.name not in done]
    for attempt in (1, 2):
        remaining = []
        for fbx in files:
            try:
                resp_text = import_fbx(str(fbx).replace("\\", "/"))
            except Exception as exc:
                resp = {"status": "error", "message": f"bridge call failed: {exc}"}
            else:
                try:
                    resp = json.loads(resp_text)
                except (TypeError, json.JSONDecodeError):
                    resp = {"status": "error", "message": resp_text}
            if resp.get("status") == "success":
                report["ok"].append(fbx.name)
                print(f"OK {fbx.name}")
            else:
                if attempt == 1:
                    print(f"RETRY {fbx.name}: {resp.get('message', resp)}")
                    remaining.append(fbx)
                else:
                    report["failed"].append({"file": fbx.name, "error": resp.get("message", resp)})
                    print(f"FAIL {fbx.name}: {resp.get('message', resp)}")
            REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
        if not remaining:
            break
        files = remaining
    print(f"report: {REPORT}")
    return 0 if not report["failed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
