#!/usr/bin/env python3
"""
Ingest Houdini grooms for UE Groom plugin.

Scans Saved/Audit/choral_sheep/grooms for Groom_ChoralSheep_PC_{label}.abc
Validates placeholder vs real Alembic (real ABC starts with Ogawa, placeholder is text),
writes a manifest for Content/Python/apply_choral_sheep_grooms.py.

Usage:
    python Tools/Houdini/ingest_grooms.py --verify
    python Tools/Houdini/ingest_grooms.py --src Saved/Audit/choral_sheep/grooms --verify
"""
import argparse
import json
from pathlib import Path

LABELS = ["C","Cs","D","Ds","E","F","Fs","G","Gs","A","As","B"]

def _is_real_abc(p: Path) -> bool:
    try:
        head = p.read_bytes()[:200]
        # Real Alembic Ogawa starts with binary HDF5/Alembic magic, not '#'
        if head.startswith(b"# groom"):
            return False
        # rudimentary: real abc is not utf-8 decodable as short text
        try:
            text = head.decode("utf-8")
            if "Ogawa" in text or "Alembic" in text:
                return True
        except Exception:
            return True  # binary = real
        return head[:1] not in (b"#", b"{")
    except Exception:
        return False

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default="Saved/Audit/choral_sheep/grooms")
    ap.add_argument("--verify", action="store_true")
    args = ap.parse_args()
    src = Path(args.src).resolve()
    src.mkdir(parents=True, exist_ok=True)
    abcs = sorted(src.glob("Groom_ChoralSheep_PC_*.abc"))
    jss = sorted(src.glob("Groom_ChoralSheep_PC_*.json"))
    print(f"[groom ingest] src {src}")
    print(f"  ABC: {len(abcs)} / 12")
    for p in abcs:
        real = _is_real_abc(p)
        print(f"   {p.name} {p.stat().st_size}b {'REAL' if real else 'PLACEHOLDER (hython needed for strands)'}")
    if args.verify:
        for p in jss:
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                print(f"  JSON {p.name}: clump {data.get('wool_clump_scale')} curl {data.get('curl')} len {data.get('length_cm')}cm")
            except Exception as e:
                print(f"  JSON {p.name} bad: {e}")
    # manifest
    manifest = {
        "schema": "melodia.groom_ingest.v1",
        "grooms_dir": str(src),
        "ue_groom_dir": "/Game/Melodia/Companions/ChoralSheep/Grooms/",
        "cards_fbx_dir": str(src),
        "tracks": [
            {"label": p.stem.split("_PC_")[-1], "abc": str(p.resolve()), "json": str((src / f"{p.stem}.json").resolve()), "real": _is_real_abc(p)}
            for p in abcs
        ],
        "contact_sheet": str((src / "_Groom_ContactSheet.png").resolve()) if (src / "_Groom_ContactSheet.png").is_file() else None,
        "note": "Placeholders verify LOD binding; real strands require hython cook of choral_sheep_groom.hipnc",
    }
    mf = src / "groom_ingest_manifest.json"
    mf.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"[groom ingest] manifest -> {mf}")
    print(f"[groom ingest] next: In UE Editor Python exec Content/Python/apply_choral_sheep_grooms.py (will report placeholders vs real)")

if __name__ == "__main__":
    main()
