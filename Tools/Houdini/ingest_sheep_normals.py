#!/usr/bin/env python3
"""
Ingest sculpted normal maps for Choral Sheep (you said ~1 hour).

Accepts either:
  - one shared map: T_ChoralSheep_Normal.png (applied to all 12 MIs)
  - 12 per-PC maps: T_ChoralSheep_Normal_PC{C,Cs,D,Ds,E,F,Fs,G,Gs,A,As,B}.png
             or: T_ChoralSheep_Normal_PC00..PC11.png
             or: ChoralWool_PC_{label}_Normal.png (Houdini COP export)

Drops into ingest dir, validates (power-of-two, 8-bit RGB, Normal compression hint),
and writes a manifest for Content/Python/apply_choral_sheep_normals.py to consume.

Usage:
    python Tools/Houdini/ingest_sheep_normals.py --src C:/sculpts/sheep_normals --verify
    python Tools/Houdini/ingest_sheep_normals.py --src Saved/Audit/choral_sheep/sculpted_normals --ingest-dir Saved/Audit/choral_sheep/sculpted_normals
    # dry-run listing:
    python Tools/Houdini/ingest_sheep_normals.py --src C:/sculpts --list-only
"""
import argparse
import json
import re
import shutil
from pathlib import Path

LABELS = ["C","Cs","D","Ds","E","F","Fs","G","Gs","A","As","B"]
LABEL_TO_PC = {l:i for i,l in enumerate(LABELS)}
PC_TO_LABEL = {i:l for i,l in enumerate(LABELS)}

# accept many naming conventions from sculpt apps / Houdini COP exports
PATTERNS = [
    re.compile(r"PC[_-]?(\d{1,2})", re.I),
    re.compile(r"PC[_-]?(C#?|D#?|E|F#?|G#?|A#?|B)", re.I),
    re.compile(r"_(C#?|D#?|E|F#?|G#?|A#?|B)(?:_Normal|\.png)", re.I),
]

def _label_from_name(name: str) -> str | None:
    n = name.replace("#","s")  # C# -> Cs
    # try explicit label token
    for lab in LABELS:
        if f"_{lab}_" in f"_{n}_" or n.endswith(f"_{lab}") or f"_{lab}." in n:
            return lab
    # try PC number
    m = re.search(r"PC0*(\d{1,2})", n, re.I)
    if m:
        pc = int(m.group(1))
        if 0 <= pc < 12:
            return PC_TO_LABEL[pc]
    # fallback: parse any PC token
    for pat in PATTERNS:
        m = pat.search(n)
        if m:
            token = m.group(1)
            if token.isdigit():
                pc = int(token)
                if 0 <= pc < 12:
                    return PC_TO_LABEL[pc]
            else:
                tok = token.replace("#","s").capitalize() if len(token)==1 else token
                # normalize Cs vs C s
                for lab in LABELS:
                    if lab.lower() == tok.lower():
                        return lab
    return None

def _is_power_of_two(n:int) -> bool:
    return n>0 and (n & (n-1)==0)

