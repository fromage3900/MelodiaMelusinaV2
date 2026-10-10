"""Reference and torso-receipt regressions; acceptance still requires live PIE."""
import copy
import json
import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location("melusina_anim_gate", Path(__file__).with_name("melusina_anim_gate.py"))
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)

ROOT = "/Game/Test/BP_Player"
ABP = "/Game/Test/ABP_Current"
OLD = "/Game/Test/A_Retired"


def fixture():
    return {
        "registry_loading": False,
        "assets": {
            ROOT: {"class": "Blueprint", "hard_dependencies": [ABP]},
            ABP: {"class": "AnimBlueprint", "hard_dependencies": [], "soft_dependencies": []},
            OLD: {"class": "AnimSequence"},
        },
    }, {"roots": [ROOT], "canonical_allowlist": {ABP: "body owner"}, "retired_denylist": {OLD: "explicit retirement"}}


@pytest.mark.parametrize("kind", ["AnimBlueprint", "AnimSequence", "IKRigDefinition", "IKRetargeter", "AnimMontage", "Skeleton", "BlendSpace", "PoseAsset", "AnimComposite", "ControlRigBlueprint"])
@pytest.mark.parametrize("edge_kind", ["hard_dependencies", "soft_dependencies"])
def test_retired_asset_fails_with_reference_chain_for_every_asset_type(kind, edge_kind):
    manifest, policy = fixture()
    manifest["assets"][OLD]["class"] = kind
    manifest["assets"][ABP][edge_kind] = [OLD + ".A_Retired"]
    report = gate.check_runtime_references(manifest, policy)
    assert not report["ok"]
    assert report["violations"][0]["reference_chain"] == [ROOT, ABP, OLD]


def test_native_soft_default_is_checked_even_without_registry_referencer():
    manifest, policy = fixture()
    policy["required_native_consumers"] = {"WaveHarp": 1}
    edge = native_edge(source=ROOT, target=OLD, consumer="WaveHarp")
    report = gate.check_runtime_references(manifest, policy, [edge])
    assert not report["ok"]
    assert report["violations"][0]["reference_chain"] == [ROOT, OLD]


def native_edge(source=ROOT, target=OLD, consumer="WaveHarp", field="ChargeDrawAnim",
                required=True, expected_skeleton="/Game/Test/SK_Melusina",
                target_skeleton="/Game/Test/SK_Melusina"):
    return {
        "source": source,
        "target": target,
        "consumer": consumer,
        "field": field,
        "required": required,
        "expected_skeleton": expected_skeleton,
        "target_skeleton": target_skeleton,
    }


def test_exact_required_native_fields_reject_missing_and_duplicate_edges():
    manifest, policy = fixture()
    policy["required_native_fields"] = [{"consumer": "WaveHarp", "field": "ChargeDrawAnim",
                                         "expected_skeleton": "/Game/Test/SK_Melusina"}]
    missing = gate.check_runtime_references(manifest, policy)
    assert not missing["ok"]
    assert any("Required native field extraction missing: WaveHarp.ChargeDrawAnim" in e for e in missing["errors"])

    duplicate = gate.check_runtime_references(
        manifest, policy,
        [native_edge(), native_edge(target="/Game/Test/A_Other")])
    assert not duplicate["ok"]
    assert any("Duplicate native binding field edge: WaveHarp.ChargeDrawAnim" in e for e in duplicate["errors"])


def test_required_native_edge_must_be_well_formed_and_have_known_skeletons():
    manifest, policy = fixture()
    policy["required_native_fields"] = [{"consumer": "WaveHarp", "field": "ChargeDrawAnim",
                                         "expected_skeleton": "/Game/Test/SK_Melusina"}]
    malformed = native_edge()
    del malformed["field"]
    report = gate.check_runtime_references(manifest, policy, [malformed])
    assert not report["ok"]
    assert any("Malformed native binding edge" in e and "field" in e for e in report["errors"])

    unknown = native_edge(target_skeleton=None)
    report = gate.check_runtime_references(manifest, policy, [unknown])
    assert not report["ok"]
    assert any("Required native field has unknown skeleton: WaveHarp.ChargeDrawAnim" in e for e in report["errors"])


def test_battle_root_native_field_rejects_wrong_skeleton():
    manifest, policy = fixture()
    battle = "/Game/Experiments/MelodiaJRPG/BP_MelusinaSwordsman_Presentation"
    manifest["assets"][battle] = {"class": "Blueprint", "hard_dependencies": [], "soft_dependencies": []}
    policy["roots"].append(battle)
    policy["required_native_fields"] = [{"consumer": "WaveHarp", "field": "ChargeDrawAnim",
                                         "expected_skeleton": "/Game/Test/SK_Melusina"}]
    edge = native_edge(source=battle, target=OLD, target_skeleton="/Game/Test/SK_Other")
    report = gate.check_runtime_references(manifest, policy, [edge])
    assert not report["ok"]
    assert any("Native field skeleton mismatch for WaveHarp.ChargeDrawAnim" in e for e in report["errors"])


