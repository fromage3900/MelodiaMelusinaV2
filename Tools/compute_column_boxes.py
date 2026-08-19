"""Compute per-column comment-box rectangles for the four Melodia masters.

Repo-side (no `unreal` import). Calls Monolith material_query get_all_expressions
(which includes pos_x/pos_y) for each master, maps parameters to their canonical
column via master_column_scheme, and writes bounding-box JSON that
annotate_master_columns.py consumes in-editor.

Usage (editor open):
  python Tools/compute_column_boxes.py
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

MONOLITH_URL = "http://127.0.0.1:9316/mcp"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
PY = PROJECT_ROOT / "Content" / "Python"
OUT = PROJECT_ROOT / "Saved" / "Audit" / "column_boxes.json"

sys.path.insert(0, str(PY))
import master_column_scheme as scheme  # noqa: E402

MASTERS = {
    "M_Master_Toon_Universal": "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal",
    "M_Master_Toon_Landscape_HeightBlend": "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Landscape_HeightBlend",
    "M_Master_Nikki": "/Game/EnvSandbox/Materials/Masters/M_Master_Nikki",
    "M_Master_Nikki_Landscape": "/Game/EnvSandbox/Materials/Masters/M_Master_Nikki_Landscape",
}

PAD = 140.0


def call_tool(name: str, arguments: dict, timeout: int = 180) -> dict:
    payload = json.dumps({
        "jsonrpc": "2.0", "id": 1, "method": "tools/call",
        "params": {"name": name, "arguments": arguments},
    }).encode()
    req = Request(MONOLITH_URL, data=payload, headers={"Content-Type": "application/json"})
    with urlopen(req, timeout=timeout) as resp:
        envelope = json.loads(resp.read().decode())
    text = envelope.get("result", {}).get("content", [{}])[0].get("text", "")
    return json.loads(text)


def boxes_for(stem: str, asset_path: str) -> dict:
    data = call_tool("material_query", {"action": "get_all_expressions", "asset_path": asset_path})
    exprs = data.get("expressions") or []
    meta = scheme.build_meta(scheme.groups_for(stem))
    groups = scheme.groups_for(stem)
    label_to_names = {label: set(names) for label, names in groups}

    by_group: dict[str, list[tuple[float, float]]] = {}
    for e in exprs:
        # Parameter nodes expose the parameter name under "parameter_name";
        # node instance names ("MaterialExpressionScalarParameter_50") are not
        # instance-editable identifiers.
        pname = e.get("parameter_name")
        if not pname or pname == "None":
            continue
        cls = e.get("class") or ""
        if "Parameter" not in cls or "CollectionParameter" in cls:
            continue
        entry = meta.get(pname)
        if not entry:
            continue
        label = entry[0]
        px, py = e.get("pos_x"), e.get("pos_y")
        if px is None or py is None:
            continue
        by_group.setdefault(label, []).append((float(px), float(py)))

    boxes: dict[str, dict] = {}
    for label, names in groups:
        pts = by_group.get(label)
        if not pts:
            continue
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        boxes[label] = {
            "x": min(xs) - PAD,
            "y": min(ys) - PAD,
            "width": max(xs) - min(xs) + 2 * PAD,
            "height": max(ys) - min(ys) + 2 * PAD,
        }
    return {"asset_path": asset_path, "boxes": boxes}


def main() -> int:
    payload: dict = {"timestamp": datetime.now(timezone.utc).isoformat(), "masters": {}}
    for stem, path in MASTERS.items():
        try:
            payload["masters"][stem] = boxes_for(stem, path)
            print(f"{stem}: {len(payload['masters'][stem]['boxes'])} boxes")
        except Exception as exc:  # noqa: BLE001
            print(f"{stem}: ERROR {exc}", file=sys.stderr)
            payload["masters"][stem] = {"asset_path": path, "boxes": {}, "error": str(exc)}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=1), encoding="utf-8")
    print(json.dumps({"out": str(OUT)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
