#!/usr/bin/env python3
"""Faraway Mother alignment diagnostic (integration spec §8.2).

Writes T_FarawayMother_AlignmentDiagnostic.png in the exact pixel convention of
faraway_static_field.py (column = U = world X, row = V = world Y, row 0 = -Y):

  corner patches  (-X,-Y) red   (+X,-Y) green   (-X,+Y) blue   (+X,+Y) yellow
  central cross   white, marks world (0, 0)
  seam stripe     the real ResonantSeamWay channel, magenta

The corners are asymmetric on purpose: |Chladni(3,5)| is symmetric under a V
flip, so the field alone cannot reveal a mirrored import.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image

from faraway_static_field import DEFAULT_OUT, build_field

WORLD_HALF_UU = 400000.0
PATCH_PX = 48
CROSS_HALF_WIDTH_PX = 4

CORNERS = {
    "neg_x_neg_y": ((255, 0, 0), (0, 0)),
    "pos_x_neg_y": ((0, 255, 0), (1, 0)),
    "neg_x_pos_y": ((0, 0, 255), (0, 1)),
    "pos_x_pos_y": ((255, 255, 0), (1, 1)),
}


def build(res: int) -> tuple[np.ndarray, dict]:
    img = np.zeros((res, res, 3), dtype=np.uint8)

    _, _, _, seam = build_field(res, 3, 5)
    img[seam > 0.5] = (255, 0, 255)

    c = res // 2
    img[c - CROSS_HALF_WIDTH_PX:c + CROSS_HALF_WIDTH_PX, :] = (255, 255, 255)
    img[:, c - CROSS_HALF_WIDTH_PX:c + CROSS_HALF_WIDTH_PX] = (255, 255, 255)

    markers = {}
    patch_center_uu = WORLD_HALF_UU - (PATCH_PX / 2.0) / res * 2.0 * WORLD_HALF_UU
    for name, (rgb, (ux, vy)) in CORNERS.items():
        cols = slice(res - PATCH_PX, res) if ux else slice(0, PATCH_PX)
        rows = slice(res - PATCH_PX, res) if vy else slice(0, PATCH_PX)
        img[rows, cols] = rgb
        markers[name] = {
            "rgb": list(rgb),
            "world_xy_uu": [patch_center_uu if ux else -patch_center_uu,
                            patch_center_uu if vy else -patch_center_uu],
        }
    markers["center_cross"] = {"rgb": [255, 255, 255], "world_xy_uu": [0.0, 0.0]}
    return img, markers


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--res", type=int, default=1024)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    img, markers = build(args.res)
    path = args.out / "T_FarawayMother_AlignmentDiagnostic.png"
    Image.fromarray(img, mode="RGB").save(path)

    manifest = {
        "schema": "melodia.faraway_alignment_diagnostic/v1",
        "generator": "Tools/Houdini/vdm_fabric_mountains/faraway_alignment_diagnostic.py",
        "resolution": [args.res, args.res],
        "uv_mapping": {"u": "(WorldX + 400000) / 800000", "v": "(WorldY + 400000) / 800000"},
        "known_seam": "u == v is a nodal line of Chladni(3,5): world X == Y diagonal",
        "markers": markers,
        "output": path.name,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }
    (args.out / "alignment_diagnostic_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