def test_optional_null_native_field_is_valid_only_when_explicit():
    manifest, policy = fixture()
    optional = native_edge(target=None, required=False, expected_skeleton=None, target_skeleton=None)
    assert gate.check_runtime_references(manifest, policy, [optional])["ok"]

    implicit = dict(optional)
    del implicit["required"]
    report = gate.check_runtime_references(manifest, policy, [implicit])
    assert not report["ok"]
    assert any("missing required" in e for e in report["errors"])


def test_missing_native_extraction_cannot_pass():
    manifest, policy = fixture()
    policy["required_native_consumers"] = {"WaveHarp": 5}
    report = gate.check_runtime_references(manifest, policy)
    assert not report["ok"]
    assert any("Native binding extraction" in e for e in report["errors"])


def test_archive_location_is_not_retirement_and_unknown_is_not_promotion():
    manifest, policy = fixture()
    retained = "/Game/Test/_Archive/RTG_Required"
    unknown = "/Game/Test/A_Unknown"
    manifest["assets"][ABP]["hard_dependencies"] = [retained, unknown]
    manifest["assets"][retained] = {"class": "IKRetargeter"}
    manifest["assets"][unknown] = {"class": "AnimSequence"}
    policy["canonical_allowlist"][retained] = "protected authoring pose"
    report = gate.check_runtime_references(manifest, policy)
    assert report["ok"]
    assert retained in report["allowlisted_reachable"]
    assert report["unclassified_animation_assets"] == [unknown]
    assert report["visual_completion"] is False


@pytest.mark.parametrize("change", ["missing_root", "registry_loading", "unverified_registry", "contradictory_policy"])
def test_incomplete_extraction_or_policy_cannot_pass(change):
    manifest, policy = fixture()
    if change == "missing_root":
        del manifest["assets"][ROOT]
    elif change == "registry_loading":
        manifest["registry_loading"] = True
    elif change == "unverified_registry":
        del manifest["registry_loading"]
    else:
        policy["canonical_allowlist"][OLD] = "conflicting admission"
    assert not gate.check_runtime_references(manifest, policy)["ok"]


def test_cycles_terminate_without_mutating_extraction():
    manifest, policy = fixture()
    manifest["assets"][ABP]["hard_dependencies"] = [ROOT]
    original = copy.deepcopy(manifest)
    assert gate.check_runtime_references(manifest, policy)["ok"]
    assert manifest == original


def test_unreal_tag_path_normalization():
    assert gate.package_path("/Script/Engine.Skeleton'/Game/Test/SK_Body.SK_Body'") == "/Game/Test/SK_Body"


def torso_receipt():
    phases = ("idle", "draw", "hold", "fire", "recovery",
              "caster_draw", "caster_fire", "caster_recovery")
    return {"errors": [], "proof": "Direct-owner simulated diagnostic",
            "samples": [{"phase": phase, "view": view,
                         "bones_cs": {"root_x": {"p": [0, 0, 72]},
                                      "spine_03_x": {"p": [0, 0, 110]},
                                      "head_x": {"p": [0, 0, 136]}}}
                        for phase in phases for view in ("front", "side")]}


def test_upright_runtime_diagnostic_does_not_claim_input_or_visual_acceptance():
    receipt = torso_receipt()
    original = copy.deepcopy(receipt)
    result = gate.check_runtime_torso_order(receipt)
    assert result["ok"]
    assert not result["physical_input_acceptance"]
    assert not result["visual_completion"]
    assert receipt == original


@pytest.mark.parametrize("phase", ["draw", "hold", "fire", "caster_fire"])
def test_layered_inversion_fails_even_when_other_view_is_upright(phase):
    receipt = torso_receipt()
    row = next(s for s in receipt["samples"] if s["phase"] == phase)
    row["bones_cs"]["spine_03_x"]["p"][2] = 47
    row["bones_cs"]["head_x"]["p"][2] = 21
    result = gate.check_runtime_torso_order(receipt)
    assert not result["ok"]
    assert any("Torso inversion" in e for e in result["errors"])


@pytest.mark.parametrize("fault", ["missing_bone", "nan", "missing_phase", "missing_view", "capture_error"])
def test_incomplete_runtime_torso_capture_fails_closed(fault):
    receipt = torso_receipt()
    if fault == "missing_bone":
        del receipt["samples"][0]["bones_cs"]["head_x"]
    elif fault == "nan":
        receipt["samples"][0]["bones_cs"]["head_x"]["p"][2] = float("nan")
    elif fault == "missing_phase":
        receipt["samples"] = [s for s in receipt["samples"] if s["phase"] != "hold"]
    elif fault == "missing_view":
        receipt["samples"] = [s for s in receipt["samples"] if s["view"] != "side"]
    else:
        receipt["errors"] = ["capture callback failed"]
    assert not gate.check_runtime_torso_order(receipt)["ok"]


def test_runtime_capture_cli_propagates_inversion_failure(tmp_path, capsys):
    receipt = torso_receipt()
    receipt["samples"][2]["bones_cs"]["head_x"]["p"][2] = 21
    source, output = tmp_path / "capture.json", tmp_path / "gate.json"
    source.write_text(json.dumps(receipt), encoding="utf-8")
    assert gate.reference_gate_main(["--runtime-capture", str(source), "--output", str(output)]) == 1
    assert not json.loads(output.read_text(encoding="utf-8"))["ok"]
    assert json.loads(capsys.readouterr().out)["physical_input_acceptance"] is False
