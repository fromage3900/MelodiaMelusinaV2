"""Audit the canonical Nikki render-volume contract in UE."""
from __future__ import annotations
import json
from pathlib import Path
from setup_nikki_render_post_process import BLENDABLES, LEVELS

def main() -> int:
    import unreal
    results = []
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for level in LEVELS:
        leaf = level.rsplit("/", 1)[-1]
        if not unreal.EditorAssetLibrary.does_asset_exist(f"{level}.{leaf}"):
            results.append({"level": level, "status": "missing"})
            continue
        les.load_level(level)
        ppv = next((a for a in eas.get_all_level_actors() or [] if a.get_actor_label() == "PPV_NikkiDream"), None)
        paths = [p for _, p in BLENDABLES if unreal.EditorAssetLibrary.does_asset_exist(p)]
        results.append({"level": level, "status": "ok" if ppv else "missing_volume",
                        "volume": ppv.get_actor_label() if ppv else None,
                        "unbound": bool(ppv.get_editor_property("unbound")) if ppv else False,
                        "blendable_assets": paths})
    report = {"ok": all(r["status"] in ("ok", "missing") for r in results), "levels": results}
    out = Path(__file__).resolve().parents[1] / ".." / "Saved" / "Audit" / "nikki_post_process_audit.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["ok"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
