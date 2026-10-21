"""Spawn Sir Melodious perches from a Houdini-cooked perches.json manifest.

The manifest is written by Saved/HoudiniFoundry/CathedralConvergence_20261016/export_perches.py. Each row is one
BP_SirPerch (ASirPerchPoint) placement on a fountain spire or lancet apex.

Differences from setup_sir_melodious_perches.py / sir_perch_panel.spawn_missing (both left untouched):
  * placements come from the manifest, not a hand-typed coordinate dict;
  * NO ground snap - these perches are elevated on purpose;
  * rows with clear=false are never spawned.

Usage:
  python Content/Python/spawn_perches_from_manifest.py <perches.json>            # dry run (default), reads files only
  (inside the editor)  spawn_perches_from_manifest.apply(path, approved=True)    # owner-approved only

The UE conversion in the manifest (ue_cm_unverified) is UNVERIFIED until the first import of the staged FBX proves the
axis/handedness; check one perch against its fountain before spawning the rest. Dry-run is the only mode exercised so far.
"""
import json
import sys
from pathlib import Path

BP_PATH = "/Game/Melodia/Characters/SirMelodious/Perch/BP_SirPerch"
REPORT = Path(__file__).resolve().parents[2] / "Saved" / "Audit" / "perch_manifest_spawn_report.json"


def load(path):
    doc = json.loads(Path(path).read_text(encoding="utf-8"))
    rows = [r for r in doc["rows"] if r.get("clear")]
    skipped = [r["id"] for r in doc["rows"] if not r.get("clear")]
    return doc, rows, skipped


def dry_run(path):
    doc, rows, skipped = load(path)
    out = {"mode": "dry-run", "manifest": str(path), "spec": doc.get("spec"), "would_spawn": len(rows), "skipped_blocked": skipped,
           "class": BP_PATH, "ue_conversion": doc["conventions"]["ue_conversion"],
           "sample": [{"label": r["label"], "location_cm": r["ue_cm_unverified"], "yaw": r["ue_yaw_unverified"]} for r in rows[:5]]}
    print(json.dumps(out, indent=1))
    return out


def apply(path, approved=False):
    """Spawn in the open editor level. Refuses without approved=True. Skips labels that already exist."""
    if not approved:
        return {"ok": False, "error": "owner approval required (approved=True)"}
    try:
        import unreal
    except ImportError:
        return {"ok": False, "error": "not running inside the Unreal editor"}
    doc, rows, skipped = load(path)
    cls = unreal.EditorAssetLibrary.load_blueprint_class(BP_PATH) or getattr(unreal, "SirPerchPoint", None)
    if cls is None:
        return {"ok": False, "error": "BP_SirPerch / SirPerchPoint class not found"}
    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    existing = {a.get_actor_label() for a in subsystem.get_all_level_actors()}
    spawned, kept, errors = [], [], []
    for r in rows:
        if r["label"] in existing:
            kept.append(r["label"])
            continue
        try:
            x, y, z = r["ue_cm_unverified"]
            actor = unreal.EditorLevelLibrary.spawn_actor_from_class(cls, unreal.Vector(x, y, z), unreal.Rotator(0, 0, r["ue_yaw_unverified"]))
            actor.set_actor_label(r["label"])
            spawned.append(r["label"])
        except Exception as exc:  # report, keep going
            errors.append(f"{r['label']}: {exc}")
    out = {"ok": not errors, "spawned": len(spawned), "already_present": len(kept), "errors": errors, "skipped_blocked": skipped}
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(out, indent=1), encoding="utf-8")
    return out


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    dry_run(sys.argv[1])
