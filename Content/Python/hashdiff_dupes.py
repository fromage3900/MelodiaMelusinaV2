"""Hash-diff analysis of duplicate content roots for quarantine report."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONTENT = PROJECT_ROOT / "Content"
REPORT_PATH = PROJECT_ROOT / "Saved" / "Audit" / "dupe_root_hashdiff.json"

# Define the 7 duplicate root pairs for comparison
DUPE_ROOTS = [
    # (dupe_root, primary_root) - comparing dupe against primary
    ("_PROJECT", "Melodia/_PROJECT"),  # _PROJECT vs Melodia/_PROJECT
    ("Library", "EnvSandbox/Library"),   # Library/Migrated vs EnvSandbox/Library/Migrated
    ("Characters/Melusina", "Melodia/Characters/Melusina"),
    ("TurnBasedJRPGTemplate", "_ThirdParty/TurnBasedJRPGTemplate"),
    ("Art", "_PROJECT/Art"),
    ("Actor_BP", "Melodia/Actor_BP"),
    ("Game_BP", "Melodia/Game_BP"),
]

def get_file_hash(path: Path) -> str:
    """Compute SHA256 hash of a file."""
    if not path.exists() or not path.is_file():
        return ""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()[:12]  # Short hash

def scan_uassets(root: Path) -> dict:
    """Scan all uasset files in a root, returning stem->(hash, size, mtime) mapping."""
    result = {}
    if not root.exists():
        return result
    for p in root.rglob("*.uasset"):
        rel = p.relative_to(CONTENT)
        stem = p.stem
        result[rel.as_posix()] = {
            "hash": get_file_hash(p),
            "size_kb": round(p.stat().st_size / 1024, 1),
            "mtime": datetime.fromtimestamp(p.stat().st_mtime, timezone.utc).isoformat(),
        }
    return result

def compare_roots(dupe_path: str, primary_path: str) -> dict:
    """Compare dupe root against primary root."""
    dupe_root = CONTENT / dupe_path
    primary_root = CONTENT / primary_path
    
    dupe_assets = scan_uassets(dupe_root)
    primary_assets = scan_uassets(primary_root)
    
    # Build stem->locations mapping for quick lookup
    primary_by_stem = defaultdict(list)
    for path, meta in primary_assets.items():
        stem = Path(path).stem
        primary_by_stem[stem].append((path, meta))
    
    dupe_by_stem = defaultdict(list)
    for path, meta in dupe_assets.items():
        stem = Path(path).stem
        dupe_by_stem[stem].append((path, meta))
    
    verdicts = {
        "identical_dupe": [],      # Same hash (exact duplicate)
        "unique_only_primary": [], # Only exists in primary
        "unique_only_dupe": [],    # Only exists in dupe
        "newer_here": [],          # Different hashes/sizes
        "size_comparison": {},     # Detailed size/hash comparison
    }
    
    # Check dupe assets against primary
    for path, dupe_meta in dupe_assets.items():
        stem = Path(path).stem
        primary_matches = primary_by_stem.get(stem, [])
        
        identical = False
        newer = False
        
        for primary_path_match, primary_meta in primary_matches:
            if dupe_meta["hash"] and dupe_meta["hash"] == primary_meta["hash"]:
                identical = True
                break
            elif dupe_meta["size_kb"] != primary_meta["size_kb"]:
                newer = True
        
        if identical:
            verdicts["identical_dupe"].append(path)
        elif primary_matches and newer:
            verdicts["newer_here"].append({
                "dupe": path,
                "dupe_size_kb": dupe_meta["size_kb"],
                "dupe_mtime": dupe_meta["mtime"],
                "primary_size_kb": primary_matches[0][1]["size_kb"],
                "primary_mtime": primary_matches[0][1]["mtime"],
            })
        else:
            verdicts["unique_only_dupe"].append(path)
    
    # Check primary-only assets
    for path, meta in primary_assets.items():
        stem = Path(path).stem
        if stem not in dupe_by_stem:
            verdicts["unique_only_primary"].append(path)
    
    return verdicts

def main():
    report = {"generated_at": datetime.now(timezone.utc).isoformat(), "roots": {}}
    
    for dupe, primary in DUPE_ROOTS:
        result = compare_roots(dupe, primary)
        report["roots"][f"{dupe} vs {primary}"] = result
    
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Hash-diff report: {REPORT_PATH}")
    print(f"Roots analyzed: {len(DUPE_ROOTS)}")
    return report

if __name__ == "__main__":
    main()