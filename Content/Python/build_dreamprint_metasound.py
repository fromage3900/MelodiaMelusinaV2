"""Dreamprint — build MSS_MelodiaMusicPulse (FINAL: all binding facts resolved).

Probe-resolved binding facts (2026-08-16):
  accessor: unreal.get_engine_subsystem(unreal.MetaSoundBuilderSubsystem)
  create_source_builder(name, MetaSoundOutputAudioFormat.MONO, False) -> 5-tuple
  node classes: MetasoundFrontendClassName("UE","Wave Player","Mono"),
                ("UE","Envelope Follower","")
  pins: wave "Wave Asset"/"Loop" in, "Out Mono" out; env "In" in, "Envelope" out
  connect_nodes(output_handle, input_handle)
  connect_node_output_to_graph_output(GRAPH_OUTPUT_NAME, node_output_handle)  # name FIRST
  add_graph_output_node(name, "Float", literal)
  literals via MetasoundFrontendLiteralBlueprintAccess static factories
  (create_bool/float/object_meta_sound_literal) — Type property is protected
  and cannot be set directly.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal

ASSET_FOLDER = "/Game/Melodia/_PROJECT/04_Audio/Music"
ASSET_NAME = "MSS_MelodiaMusicPulse"
ASSET_PATH = f"{ASSET_FOLDER}/{ASSET_NAME}"
BGM_WAVE = "/Game/Melodia/Audio/BGM/SW_BGM_Zundamon_Sewaa_Full"
REPORT = Path(__file__).resolve().parents[2] / "Saved" / "Audit" / "dreamprint_metasound_build.json"


def _write_report(res: dict) -> None:
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(res, indent=2), encoding="utf-8")
    print(json.dumps(res, indent=2))


def main() -> int:
    if not unreal.EditorAssetLibrary.does_directory_exist(ASSET_FOLDER):
        unreal.EditorAssetLibrary.make_directory(ASSET_FOLDER)
    wave = unreal.load_asset(BGM_WAVE)
    if not wave:
        _write_report({"timestamp": datetime.now(timezone.utc).isoformat(), "asset": ASSET_PATH,
                       "status": "HOLD", "reason": f"BGM wave missing: {BGM_WAVE}", "ok": False})
        return 1

    steps = {}

    b = unreal.get_engine_subsystem(unreal.MetaSoundBuilderSubsystem)
    t = b.create_source_builder(ASSET_NAME, unreal.MetaSoundOutputAudioFormat.MONO, False)
    sb = t[0]
    steps["create"] = str(t[4])

    wave_h, r1 = sb.add_node_by_class_name(unreal.MetasoundFrontendClassName("UE", "Wave Player", "Mono"))
    env_h, r2 = sb.add_node_by_class_name(unreal.MetasoundFrontendClassName("UE", "Envelope Follower", ""))
    steps["add_nodes"] = [str(r1), str(r2)]

    wave_asset_in, _ = sb.find_node_input_by_name(wave_h, "Wave Asset")
    loop_in, _ = sb.find_node_input_by_name(wave_h, "Loop")
    wave_out, _ = sb.find_node_output_by_name(wave_h, "Out Mono")
    env_in, _ = sb.find_node_input_by_name(env_h, "In")
    env_out, _ = sb.find_node_output_by_name(env_h, "Envelope")

    access = unreal.MetasoundFrontendLiteralBlueprintAccess
    lit_wave = access.create_object_meta_sound_literal(wave)
    lit_loop = access.create_bool_meta_sound_literal(True)
    lit_float = access.create_float_meta_sound_literal(0.0)

    steps["set_wave_asset"] = str(sb.set_node_input_default(wave_asset_in, lit_wave))
    steps["set_loop"] = str(sb.set_node_input_default(loop_in, lit_loop))
    steps["connect_wave_env"] = str(sb.connect_nodes(wave_out, env_in))
    steps["connect_src"] = str(sb.connect_node_output_to_graph_output("UE.OutputFormat.Mono.Audio:0", wave_out))
    steps["add_env_out"] = str(sb.add_graph_output_node("Envelope", "Float", lit_float))
    steps["connect_env_out"] = str(sb.connect_node_output_to_graph_output("Envelope", env_out))

    asset = None
    if unreal.EditorAssetLibrary.does_asset_exist(ASSET_PATH):
        asset = unreal.load_asset(ASSET_PATH)
    else:
        factory = unreal.MetaSoundSourceFactory()
        asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
        asset = asset_tools.create_asset(ASSET_NAME, ASSET_FOLDER, unreal.MetaSoundSource, factory)
    steps["asset_created"] = str(asset is not None)
    if asset:
        steps["build"] = str(sb.build_and_overwrite_meta_sound(asset))
        unreal.EditorAssetLibrary.save_loaded_asset(asset, only_if_is_dirty=False)

    failed = [k for k, v in steps.items() if "FAILED" in str(v) or str(v).startswith("ERR")]
    if failed or not steps.get("asset_created") == "True":
        _write_report({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "asset": ASSET_PATH, "status": "HOLD",
            "reason": "failed steps: " + ", ".join(failed) if failed else "asset not created",
            "steps": steps, "ok": False,
        })
        return 1

    _write_report({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "asset": ASSET_PATH, "wave": BGM_WAVE,
        "waveplayer_class": "UE/Wave Player/Mono",
        "envelope_class": "UE/Envelope Follower/",
        "status": "built", "steps": steps, "ok": True,
    })
    return 0


if __name__ == "__main__":
    raise SystemExit(main())