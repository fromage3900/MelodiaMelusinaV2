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
CANONICAL_TEXTURE_DEST = "/Game/Melodia/UI/Textures/Storybook"
CANONICAL_ASSET_NAMES = {
    "storybook.sparkle": "storybook_sparkle",
    "storybook.waypoint": "storybook_waypoint",
    "storybook.player_pin": "storybook_player_pin",
    "storybook.speech_tail": "storybook_speech_tail",
    "storybook.menu_diamond": "storybook_menu_diamond",
    "storybook.bird_crest": "storybook_bird_crest",
    "storybook.note_head": "storybook_note_head",
}


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
    seen_asset_names: set[str] = set()

    texture_dest = data.get("ue", {}).get("texture_dest")
    if texture_dest != CANONICAL_TEXTURE_DEST:
        failures.append(
            f"texture_dest {texture_dest!r} != canonical {CANONICAL_TEXTURE_DEST!r}"
        )

    for entry in data.get("entries", []):
        source_svg = entry.get("source_svg")
        if source_svg and not (ROOT / source_svg).is_file():
            failures.append(f"{entry['id']}: missing source_svg {source_svg}")

        if entry.get("runtime_type") != "texture":
            continue

        expected_asset_name = CANONICAL_ASSET_NAMES.get(entry["id"])
        asset_name = entry.get("asset_name")
        if expected_asset_name is None:
            failures.append(f"{entry['id']}: texture entry has no canonical mapping")
        elif asset_name != expected_asset_name:
            failures.append(
                f"{entry['id']}: asset_name {asset_name!r} != {expected_asset_name!r}"
            )
        if asset_name in seen_asset_names:
            failures.append(f"{entry['id']}: duplicate asset_name {asset_name!r}")
        if asset_name:
            seen_asset_names.add(asset_name)

        ue_dest = entry.get("ue_dest", texture_dest)
        if ue_dest != CANONICAL_TEXTURE_DEST:
            failures.append(
                f"{entry['id']}: ue_dest {ue_dest!r} would create a parallel namespace"
            )

        payload = ROOT / entry["png_b64"]
        if not payload.is_file():
            failures.append(f"{entry['id']}: missing payload {entry['png_b64']}")
            continue

        try:
            encoded = payload.read_text(encoding="ascii").strip()
            raw = base64.b64decode(encoded, validate=True)
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
