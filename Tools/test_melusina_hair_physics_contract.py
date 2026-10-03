import json
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))
from melusina_hair_physics_contract import DEFAULT_CONTRACT, validate_probe  # noqa: E402


def contract():
    return json.loads(DEFAULT_CONTRACT.read_text(encoding="utf-8"))


def passing_probe():
    c = contract()
    s = c["settings"]
    return {"asset": c["asset"], "mesh": c["mesh"], "node_count": 1, "nodes": [{
        "name": c["node"], "root_bone": c["root_bone"], "gravity": s["gravity"],
        "enable_wind": s["enable_wind"], "wind_scale": s["wind_scale"],
        "dummy_bone_length": s["dummy_bone_length"], "bone_subdivision_count": s["bone_subdivision_count"],
        "need_warm_up": s["need_warm_up"], "warm_up_frames": s["warm_up_frames"],
        "physics_settings": {key: s[key] for key in ("damping", "stiffness", "world_damping_location", "world_damping_rotation", "limit_angle", "radius")},
    }]}


def test_live_profile_shape_passes():
    assert validate_probe(passing_probe(), contract())["ok"] is True


def test_stale_aggressive_tune_fails():
    probe = passing_probe()
    probe["nodes"][0]["physics_settings"].update(damping=0.42, stiffness=0.14)
    report = validate_probe(probe, contract())
    assert report["ok"] is False and len(report["errors"]) == 2


def test_missing_warmup_fails():
    probe = passing_probe()
    probe["nodes"][0]["need_warm_up"] = False
    assert validate_probe(probe, contract())["ok"] is False


def test_wrong_root_or_extra_node_fails():
    probe = passing_probe()
    probe["nodes"][0]["root_bone"] = "HairExp_Rig"
    probe["node_count"] = 2
    assert len(validate_probe(probe, contract())["errors"]) >= 2


def test_retired_export_root_cannot_return():
    probe = passing_probe()
    probe["nodes"][0]["root_bone"] = "HairExp_Rig"
    report = validate_probe(probe, contract())
    assert report["ok"] is False
    assert report["errors"] == ["KawaiiPhysics root must remain hair_root"]
