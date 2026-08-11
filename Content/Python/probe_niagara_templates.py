"""Probe engine Niagara template paths (one-shot diagnostic)."""
from __future__ import annotations

import json
from pathlib import Path

import unreal

CANDIDATES = [
    "/Niagara/DefaultAssets/Templates/Systems/Fountain",
    "/Niagara/DefaultAssets/Templates/Systems/Fountain.Fountain",
    "/Niagara/DefaultAssets/Templates/Emitters/Fountain",
    "/Niagara/DefaultAssets/Templates/Emitters/Fountain.Fountain",
    "/Niagara/DefaultAssets/Templates/Systems/HangingParticulates",
    "/Niagara/DefaultAssets/Templates/Systems/HangingParticulates.HangingParticulates",
    "/Niagara/DefaultAssets/Templates/Emitters/HangingParticulates",
    "/Niagara/DefaultAssets/Templates/Emitters/HangingParticulates.HangingParticulates",
    "/Niagara/DefaultAssets/Templates/Systems/OmnidirectionalBurst",
    "/Niagara/DefaultAssets/Templates/Systems/OmnidirectionalBurst.OmnidirectionalBurst",
    "/Niagara/DefaultAssets/Templates/Emitters/OmnidirectionalBurst",
    "/Niagara/DefaultAssets/Templates/Emitters/OmnidirectionalBurst.OmnidirectionalBurst",
    "/Niagara/DefaultAssets/Templates/Systems/FloatingDust",
    "/Niagara/DefaultAssets/Templates/Systems/SimpleSpriteBurst",
    "/Niagara/DefaultAssets/Templates/Systems/EmitterTemplate",
    "/Niagara/DefaultAssets/Systems/EmitterTemplate",
    "/Niagara/DefaultAssets/Systems/Fountain",
]

out = []
for path in CANDIDATES:
    exists = unreal.EditorAssetLibrary.does_asset_exist(path)
    cls = ""
    if exists:
        asset = unreal.load_asset(path)
        cls = type(asset).__name__ if asset else "load_failed"
    out.append({"path": path, "exists": exists, "class": cls})

report = Path(__file__).resolve().parents[2] / "Saved" / "Audit" / "niagara_template_probe.json"
report.parent.mkdir(parents=True, exist_ok=True)
report.write_text(json.dumps(out, indent=2), encoding="utf-8")
print(json.dumps(out, indent=2))
