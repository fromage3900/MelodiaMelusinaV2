"""Probe Monolith MCP availability and list niagara actions (editor must be open)."""
from __future__ import annotations

import json
from pathlib import Path

REPORT = Path(__file__).resolve().parents[2] / "Saved" / "Audit" / "monolith_probe.json"


def main() -> int:
    import monolith_mcp_client as mono

    report = {
        "url": mono.MONOLITH_URL,
        "ping": mono.ping(),
        "niagara_actions": [],
        "error": None,
    }
    if report["ping"]:
        try:
            report["niagara_actions"] = mono.discover_niagara_actions()
        except Exception as exc:
            report["error"] = str(exc)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["ping"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
