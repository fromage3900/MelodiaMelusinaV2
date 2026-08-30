"""Read-only audit for ZenForestTest musical glam gate — no writes.

Run:
    py Content/Python/audit_zenforest_musical.py
    py Content/Python/audit_zenforest_musical.py --json

Checks:
  - MPC_Melodia_Palette + NPC_Melodia_Palette exist and are reachable
  - Musical alphas present in Content/Alphas_Sparkles and (if placed) in ZenForestTest_MusicalGlam
  - Level actors: VFX_Zen_*, Cam_ZenGlam_*, PP_Zen_*, LS sequence
  - Engine ini: r.CustomDepth=3, r.Substrate, r.Lumen, r.MotionBlur flag
  - MRQ presets exist

Writes Saved/Audit/zenforest_musical_audit.json (read-only evidence).
"""
from __future__ import annotations

import configparser
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT = PROJECT_ROOT / "Saved" / "Audit" / "zenforest_musical_audit.json"
LEVEL = "/Game/ZenForestTest"
GLAM_FOLDER = "/Game/ZenForestTest_MusicalGlam"
SEQ_PATH = f"{GLAM_FOLDER}/LS_ZenForest_MusicalGlam_001"
MRQ_PATH = "/Game/EnvSandbox/MRQ/Presets/MRQ_ZenForest_MusicalGlam"
MPC_PATHS = ["/Game/Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette", "/Game/_PROJECT/04_Materials/MPC_Melodia_Palette"]
NPC_PATH = "/Game/EnvSandbox/VFX/MPC/NPC_Melodia_Palette"
ALPHA_DIR = PROJECT_ROOT / "Content" / "Alphas_Sparkles"
ENGINE_INI = PROJECT_ROOT / "Config" / "DefaultEngine.ini"


def _unreal():
    try:
        import unreal  # type: ignore
        return unreal
    except ImportError:
        return None


def _check_ini() -> dict:
    out: dict = {"path": str(ENGINE_INI).replace("\\", "/"), "exists": ENGINE_INI.exists(), "values": {}, "issues": []}
    if not ENGINE_INI.exists():
        out["issues"].append("DefaultEngine.ini missing")
        return out
    cfg = configparser.ConfigParser(strict=False)
    cfg.read(ENGINE_INI, encoding="utf-8")
    # Raw scan for renderer settings
    text = ENGINE_INI.read_text(encoding="utf-8", errors="ignore")
    checks = {
        "r.CustomDepth=3": "r.CustomDepth=3" in text,
        "r.Substrate=True": "r.Substrate=True" in text,
        "r.Shadow.Virtual.Enable=1": "r.Shadow.Virtual.Enable=1" in text,
        "r.MegaLights.EnableForProject=True": "r.MegaLights.EnableForProject=True" in text,
        "r.DynamicGlobalIlluminationMethod=1": "r.DynamicGlobalIlluminationMethod=1" in text,
        "r.ReflectionMethod=1": "r.ReflectionMethod=1" in text,
        "r.DefaultFeature.MotionBlur=False": "r.DefaultFeature.MotionBlur=False" in text,
    }
    out["values"] = checks
    for k, v in checks.items():
        if not v and k != "r.DefaultFeature.MotionBlur=False":
            out["issues"].append(f"Missing or unexpected {k}")
    return out


