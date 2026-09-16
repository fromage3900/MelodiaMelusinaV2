#!/usr/bin/env python3
"""Validate the exported Auriga Meter GLB with only the Python standard library.

Usage:
  python tools/fromage-webgl-kit/scripts/check_auriga_meter.py \
    tools/fromage-webgl-kit/prototypes/product-motion-lab/assets/auriga_meter.glb
"""
from __future__ import annotations

import argparse
import json
import struct
from pathlib import Path

JSON_CHUNK = 0x4E4F534A
EXPECTED_NODES = {
    "AURIGA_METER_ROOT",
    "LID_ASSEMBLY",
    "DISPLAY_GLASS",
    "SIDE_PORT",
    "CONTROL_DIAL",
    "ANCHOR_screen",
    "ANCHOR_hinge",
    "ANCHOR_port",
}
EXPECTED_ANCHORS = {"ANCHOR_screen", "ANCHOR_hinge", "ANCHOR_port"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check Auriga Meter GLB structure.")
    parser.add_argument("glb", type=Path)
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument("--max-bytes", type=int, default=5_000_000)
    return parser.parse_args()


def read_glb_json(path: Path) -> dict:
    raw = path.read_bytes()
    if len(raw) < 20:
        raise ValueError("file too small to be a GLB")
    magic, version, declared_length = struct.unpack_from("<4sII", raw, 0)
    if magic != b"glTF":
        raise ValueError("invalid GLB magic")
    if version != 2:
        raise ValueError(f"expected GLB v2, got v{version}")
    if declared_length != len(raw):
        raise ValueError(f"declared length {declared_length} != actual {len(raw)}")

    offset = 12
    document = None
    while offset + 8 <= len(raw):
        chunk_length, chunk_type = struct.unpack_from("<II", raw, offset)
        offset += 8
        end = offset + chunk_length
        if end > len(raw):
            raise ValueError("GLB chunk extends beyond end of file")
        if chunk_type == JSON_CHUNK:
            document = json.loads(raw[offset:end].decode("utf-8").rstrip(" \t\r\n\x00"))
            break
        offset = end
    if document is None:
        raise ValueError("GLB has no JSON chunk")
    return document


def triangle_count(doc: dict) -> int:
    accessors = doc.get("accessors", [])
    total = 0
    for mesh in doc.get("meshes", []):
        for primitive in mesh.get("primitives", []):
            if primitive.get("mode", 4) != 4:
                continue
            index_accessor = primitive.get("indices")
            if isinstance(index_accessor, int) and 0 <= index_accessor < len(accessors):
                total += int(accessors[index_accessor].get("count", 0)) // 3
            else:
                position_accessor = primitive.get("attributes", {}).get("POSITION")
                if isinstance(position_accessor, int) and 0 <= position_accessor < len(accessors):
                    total += int(accessors[position_accessor].get("count", 0)) // 3
    return total


def inspect(path: Path, max_bytes: int) -> tuple[dict, list[str]]:
    errors: list[str] = []
    if not path.is_file():
        return {}, [f"missing GLB: {path}"]

    size = path.stat().st_size
    if size > max_bytes:
        errors.append(f"GLB is {size} bytes, over configured {max_bytes}-byte evidence budget")
    try:
        doc = read_glb_json(path)
    except Exception as exc:
        return {}, [str(exc)]

    nodes = doc.get("nodes", [])
    names = {str(node.get("name", "")) for node in nodes}
    missing = sorted(EXPECTED_NODES - names)
    if missing:
        errors.append("missing required nodes: " + ", ".join(missing))

    anchors = sorted(name for name in names if name.startswith("ANCHOR_"))
    if set(anchors) != EXPECTED_ANCHORS:
        errors.append("anchor set mismatch: " + ", ".join(anchors))

    animations = doc.get("animations", [])
    if not animations:
        errors.append("no animations exported")
    else:
        animated_node_indices = {
            channel.get("target", {}).get("node")
            for animation in animations
            for channel in animation.get("channels", [])
        }
        animated_names = {
            nodes[index].get("name", "")
            for index in animated_node_indices
            if isinstance(index, int) and 0 <= index < len(nodes)
        }
        for required in ("AURIGA_METER_ROOT", "LID_ASSEMBLY", "CONTROL_DIAL"):
            if required not in animated_names:
                errors.append(f"{required} is not targeted by an animation channel")

    summary = {
        "file": str(path),
        "bytes": size,
        "nodes": len(nodes),
        "meshes": len(doc.get("meshes", [])),
        "materials": len(doc.get("materials", [])),
        "animations": len(animations),
        "anchors": anchors,
        "triangles_approx": triangle_count(doc),
        "generator": doc.get("asset", {}).get("generator"),
    }
    return summary, errors


def main() -> int:
    args = parse_args()
    summary, errors = inspect(args.glb.resolve(), args.max_bytes)
    payload = {"ok": not errors, "summary": summary, "errors": errors}
    if args.as_json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(("CHECK_OK" if not errors else "CHECK_FAIL"), json.dumps(summary, sort_keys=True))
        for error in errors:
            print(" -", error)
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
