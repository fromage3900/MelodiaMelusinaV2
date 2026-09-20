"""Stub BP_MelusinaRoomShell + PCG_MelusinaRoomShell_PCGex by duplicating nearest templates."""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
import unreal

EAL = unreal.EditorAssetLibrary
ATL = unreal.AssetToolsHelpers.get_asset_tools()

PCG_DST = "/Game/EnvSandbox/PCG/House/PCG_MelusinaRoomShell_PCGex"
BP_DST = "/Game/EnvSandbox/Blueprints/House/BP_MelusinaRoomShell"
PCG_SRC_CANDIDATES = [
    "/Game/EnvSandbox/PCG/_Dev/_probe_pcgex",
    "/Game/EnvSandbox/PCG/House/PCG_MelusinaHouse_MorningDell",
    "/Game/EnvSandbox/PCG/Styles/Sakura/PCG_Nikki_PhyllotaxisGarden_Walkable",
]
BP_SRC_CANDIDATES = [
    # Prefer a simple Actor BP if we find one; else create from scratch
]

def ensure_dir(path):
    # path like /Game/EnvSandbox/PCG/House
    if not EAL.does_directory_exist(path):
        EAL.make_directory(path)

notes = []
created = {}

# --- PCG graph stub ---
ensure_dir("/Game/EnvSandbox/PCG/House")
if EAL.does_asset_exist(PCG_DST):
    notes.append("pcg_already_exists")
    created["pcg"] = {"path": PCG_DST, "action": "exists"}
else:
    src = next((p for p in PCG_SRC_CANDIDATES if EAL.does_asset_exist(p)), None)
    if not src:
        notes.append("no_pcg_src")
        created["pcg"] = {"path": PCG_DST, "action": "failed_no_src"}
    else:
        ok = EAL.duplicate_asset(src, PCG_DST)
        notes.append(f"duplicated_pcg_from={src} ok={ok}")
        created["pcg"] = {"path": PCG_DST, "action": "duplicated", "from": src, "ok": bool(ok)}

# --- Blueprint stub ---
ensure_dir("/Game/EnvSandbox/Blueprints/House")
if EAL.does_asset_exist(BP_DST):
    notes.append("bp_already_exists")
    created["bp"] = {"path": BP_DST, "action": "exists"}
else:
    try:
        factory = unreal.BlueprintFactory()
        factory.set_editor_property("ParentClass", unreal.Actor)
        bp = ATL.create_asset(
            asset_name="BP_MelusinaRoomShell",
            package_path="/Game/EnvSandbox/Blueprints/House",
            asset_class=unreal.Blueprint,
            factory=factory,
        )
        notes.append(f"bp_create={bp}")
        created["bp"] = {"path": BP_DST, "action": "created", "obj": str(bp)}
        if bp:
            EAL.save_asset(BP_DST)
    except Exception as e:
        notes.append(f"bp_create_err={e}")
        created["bp"] = {"path": BP_DST, "action": "failed", "error": str(e)}

# Try add PCG component via loaded generated class if possible
try:
    if EAL.does_asset_exist(BP_DST) and EAL.does_asset_exist(PCG_DST):
        # Load BP for editing is limited in Python; document manual assign if needed
        notes.append("assign_pcg_component_manual_or_followup")
except Exception as e:
    notes.append(f"wire_err={e}")

# Verify
verify = {
    "PCG": EAL.does_asset_exist(PCG_DST),
    "BP": EAL.does_asset_exist(BP_DST),
}

report = {
    "schema": "melodia.pcgex_roomshell_stubs.v1",
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "created": created,
    "verify": verify,
    "notes": notes,
    "recipe": "Saved/Audit/PCGex_MelusinaRoomShell_RECIPE.md",
    "next": "MA pcgex_scaffold exec when ready; Z lock SM_room_2; graph still needs PCGex node authoring inside duplicated stub",
}
out = Path(unreal.Paths.project_dir()) / "Saved" / "Audit" / "pcgex_roomshell_stubs_2026-09-20.json"
out.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
print("STUBS " + json.dumps({"verify": verify, "created": created, "notes": notes}, default=str))
