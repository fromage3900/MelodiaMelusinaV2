"""Copy Electric Dreams closure assets from G: to C: (2026-08-13).

Owner decision (2026-08-13): use ED meshes/systems as building blocks, NOT the
full map. This copies:
  - Asmbly external-actor packages (37) referenced by the Asmbly assembly umaps
    that are already on C: (manifest subset, sources verified on G:).
  - Audible ambience subset under /Game/Audio/Aud_Source/: fx_Amb_Quad,
    fx_Amb_Spot, fx_Prop (pure jungle/riverbed loops + one-shots). The
    Soundscape plugin palettes (fx_Amb_SoundScape), demo music (mx_Music),
    datalayers, demo blueprints and the 4 km^2 ED world actors are intentionally
    NOT copied (owner: "not the full map").

Always mirrors G: source RELATIVE paths (proper case) so the registry resolves
them case-insensitively; the old manifest `dest` field is NOT used (it has a
double-dot `..uasset` bug).

Usage:
  python Tools/copy_ed_closures_20260813.py            # copy all (idempotent)
  python Tools/copy_ed_closures_20260813.py --dry-run  # report only
"""
import argparse
import json
import os
import shutil
import sys

C_CONTENT = r"C:\EnvironmentPortfolio\BS_GodFile\Content"
G_CONTENT = r"G:\EnvironmentPortfolio\BS_GodFile\Content"
MANIFEST = os.path.join(os.path.dirname(__file__), "..", "Saved",
                        "stale_copy_manifest_20260812.json")

AUDIO_SUBFOLDERS = ["fx_Amb_Quad", "fx_Amb_Spot", "fx_Prop"]

# Tiny packages referenced by assets already resident on C: (Megascans leakage
# decals -> mask texture; AudioModulation control buses -> volume curve).
TAIL_PKGS = ["textures/envrnd/t_softsquare_01_m", "volume"]


def copy_file(src, dst, dry_run):
    if not os.path.exists(src):
        return ("MISSING-SRC", src)
    if os.path.exists(dst):
        return ("SKIP-EXISTS", dst)
    if dry_run:
        return ("WOULD-COPY", dst)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst)
    if os.path.getsize(src) != os.path.getsize(dst):
        return ("SIZE-MISMATCH", dst)
    return ("COPIED", dst)


def copy_manifest_subset(manifest, subset_pred, dry_run):
    if not os.path.exists(MANIFEST):
        print("manifest missing:", MANIFEST)
        return
    with open(MANIFEST) as f:
        entries = json.load(f)
    picked = [e for e in entries if subset_pred(e["pkg"])]
    results = {}
    for e in sorted(picked, key=lambda x: x["source"].lower()):
        src = e["source"]
        rel = os.path.relpath(src, G_CONTENT)
        dst = os.path.join(C_CONTENT, rel)
        tag, detail = copy_file(src, dst, dry_run)
        results.setdefault(tag, []).append(detail)
        if tag not in ("SKIP-EXISTS",):
            print(f"{tag:12s} {rel}")
    for tag in sorted(results):
        print(f"{tag}: {len(results[tag])}")
    return results


def copy_audio_subset(dry_run):
    results = {}
    for folder in AUDIO_SUBFOLDERS:
        src_dir = os.path.join(G_CONTENT, "Audio", "Aud_Source", folder)
        if not os.path.isdir(src_dir):
            print(f"missing audio source dir: {src_dir}")
            continue
        for root, _dirs, files in os.walk(src_dir):
            for fn in sorted(files):
                src = os.path.join(root, fn)
                rel = os.path.relpath(src, G_CONTENT)
                dst = os.path.join(C_CONTENT, rel)
                tag, detail = copy_file(src, dst, dry_run)
                results.setdefault(tag, []).append(detail)
                if tag not in ("SKIP-EXISTS",):
                    print(f"{tag:12s} {rel}")
    for tag in sorted(results):
        print(f"{tag}: {len(results[tag])}")
    return results


def copy_tail_pkgs(dry_run):
    results = {}
    for pkg in TAIL_PKGS:
        src = os.path.join(G_CONTENT, pkg + ".uasset")
        dst = os.path.join(C_CONTENT, pkg + ".uasset")
        tag, detail = copy_file(src, dst, dry_run)
        results.setdefault(tag, []).append(detail)
        print(f"{tag:12s} {pkg}.uasset")
    for tag in sorted(results):
        print(f"{tag}: {len(results[tag])}")
    return results


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    print("== Asmbly external-actor closure ==")
    copy_manifest_subset(MANIFEST,
                         lambda p: p.startswith("__externalactors__/asmbly/")
                         or p.startswith("asmbly/"), args.dry_run)
    print("== Audio ambience subset (fx_Amb_Quad / fx_Amb_Spot / fx_Prop) ==")
    copy_audio_subset(args.dry_run)
    print("== Tail packages (resident-asset refs) ==")
    copy_tail_pkgs(args.dry_run)
    print("done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