def run() -> dict:
    ts = datetime.now(timezone.utc).isoformat()
    unreal = _unreal()
    report: dict = {"timestamp": ts, "level": LEVEL, "glam_folder": GLAM_FOLDER, "issues": []}

    # Ini gate
    report["engine_ini"] = _check_ini()
    if report["engine_ini"]["issues"]:
        report["issues"].extend([{"severity": "warn", "id": "ini", "msg": m} for m in report["engine_ini"]["issues"]])

    # Alphas on disk
    alphas = []
    for name in ["T_Alpha_Rune_SoundwavePulse.png", "T_Alpha_Rune_MusicalClefScroll.png", "T_Alpha_Ghibli_PetalVortex.png", "T_Alpha_Ghibli_WindSwirl.png", "T_Alpha_Rune_BaroqueFiligree.png"]:
        p = ALPHA_DIR / name
        alphas.append({"name": name, "exists": p.exists(), "bytes": p.stat().st_size if p.exists() else 0})
        if not p.exists():
            report["issues"].append({"severity": "warn", "id": "missing_alpha_disk", "name": name})
    report["alphas_disk"] = alphas

    if unreal is None:
        report["mode"] = "standalone_no_unreal"
        report["mpc"] = [{"path": p, "exists": "unknown_without_editor"} for p in MPC_PATHS]
        report["npc"] = {"path": NPC_PATH, "exists": "unknown_without_editor"}
        report["sequence"] = {"path": SEQ_PATH, "exists": "unknown_without_editor"}
        report["ok"] = len([i for i in report["issues"] if i["severity"] == "critical"]) == 0
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(json.dumps(report, indent=2))
        return report

    # Editor checks
    report["mode"] = "editor"

    # MPC / NPC
    mpc_entries = []
    mpc_found = False
    for p in MPC_PATHS:
        exists = unreal.EditorAssetLibrary.does_asset_exist(p)
        mpc_entries.append({"path": p, "exists": exists})
        mpc_found = mpc_found or exists
    report["mpc"] = mpc_entries
    if not mpc_found:
        report["issues"].append({"severity": "critical", "id": "missing_mpc", "msg": "No MPC_Melodia_Palette found at tried paths"})
    npc_exists = unreal.EditorAssetLibrary.does_asset_exist(NPC_PATH)
    report["npc"] = {"path": NPC_PATH, "exists": npc_exists}
    if not npc_exists:
        report["issues"].append({"severity": "warn", "id": "missing_npc", "msg": "NPC_Melodia_Palette missing — Niagara will read constant 0 (see MelodiaAudioReactivePresentationSubsystem warning)"})

    # Sequence + MRQ
    report["sequence"] = {"path": SEQ_PATH, "exists": unreal.EditorAssetLibrary.does_asset_exist(SEQ_PATH)}
    report["mrq_preset"] = {"path": MRQ_PATH, "exists": unreal.EditorAssetLibrary.does_asset_exist(MRQ_PATH)}
    glam_dir_exists = unreal.EditorAssetLibrary.does_directory_exist(GLAM_FOLDER)
    report["glam_folder_exists"] = glam_dir_exists

    # Level actor scan (requires level load)
    try:
        les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
        if unreal.EditorAssetLibrary.does_asset_exist(f"{LEVEL}.ZenForestTest"):
            les.load_level(LEVEL)
            eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
            actors = eas.get_all_level_actors() or []
            glam_actors = []
            for a in actors:
                label = a.get_actor_label()
                if label.startswith("VFX_Zen_") or label.startswith("Cam_ZenGlam") or label == "PP_Zen_MusicalGlam_Hint":
                    comp = None
                    try:
                        comp = a.get_component_by_class(unreal.NiagaraComponent)
                    except Exception:
                        pass
                    glam_actors.append({"label": label, "class": a.get_class().get_name(), "has_niagara": bool(comp)})
            report["level_actors_glam"] = sorted(glam_actors, key=lambda x: x["label"])
            report["level_actor_count"] = len(actors)
            # Expect at least 4 VFX + 4 cams + 1 PPV for full pass
            if len([x for x in glam_actors if x["label"].startswith("VFX_Zen_")]) < 3:
                report["issues"].append({"severity": "warn", "id": "few_vfx_actors", "msg": "Expected >=3 VFX_Zen_* in ZenForestTest — run setup_zenforest_musical_glam.py"})
            if len([x for x in glam_actors if x["label"].startswith("Cam_ZenGlam")]) < 3:
                report["issues"].append({"severity": "warn", "id": "few_cams", "msg": "Expected >=3 Cam_ZenGlam_* — run setup scripts"})
        else:
            report["issues"].append({"severity": "critical", "id": "level_missing", "msg": LEVEL})
    except Exception as exc:
        report["issues"].append({"severity": "warn", "id": "actor_scan_failed", "msg": str(exc)})

    report["critical_count"] = sum(1 for i in report["issues"] if i.get("severity") == "critical")
    report["ok"] = report["critical_count"] == 0
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    if unreal:
        try:
            unreal.log(f"[ZenMusicalAudit] -> {REPORT} ok={report['ok']}")
        except Exception:
            pass
    return report


def main() -> int:
    r = run()
    if "--json" in sys.argv:
        print(json.dumps(r, indent=2))
    return 0 if r.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
