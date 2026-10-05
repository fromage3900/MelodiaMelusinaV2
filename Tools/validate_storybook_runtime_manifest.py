"""Offline integrity gate for the canonical Storybook UI export manifest.

No Unreal or Figma dependency. Verifies every texture payload decodes as PNG,
checks IHDR pixel dimensions against export_size, and confirms every declared
SVG source exists in git worktree when run locally.
"""
from __future__ import annotations

import base64
import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "pipeline" / "figma" / "storybook_runtime_manifest.json"
PNG_SIG = b"\x89PNG\r\n\x1a\n"


def png_size(data: bytes) -> tuple[int, int]:
    if len(data) < 24 or data[:8] != PNG_SIG:
        raise ValueError("not a PNG payload")
    if data[12:16] != b"IHDR":
        raise ValueError("PNG missing IHDR at canonical offset")
    return struct.unpack(">II", data[16:24])


def main() -> int:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    failures: list[str] = []
    checked = 0

    for entry in data.get("entries", []):
        source_svg = entry.get("source_svg")
        if source_svg and not (ROOT / source_svg).is_file():
            failures.append(f"{entry['id']}: missing source_svg {source_svg}")

        if entry.get("runtime_type") != "texture":
            continue

        payload = ROOT / entry["png_b64"]
        if not payload.is_file():
            failures.append(f"{entry['id']}: missing payload {entry['png_b64']}")
            continue

        try:
            raw = base64.b64decode(payload.read_text(encoding="ascii").strip(), validate=True)
            size = png_size(raw)
        except Exception as exc:
            failures.append(f"{entry['id']}: decode/PNG error: {exc}")
            continue

        expected = tuple(entry["export_size"])
        if size != expected:
            failures.append(f"{entry['id']}: PNG {size} != manifest {expected}")
        checked += 1

    if failures:
        print("STORYBOOK_RUNTIME_MANIFEST: FAIL")
        for failure in failures:
            print(" -", failure)
        return 1

    print(
        f"STORYBOOK_RUNTIME_MANIFEST: PASS "
        f"({checked} texture payloads; "
        f"{len(data.get('entries', []))} total runtime entries)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
