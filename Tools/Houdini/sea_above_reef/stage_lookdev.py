"""Stage Melusina lookdev textures (dress + starskiff) into the game content tree.

Destination (Phase A2 convention area): Content/Melodia/Characters/Melusina/Textures/Clothes/
NEW FILES ONLY — refuses to overwrite any existing file (the T_MelusinaC_* set of
record must never be clobbered; Phase A2 owner question on the v22 set of record
is still open).

Run:  python Tools/Houdini/sea_above_reef/stage_lookdev.py
"""

import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import reef_common as rc  # noqa: E402

SRC = rc.PROJECT_ROOT / "Saved" / "Audit" / "melusina_lookdev" / "houdini_variants"
DST = rc.PROJECT_ROOT / "Content" / "Melodia" / "Characters" / "Melusina" / "Textures" / "Clothes"

# per-file import contract (Phase A2 binding notes)
CONTRACT = {
    "T_MelusinaC_DressShorewake_BaseColor": {"sRGB": True, "map": "BaseColor"},
    "T_MelusinaC_DressShorewake_Normal": {"sRGB": False, "map": "Normal (OpenGL Y+)"},
    "T_MelusinaC_DressShorewake_Emission": {"sRGB": False, "map": "Emissive (static)"},
    "T_MelusinaC_DressShorewake_Roughness": {"sRGB": False, "map": "Roughness"},
    "T_Starskiff_Hull_BaseColor": {"sRGB": True, "map": "BaseColor"},
    "T_Starskiff_Hull_Normal": {"sRGB": False, "map": "Normal (OpenGL Y+)"},
    "T_Starskiff_Hull_Roughness": {"sRGB": False, "map": "Roughness"},
    "T_Starskiff_Wake_Emission": {"sRGB": False, "map": "Emissive (static wake strip)"},
}


def main():
    DST.mkdir(parents=True, exist_ok=True)
    entries, refused = [], []
    for src in sorted(SRC.glob("T_MelusinaC_*.png")) + sorted(SRC.glob("T_Starskiff_*.png")):
        dst = DST / src.name
        if dst.exists():
            refused.append(src.name)
            print(f"[stage] REFUSED (exists): {dst.name}")
            continue
        shutil.copy2(src, dst)
        ok = rc.sha256_of(src) == rc.sha256_of(dst)
        entries.append({
            "file": str(dst.relative_to(rc.PROJECT_ROOT)).replace("\\", "/"),
            "source": str(src.relative_to(rc.PROJECT_ROOT)).replace("\\", "/"),
            "bytes": dst.stat().st_size,
            "sha256": dst_hash if (dst_hash := rc.sha256_of(dst)) else "",
            "verified": ok,
            "import": CONTRACT.get(src.stem, {"sRGB": "review", "map": "unlisted"}),
        })
        print(f"[stage] {src.name} -> Clothes/ ({'hash OK' if ok else 'HASH MISMATCH'})")

    payload = {
        "schema": "melodia.melusina_lookdev_stage.v1",
        "staged_root": str(DST.relative_to(rc.PROJECT_ROOT)).replace("\\", "/"),
        "refused_existing": refused,
        "binding_note": "holder binds at the MI instance layer via material_query "
                        "set_instance_parameters per specs/anim_presets/"
                        "melusina_v2_material_map.json; masters never edited",
        "files": entries,
    }
    out = SRC / "stage_manifest.json"
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    bad = [e for e in entries if not e["verified"]]
    print(f"[stage] {len(entries)} staged, {len(refused)} refused, "
          f"hash {len(entries) - len(bad)}/{len(entries)} OK -> {out.name}")


if __name__ == "__main__":
    main()
