"""Verify the Figma-to-Unreal Melodia battle UI asset contract.

This is deliberately read-only. Run it before import to catch missing exports and
after import to prove the canonical Unreal asset paths were created:

    UnrealEditor-Cmd.exe BS_GodFile.uproject \
      -ExecutePythonScript=Content/Python/verify_melodia_game_ui_assets.py
"""
from __future__ import annotations

import json
from pathlib import Path

import unreal


ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = ROOT / "pipeline" / "figma" / "figma_game_ui_manifest.json"
REPORT_PATH = ROOT / "Saved" / "Melodia" / "figma_ui_asset_verify.json"


def _expected_asset_path(entry: dict[str, str]) -> str:
    stem = Path(entry["filename"]).stem
    destination = entry["ue_dest"].rstrip("/")
    return f"{destination}/{stem}.{stem}"


def main() -> bool:
    if not MANIFEST_PATH.is_file():
        unreal.log_error(f"[MelodiaUIAssets] Missing manifest: {MANIFEST_PATH}")
        return False

    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    checks: list[dict[str, object]] = []
    for entry in manifest.get("entries", []):
        source = Path(entry["source"])
        asset_path = _expected_asset_path(entry)
        source_exists = source.is_file() and source.stat().st_size > 0
        asset_exists = unreal.EditorAssetLibrary.does_asset_exist(asset_path)
        checks.append({
            "figma": entry["figma"],
            "source": str(source),
            "source_exists": source_exists,
            "asset_path": asset_path,
            "asset_exists": asset_exists,
        })

    report = {
        "manifest": str(MANIFEST_PATH),
        "asset_count": len(checks),
        "source_exports_ok": all(bool(check["source_exists"]) for check in checks),
        "canonical_assets_ok": all(bool(check["asset_exists"]) for check in checks),
        "checks": checks,
    }
    report["ok"] = report["source_exports_ok"] and report["canonical_assets_ok"]
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    unreal.log(f"[MelodiaUIAssets] Wrote {REPORT_PATH}")
    unreal.log(f"[MelodiaUIAssets] ok={report['ok']} assets={len(checks)}")
    return bool(report["ok"])


if __name__ == "__main__":
    main()
