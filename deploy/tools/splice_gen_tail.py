# -*- coding: utf-8 -*-
"""Splice UTF-8-clean tail from revert copy; merge tail-only additions from current."""
from __future__ import annotations

import re
from pathlib import Path

DEPLOY = Path(__file__).resolve().parents[1]
CURRENT = DEPLOY / "surreal_architecture_gen.py"
REVERT = Path(__file__).resolve().parents[2].parent / "BS_GodFile_revert" / "deploy" / "surreal_architecture_gen.py"
MARKER = 'return _spawn_mesh_from_data("EscherRecursivePortal", verts, [], faces)'

# Class registrations present in current tail but absent from revert tail.
EXTRA_CLASS_LINES = [
    "    SURREAL_ARCH_OT_preset_scifi_airlock,",
    "    SURREAL_ARCH_OT_preset_filigree_vine_panel,",
    "    SURREAL_ARCH_OT_preset_filigree_geometric_panel,",
    "    SURREAL_ARCH_OT_preset_filigree_rail_vine,",
    "    SURREAL_ARCH_OT_preset_art_nouveau_facade,",
    "    SURREAL_ARCH_OT_preset_renaissance_piazza,",
]
ANCHOR = "    SURREAL_ARCH_OT_preset_covered_bazaar,"


def split_at_marker(path: Path) -> tuple[list[str], list[str]]:
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    idx = next(i for i, ln in enumerate(lines) if MARKER in ln)
    return lines[: idx + 1], lines[idx + 1 :]


def inject_class_registrations(tail: list[str]) -> list[str]:
    out: list[str] = []
    injected = False
    for ln in tail:
        out.append(ln)
        if not injected and ANCHOR in ln:
            out.append("    # v2.115+ — filigree + graph presets\n")
            out.extend(f"{x}\n" for x in EXTRA_CLASS_LINES)
            injected = True
    if not injected:
        raise RuntimeError(f"anchor not found in tail: {ANCHOR!r}")
    return out


def main() -> None:
    prefix, _bad = split_at_marker(CURRENT)
    _, good = split_at_marker(REVERT)
    good = inject_class_registrations(good)
    merged = prefix + good
    text = "".join(merged)
    text = text.replace('"version": (2, 116, 0)', '"version": (2, 119, 0)', 1)
    CURRENT.write_text(text, encoding="utf-8", newline="\n")
    print(f"wrote {len(merged)} lines")


if __name__ == "__main__":
    main()
