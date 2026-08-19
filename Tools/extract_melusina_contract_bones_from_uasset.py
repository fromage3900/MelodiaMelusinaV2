"""Extract the canonical Melusina reference-bone contract from the UE package.

This is a read-only fallback for environments where the Unreal Python commandlet
cannot start because the editor/DDC service is unhealthy.  It reads the cooked
``FReferenceSkeleton`` payload from the existing ``SK_Melusina_Skeleton.uasset``;
it never edits or rewrites the asset.  The normal authority remains
``Content/Python/export_melusina_contract_bones.py`` when the editor is healthy.
"""

from __future__ import annotations

import argparse
import json
import struct
from pathlib import Path


EXPECTED_BONE_COUNT = 465
DEFAULT_SKELETON = Path("Content/Melodia/Characters/Melusina/SK_Melusina_Skeleton.uasset")
DEFAULT_OUTPUT = Path("specs/anim_presets/melusina_contract_bones.json")
DEFAULT_MAP = Path("specs/anim_presets/melusina_arp_to_contract_bones.json")
KNOWN_CONTRACT_NAMES = {"root", "c_traj", "root_x", "c_spine_01_x", "head_x", "DEF_eye_L"}
OBSERVED_GROUP_MAP = {
    "DEF-face": "ORG-face",
    "faceit_main": "ORG-face",
    "jawbone_x": "jaw",
    "subneck_twist_1_x": "neck_x",
}
OBSERVED_BONE_MAP = {}
for _finger in ("index", "middle", "ring", "pinky", "thumb"):
    for _segment in ("base", "2", "3"):
        for _side in ("l", "r"):
            OBSERVED_BONE_MAP[f"{_finger}1_base_ref_{_side}" if _segment == "base" else f"{_finger}{_segment}_ref_{_side}"] = (
                f"{_finger}1_base_{_side}" if _segment == "base" else f"{_finger}{_segment}_{_side}"
            )
OBSERVED_BONE_MAP["root_ref_x"] = "root"


def _read_serialized_reference_skeleton(data: bytes) -> list[str]:
    """Read the UE5 FReferenceSkeleton name payload.

    The package stores the array count followed by a compact per-bone record:
    FString name plus three fixed-width fields.  We locate the unique 465-entry
    array by its count and validate the complete record sequence before using it.
    """

    count_bytes = struct.pack("<I", EXPECTED_BONE_COUNT)
    candidates: list[list[str]] = []
    cursor = 0
    while True:
        cursor = data.find(count_bytes, cursor)
        if cursor < 0:
            break
        # The array has a small version/metadata prelude between the count and
        # the first FString.  Probe only that bounded prelude so unrelated 465
        # integers elsewhere in the package cannot be mistaken for the rig.
        for delta in range(4, 65):
            pos = cursor + delta
            names: list[str] = []
            try:
                for _ in range(EXPECTED_BONE_COUNT):
                    if pos + 4 > len(data):
                        raise ValueError("truncated FString length")
                    length = struct.unpack_from("<I", data, pos)[0]
                    pos += 4
                    if not 1 <= length <= 128 or pos + length > len(data):
                        raise ValueError("invalid FString length")
                    if data[pos + length - 1] != 0:
                        raise ValueError("FString is not null terminated")
                    name = data[pos : pos + length - 1].decode("utf-8")
                    if not name or any(ord(ch) < 32 for ch in name):
                        raise ValueError("invalid bone name")
                    names.append(name)
                    pos += length + 12
            except (UnicodeDecodeError, ValueError, struct.error):
                continue

            if len(set(names)) == EXPECTED_BONE_COUNT and KNOWN_CONTRACT_NAMES.issubset(names):
                candidates.append(names)
                break
        cursor += 4

    if len(candidates) != 1:
        raise RuntimeError(f"Expected one validated {EXPECTED_BONE_COUNT}-bone payload; found {len(candidates)}")
    return candidates[0]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skeleton", type=Path, default=DEFAULT_SKELETON)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--mapping", type=Path, default=DEFAULT_MAP)
    parser.add_argument("--expected-bone-count", type=int, default=465)
    parser.add_argument(
        "--skeleton-path",
        default="/Game/Melodia/Characters/Melusina/SK_Melusina_Skeleton",
        help="UE asset path to record in the output; useful for the 464-bone source rig.",
    )
    parser.add_argument("--target-bone-count", type=int)
    args = parser.parse_args()

    global EXPECTED_BONE_COUNT
    EXPECTED_BONE_COUNT = args.expected_bone_count
    data = args.skeleton.read_bytes()
    bone_names = _read_serialized_reference_skeleton(data)
    mapping = json.loads(args.mapping.read_text(encoding="utf-8"))
    result = {
        "schema_version": 1,
        "source": str(args.skeleton).replace("\\", "/"),
        "skeleton": args.skeleton_path,
        "bone_count": len(bone_names),
        "target_bone_count": args.target_bone_count or len(bone_names),
        "bone_names": bone_names,
        "name_style": "underscore_or_contract_hyphen_face_names",
        "units": "centimeters",
        "authority": "serialized FReferenceSkeleton read-only extraction",
        "ue_python_authority": "Content/Python/export_melusina_contract_bones.py",
        "semantic_map": mapping.get("semantic_map", {}),
        "weight_group_map": OBSERVED_GROUP_MAP,
        "bone_map": OBSERVED_BONE_MAP,
        "synthetic_bones": ["Retopo_Cube_003_001"],
        "drop": mapping.get("drop", []),
        "dot_rule": mapping.get("dot_rule", {}),
        "unit_rule": mapping.get("unit_rule", {}),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "bone_count": len(bone_names)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
