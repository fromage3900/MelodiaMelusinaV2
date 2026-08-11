"""Dirty detection for MI preview loop captures.

Writes/reads:
  Saved/Portfolio/MaterialLoops/dirty_cache.json

Run standalone:
  python Content/Python/mi_preview_dirty.py
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import mi_preview_manifest as manifest_mod
import mi_preview_studio as studio

CACHE_PATH = studio.DIRTY_CACHE_JSON
HERO_REFRESH_DAYS = 7
PROOF_MI = "MI_ZenTrim_FlowersLots"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_json(path: Path) -> Any:
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _write_cache(data: dict) -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _png_frame_count(mi_id: str) -> int:
    out_dir = studio.output_dir_for_mi(mi_id)
    if not out_dir.is_dir():
        return 0
    return len(list(out_dir.glob("*.png")))


def _webm_mtime(mi_id: str) -> datetime | None:
    webm = studio.PROJECT_ROOT / "my-site-clean" / "generated" / "assets" / "material-loops" / f"{mi_id}.webm"
    if not webm.is_file():
        webm = studio.LOOPS_ROOT.parent.parent / "my-site-clean" / "generated" / "assets" / "material-loops" / f"{mi_id}.webm"
    if not webm.is_file():
        return None
    return datetime.fromtimestamp(webm.stat().st_mtime, tz=timezone.utc)


def fingerprint_entry(entry: dict[str, Any]) -> str:
    """Best-effort fingerprint; uses UE asset registry when in editor."""
    mi_id = entry["id"]
    asset_path = str(entry.get("asset_path") or "")
    profile = str(entry.get("profile") or "")
    mesh = str(entry.get("preview_mesh") or "")
    backdrop = str(entry.get("backdrop") or "")

    try:
        import unreal

        reg = unreal.AssetRegistryHelpers.get_asset_registry()
        data = reg.get_asset_by_object_path(asset_path)
        if data and data.is_valid():
            tag = ""
            for key in ("Saved", "Revision", "PackageFileSummaryVersion"):
                try:
                    val = data.get_tag_value(key)
                    if val:
                        tag = f"{key}:{val}"
                        break
                except Exception:
                    pass
            if tag:
                return f"{tag}|{profile}|{mesh}|{backdrop}"
    except ImportError:
        pass

    audit = _read_json(studio.PROJECT_ROOT / "Saved" / "Audit" / "material_instance_audit.json")
    if isinstance(audit, dict):
        for row in audit.get("materials") or []:
            if isinstance(row, dict) and row.get("name") == mi_id:
                return "|".join(
                    [
                        str(row.get("path") or asset_path),
                        str(row.get("shader_family") or profile),
                        mesh,
                        backdrop,
                    ]
                )

    return f"{asset_path}|{profile}|{mesh}|{backdrop}"


def is_capture_complete(mi_id: str) -> bool:
    return _png_frame_count(mi_id) >= studio.LOOP_FRAMES


def is_dirty(
    entry: dict[str, Any],
    cache: dict[str, Any],
    *,
    force_all: bool = False,
) -> tuple[bool, str]:
    if force_all:
        return True, "force_all"

    mi_id = entry["id"]
    fp = fingerprint_entry(entry)
    prev = (cache.get("entries") or {}).get(mi_id) or {}
    prev_fp = prev.get("fingerprint")
    frames = _png_frame_count(mi_id)

    if frames < studio.LOOP_FRAMES:
        return True, f"incomplete_frames:{frames}/{studio.LOOP_FRAMES}"

    if prev_fp != fp:
        return True, "fingerprint_changed"

    if entry.get("priority") == "hero":
        webm_time = _webm_mtime(mi_id)
        if webm_time is None:
            return True, "hero_missing_webm"
        age = datetime.now(timezone.utc) - webm_time
        if age > timedelta(days=HERO_REFRESH_DAYS):
            return True, "hero_stale_webm"

    return False, "clean"


def build_dirty_queue(
    *,
    force_all: bool = False,
    proof_only: bool = False,
    only: str | None = None,
) -> list[dict[str, Any]]:
    manifest = manifest_mod.load_manifest()
    entries = list(manifest.get("entries") or [])

    if proof_only or only:
        filt = PROOF_MI if proof_only else only
        entries = manifest_mod.filter_entries(manifest, only=filt)
        if not entries and proof_only:
            entries = manifest_mod.filter_entries(manifest, only=PROOF_MI)
        return entries

    cache_doc = _read_json(CACHE_PATH) or {"entries": {}}
    dirty: list[dict[str, Any]] = []
    for entry in entries:
        needs, reason = is_dirty(entry, cache_doc, force_all=force_all)
        if needs:
            row = dict(entry)
            row["dirty_reason"] = reason
            dirty.append(row)

    if not dirty:
        hero = next((e for e in entries if e.get("id") == PROOF_MI), None)
        if hero:
            row = dict(hero)
            row["dirty_reason"] = "fallback_proof"
            dirty.append(row)

    dirty.sort(key=lambda e: (0 if e.get("priority") == "hero" else 1, e.get("id", "")))
    return dirty


def mark_captured(entry: dict[str, Any], *, ok: bool = True, error: str | None = None) -> None:
    cache_doc = _read_json(CACHE_PATH) or {"entries": {}, "updated_at": _now_iso()}
    entries = cache_doc.setdefault("entries", {})
    mi_id = entry["id"]
    entries[mi_id] = {
        "fingerprint": fingerprint_entry(entry),
        "captured_at": _now_iso() if ok else entries.get(mi_id, {}).get("captured_at"),
        "frame_count": _png_frame_count(mi_id),
        "last_ok": ok,
        "last_error": error,
    }
    cache_doc["updated_at"] = _now_iso()
    _write_cache(cache_doc)


def write_dirty_report() -> dict[str, Any]:
    queue = build_dirty_queue()
    report = {
        "generated_at": _now_iso(),
        "dirty_count": len(queue),
        "next_dirty": [e["id"] for e in queue[:10]],
        "queue": [{"id": e["id"], "reason": e.get("dirty_reason")} for e in queue[:20]],
    }
    out = studio.LOOPS_ROOT / "dirty_queue.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def main() -> int:
    report = write_dirty_report()
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