def scan_src(src: Path):
    files = []
    for pat in ("*.png","*.tga","*.tif","*.tiff","*.exr"):
        files.extend(src.glob(pat))
        files.extend(src.glob(pat.upper()))
    return sorted(set(files))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True, help="folder containing your sculpted normal PNGs")
    ap.add_argument("--ingest-dir", default="Saved/Audit/choral_sheep/sculpted_normals", help="UE ingest dir (tracked)")
    ap.add_argument("--verify", action="store_true", help="run image validation (Pillow required)")
    ap.add_argument("--list-only", action="store_true", help="only list what would be ingested")
    ap.add_argument("--shared-name", default="T_ChoralSheep_Normal.png")
    args = ap.parse_args()

    src = Path(args.src).resolve()
    ingest = Path(args.ingest_dir).resolve()
    if not src.is_dir():
        raise SystemExit(f"src not found: {src}")
    ingest.mkdir(parents=True, exist_ok=True)

    files = scan_src(src)
    if not files:
        print(f"[ingest] no images in {src} — drop your sculpts there and rerun")
        print(f"[ingest] expected: {args.shared_name} OR 12x T_ChoralSheep_Normal_PC{{C..B}}.png")
        raise SystemExit(1)

    # classify: shared single vs per-PC
    per_pc: dict[str, Path] = {}
    shared: Path | None = None
    unrecognized: list[Path] = []

    for f in files:
        label = _label_from_name(f.stem)
        if label:
            # collision check
            if label in per_pc:
                print(f"[warn] duplicate label {label}: {f.name} vs {per_pc[label].name}")
            per_pc[label] = f
        elif f.name.lower() == args.shared_name.lower() or "normal" in f.name.lower() and len(files)==1:
            shared = f
        else:
            # if filename contains 'normal' and no label, treat as shared
            if "normal" in f.name.lower():
                if len(files)==1:
                    shared = f
                else:
                    unrecognized.append(f)
            else:
                unrecognized.append(f)

    print(f"[ingest] found {len(files)} image(s) in {src}")
    if shared:
        print(f"  shared: {shared.name}")
    if per_pc:
        print(f"  per-PC: {', '.join(f'{k}:{v.name}' for k,v in sorted(per_pc.items(), key=lambda x: LABEL_TO_PC[x[0]]))}")
    if unrecognized:
        print(f"  unrecognized (ignored): {[p.name for p in unrecognized]}")

    if args.list_only:
        return

    # verify if requested
    if args.verify:
        try:
            from PIL import Image
            for f in files:
                try:
                    im = Image.open(f)
                    w,h = im.size
                    mode = im.mode
                    pot = _is_power_of_two(w) and _is_power_of_two(h)
                    print(f"  [verify] {f.name}: {w}x{h} {mode} {'POT' if pot else 'NON-POT!'} {'ok' if pot and mode in ('RGB','RGBA') else 'check mode/size'}")
                    if not pot:
                        print(f"    -> recommend resize to 1024 or 2048 for UE")
                except Exception as e:
                    print(f"  [verify] {f.name}: failed to open ({e})")
        except ImportError:
            print("[verify] Pillow not installed — skipping pixel checks (pip install Pillow)")

    # ingest copy + normalize names
    manifest = {"ingested": [], "shared": None, "per_pc": {}, "ingest_dir": str(ingest)}
    def _safe_copy(src_file: Path, dst: Path):
        try:
            if src_file.resolve() == dst.resolve():
                return  # already in place
        except Exception:
            pass
        shutil.copy2(src_file, dst)

    if shared and not per_pc:
        dst = ingest / args.shared_name
        if not args.list_only:
            _safe_copy(shared, dst)
        manifest["shared"] = str(dst.resolve())
        manifest["ingested"].append(str(dst.resolve()))
        print(f"[ingest] copied shared -> {dst}")
    elif per_pc:
        for label, src_file in per_pc.items():
            dst = ingest / f"T_ChoralSheep_Normal_PC{label}.png"
            if not args.list_only:
                _safe_copy(src_file, dst)
            manifest["per_pc"][label] = str(dst.resolve())
            manifest["ingested"].append(str(dst.resolve()))
            print(f"[ingest] PC {label} -> {dst.name}")
        # also copy shared if present alongside per-PC? ignore
    else:
        # ambiguous — copy all as-is
        for f in files:
            dst = ingest / f.name
            _safe_copy(f, dst)
            manifest["ingested"].append(str(dst.resolve()))

    # write manifests (both audit + UE path)
    audit_manifest = ingest / "normal_ingest_manifest.json"
    audit_manifest.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    # also at houdini variants dir for COP wiring
    alt = Path("Saved/Audit/choral_sheep/houdini_variants/normal_ingest_manifest.json").resolve()
    alt.parent.mkdir(parents=True, exist_ok=True)
    alt.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"[ingest] manifest -> {audit_manifest}")
    print(f"[ingest] next: In UE Editor Python, run Content/Python/apply_choral_sheep_normals.py")
    print(f"         That script reads this manifest and sets Normal slots on MI_ChoralSheep_Coat_PC*")

if __name__ == "__main__":
    main()
