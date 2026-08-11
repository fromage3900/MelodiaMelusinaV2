"""Consolidated Melodia project health audit — runs inside Unreal Editor.

Usage (headless):
  UnrealEditor-Cmd.exe BS_GodFile.uproject ^
    -ExecutePythonScript="G:/.../Content/Python/run_melodia_health_audits.py"

Safe to run while editor is open (read-only).
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import unreal

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT_DIR = PROJECT_ROOT / "Saved" / "Audit"
REPORT_DIR.mkdir(parents=True, exist_ok=True)
REPORT = REPORT_DIR / "melodia_health.json"

results = {
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "checks": [],
}


def check(scope: str, ok: bool, detail: str):
    results["checks"].append({"scope": scope, "ok": ok, "detail": detail})
    if ok:
        unreal.log(f"[MelodiaHealth] PASS {scope}: {detail}")
    else:
        unreal.log_warning(f"[MelodiaHealth] FAIL {scope}: {detail}")


# --- 1. MPC param presence ---
mpc = unreal.EditorAssetLibrary.load_asset(
    "/Game/Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette")
cozy_params = {"WarmthGlow", "PetalFallIntensity", "DreamRipple", "EmberDance", "CozyBloom"}
if mpc:
    existing = {s.get_editor_property("parameter_info").name
                for s in mpc.get_editor_property("scalar_parameters")}
    missing = cozy_params - existing
    check("MPC.MelodiaPalette.CozyParams",
          len(missing) == 0,
          f"Missing params: {missing}" if missing else "All 5 cozy params present")
else:
    check("MPC.MelodiaPalette.Load", False, "Could not load MPC asset")


# --- 2. Quest manager header — RestoreQuestState exposed ---
quest_hpp = PROJECT_ROOT / "Plugins" / "MelodiaCore" / "Source" / "MelodiaCore" / "MelodiaQuestManagerBase.h"
if quest_hpp.exists():
    text = quest_hpp.read_text(encoding="utf-8")
    check("Source.QuestManager.RestoreQuestState",
          "RestoreQuestState" in text,
          "RestoreQuestState declaration found" if "RestoreQuestState" in text else "Missing RestoreQuestState")
    check("Source.QuestManager.GetActiveQuests",
          "TArray<FMelodiaQuestDef> GetActiveQuests" in text,
          "GetActiveQuests returns array (save-safe)" if "TArray<FMelodiaQuestDef> GetActiveQuests" in text else "Unexpected return type")
else:
    check("Source.QuestManager.File", False, f"Not found at {quest_hpp}")


# --- 3. NPC interaction — quest giver fields exposed ---
npc_hpp = PROJECT_ROOT / "Plugins" / "MelodiaCore" / "Source" / "MelodiaCore" / "MelodiaNPCInteractionComponent.h"
if npc_hpp.exists():
    text = npc_hpp.read_text(encoding="utf-8")
    check("Source.NPCInteraction.QuestFields",
          "bIsQuestGiver" in text and "QuestToGive" in text and "QuestToCompleteOnEnd" in text,
          "All 3 quest integration fields present" if all(f in text for f in ["bIsQuestGiver", "QuestToGive", "QuestToCompleteOnEnd"]) else "Missing quest integration fields")
else:
    check("Source.NPCInteraction.File", False, f"Not found at {npc_hpp}")


# --- 4. SaveGame — quest state arrays exposed ---
save_hpp = PROJECT_ROOT / "Plugins" / "MelodiaCore" / "Source" / "MelodiaCore" / "MelodiaSaveGame.h"
if save_hpp.exists():
    text = save_hpp.read_text(encoding="utf-8")
    check("Source.SaveGame.QuestState",
          "SavedActiveQuests" in text and "SavedCompletedQuestIds" in text,
          "Quest save arrays present" if all(f in text for f in ["SavedActiveQuests", "SavedCompletedQuestIds"]) else "Missing quest save arrays")
else:
    check("Source.SaveGame.File", False, f"Not found at {save_hpp}")


# --- 5. Source files compile-relevant — all headers include-guarded ---
core_dir = PROJECT_ROOT / "Plugins" / "MelodiaCore" / "Source" / "MelodiaCore"
if core_dir.exists():
    hpp_files = list(core_dir.glob("*.h"))
    missing_pragma = [f.name for f in hpp_files if "#pragma once" not in f.read_text(encoding="utf-8")]
    check("Source.PragmaOnce",
          len(missing_pragma) == 0,
          f"Missing #pragma once: {missing_pragma}" if missing_pragma else "All headers have #pragma once")


# --- 6. Build.cs module deps ---
build_cs = core_dir / "MelodiaCore.Build.cs"
if build_cs.exists():
    text = build_cs.read_text(encoding="utf-8")
    for dep in ["UMG", "Slate", "AudioMixer", "AIModule"]:
        check(f"Build.Dep.{dep}", dep in text, f"{dep} dependency present")
else:
    check("Build.BuildDotCS", False, f"Not found at {build_cs}")


# --- 7. Test files exist ---
test_files = [
    "MelodiaQuestManagerTests.cpp",
    "MelodiaProgressionTests.cpp",
    "MelodiaReactivitySignalTests.cpp",
    "MelodiaNPCApplicationTests.cpp",
    "MelodiaNPCTests.cpp",
    "MelodiaPersistenceTests.cpp",
]
for tf in test_files:
    exists = (core_dir / tf).exists()
    check(f"Tests.{tf.replace('.cpp', '')}", exists, f"Found" if exists else f"Missing: {tf}")


# --- 8. MPC duplicate check ---
mpc_v2 = unreal.EditorAssetLibrary.load_asset(
    "/Game/_PROJECT/04_Materials/MPC_Melodia_Palette")
check("MPC.DuplicateCheck",
      mpc_v2 is not None,
      f"Second copy at /Game/_PROJECT/... exists={mpc_v2 is not None}")


# --- Write report ---
REPORT.write_text(json.dumps(results, indent=2), encoding="utf-8")
unreal.log(f"[MelodiaHealth] Report written to {REPORT}")
unreal.log(f"[MelodiaHealth] {sum(1 for c in results['checks'] if c['ok'])}/{len(results['checks'])} checks passed")
