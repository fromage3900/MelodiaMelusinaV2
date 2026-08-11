"""Niagara finalization orchestrator — uses Monolith MCP to inspect, build,
assign materials, wire MPC bindings, and save showcase levels.

Usage (MCP must be live at http://127.0.0.1:9316/mcp):
  py Content/Python/finalize_niagara_mcp.py --inspect
  py Content/Python/finalize_niagara_mcp.py --build-mis
  py Content/Python/finalize_niagara_mcp.py --assign-materials
  py Content/Python/finalize_niagara_mcp.py --wire-mpc
  py Content/Python/finalize_niagara_mcp.py --showcase
  py Content/Python/finalize_niagara_mcp.py --audit
  py Content/Python/finalize_niagara_mcp.py --all          # run everything
"""
from __future__ import annotations

import json
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT_DIR = PROJECT_ROOT / "Saved" / "Audit"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

MCP_URL = "http://127.0.0.1:9316/mcp"

SAKURA_SYSTEMS = [
    "NS_SakuraPetals",
    "NS_SakuraPetals_v2",
    "NS_SakuraGroundPetals",
    "NS_SakuraPetalGust",
    "NS_SakuraDreamSparkle",
    "NS_SakuraLanternMotes",
    "NS_SakuraPondShimmer",
    "NS_SakuraWaterPetals",
    "NS_WindRibbonGust",
    "NS_ConstellationDraw",
]
VFX_BASE = "/Game/EnvSandbox/VFX"
SYSTEMS_SAKURA = f"{VFX_BASE}/Systems/Sakura"
VFX_MAT_DIR = f"{VFX_BASE}/Materials"
MPC_DIR = f"{VFX_BASE}/MPC"
MPC_SAKURA = f"{MPC_DIR}/MPC_SakuraDream"
MASTER_SPRITE = f"{VFX_MAT_DIR}/M_Niagara_SakuraSprite"

SPRITE_MI_SPECS = [
    ("MI_Niagara_Petal", MASTER_SPRITE, "petal_scatter"),
    ("MI_Niagara_Sparkle", MASTER_SPRITE, "dream_tint"),
    ("MI_Niagara_Mote", MASTER_SPRITE, "lantern_warm"),
    ("MI_Niagara_Pond", MASTER_SPRITE, "water_iridescence"),
    ("MI_Niagara_Gust", MASTER_SPRITE, "petal_pink"),
]

SYSTEM_MATERIAL_MAP = {
    "NS_SakuraPetals": (["Fountain"], "MI_Niagara_Petal"),
    "NS_SakuraPetals_v2": (["Fountain"], "MI_Niagara_Petal"),
    "NS_SakuraGroundPetals": (["FloatingDust"], "MI_Niagara_Petal"),
    "NS_SakuraPetalGust": (["OmnidirectionalBurst"], "MI_Niagara_Gust"),
    "NS_SakuraDreamSparkle": (["HangingParticulates"], "MI_Niagara_Sparkle"),
    "NS_SakuraLanternMotes": (["FloatingDust"], "MI_Niagara_Mote"),
    "NS_SakuraPondShimmer": (["HangingParticulates"], "MI_Niagara_Pond"),
    "NS_SakuraWaterPetals": (["Fountain"], "MI_Niagara_Petal"),
}

COLORS = {
    "petal_pink": (1.0, 0.74, 0.84, 1.0),
    "petal_scatter": (1.0, 0.78, 0.86, 1.0),
    "dream_tint": (1.0, 0.80, 0.90, 1.0),
    "lantern_warm": (1.0, 0.78, 0.45, 1.0),
    "water_iridescence": (0.80, 0.70, 0.95, 1.0),
}


def _mcp_call(method: str, params: dict | None = None, timeout: int = 30) -> dict:
    payload = {
        "jsonrpc": "2.0",
        "id": int(time.time() * 1000) % 100000,
        "method": method,
        "params": params or {},
    }
    req = urllib.request.Request(
        MCP_URL,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except Exception as exc:
        return {"error": str(exc)}


def _niagara(action: str, params: dict, timeout: int = 30) -> dict:
    """Call a Monolith Niagara MCP action via tools/call."""
    return _mcp_call("tools/call", {
        "name": "niagara_query",
        "arguments": {"action": action, "params": params},
    }, timeout=timeout)


def _tools_list() -> list[str]:
    result = _mcp_call("tools/list")
    tools = result.get("result", {}).get("tools", [])
    return [t["name"] for t in tools]


def _niagara_asset_path(name: str) -> str:
    return f"{SYSTEMS_SAKURA}/{name}"


# ── Step 1: Inspect ──────────────────────────────────────────────────────────

def step_inspect() -> dict:
    report = {
        "step": "inspect",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "systems": {},
        "mpc": {},
        "materials": {},
        "errors": [],
    }

    for sys_name in SAKURA_SYSTEMS:
        path = _niagara_asset_path(sys_name)
        entry = {"path": path, "exists": False, "emitters": [], "renderers": []}

        # Check asset existence
        check = _niagara("list_emitters", {"asset_path": path})
        if "error" in check:
            report["errors"].append(f"{sys_name}: {check['error']}")
            report["systems"][sys_name] = entry
            continue

        entry["exists"] = True
        emitters = check.get("result", [])
        entry["emitters"] = [e.get("name", str(e)) for e in (emitters if isinstance(emitters, list) else [])]

        for emitter in entry["emitters"]:
            rends = _niagara("list_renderers", {"asset_path": path, "emitter": emitter})
            rend_data = rends.get("result", [])
            if isinstance(rend_data, list):
                for r in rend_data:
                    entry["renderers"].append({
                        "emitter": emitter,
                        "type": r.get("type", str(r)),
                        "material": r.get("material", None),
                    })

        report["systems"][sys_name] = entry

    # Check MPC
    mpc_check = _niagara("get_npc", {"asset_path": MPC_SAKURA})
    if "error" not in mpc_check:
        report["mpc"] = mpc_check.get("result", {})
    else:
        report["errors"].append(f"MPC {MPC_SAKURA}: {mpc_check['error']}")

    # Check master sprite material
    mat_check = _mcp_call("tools/call", {
        "name": "material_query",
        "arguments": {"action": "get_material", "params": {"asset_path": MASTER_SPRITE}},
    })
    if "error" not in mat_check:
        report["materials"]["master_sprite"] = mat_check.get("result", {})
    else:
        report["errors"].append(f"Material {MASTER_SPRITE}: {mat_check['error']}")

    # Check each sprite MI
    for mi_name, parent, _ in SPRITE_MI_SPECS:
        mi_path = f"{VFX_MAT_DIR}/{mi_name}"
        mi_check = _mcp_call("tools/call", {
            "name": "material_query",
            "arguments": {"action": "get_material", "params": {"asset_path": mi_path}},
        })
        report["materials"][mi_name] = {
            "path": mi_path,
            "exists": "error" not in mi_check,
        }

    return report


# ── Step 2: Build Sprite MIs ────────────────────────────────────────────────

def step_build_mis() -> dict:
    """Build sprite material instances in-editor using the UE Python API."""
    report = {
        "step": "build_mis",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "instances": [],
        "errors": [],
    }

    try:
        import unreal
    except ImportError:
        report["errors"].append("Cannot import unreal — must run in UE editor")
        return report

    for mi_name, parent_path, color_key in SPRITE_MI_SPECS:
        mi_path = f"{VFX_MAT_DIR}/{mi_name}"
        full_path = f"{mi_path}.{mi_name}"

        if unreal.EditorAssetLibrary.does_asset_exist(full_path):
            report["instances"].append({"name": mi_name, "path": mi_path, "status": "exists"})
            continue

        parent = unreal.load_asset(parent_path)
        if not parent:
            report["errors"].append(f"Parent material {parent_path} not found")
            continue

        # Create MI
        mi = unreal.MaterialEditingLibrary.create_material_instance(parent)
        if not mi:
            report["errors"].append(f"Failed to create {mi_name}")
            continue

        # Set base color
        color = COLORS.get(color_key, (1, 1, 1, 1))
        unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(
            mi, "BaseColor", unreal.LinearColor(*color)
        )

        # Set emissive
        emissive_val = 1.2 if "Petal" in mi_name else (0.8 if "Sparkle" in mi_name else 0.4)
        unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(
            mi, "Emissive", emissive_val
        )

        # Set opacity
        opacity = 0.85 if "Petal" in mi_name else 0.6
        unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(
            mi, "Opacity", opacity
        )

        # Save
        package_path = f"/Game/EnvSandbox/VFX/Materials/{mi_name}"
        unreal.EditorAssetLibrary.save_asset(package_path, only_if_is_dirty=False)
        report["instances"].append({"name": mi_name, "path": mi_path, "status": "created"})

    return report


# ── Step 3: Assign Materials to Renderers via MCP ────────────────────────────

def step_assign_materials() -> dict:
    report = {
        "step": "assign_materials",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "assignments": [],
        "errors": [],
    }

    for sys_name, (emitters, mi_name) in SYSTEM_MATERIAL_MAP.items():
        path = _niagara_asset_path(sys_name)
        mi_path = f"{VFX_MAT_DIR}/{mi_name}"

        for emitter_name in emitters:
            # Verify emitter exists
            emitters_check = _niagara("list_emitters", {"asset_path": path})
            if "error" in emitters_check:
                report["errors"].append(f"{sys_name}: cannot list emitters — {emitters_check['error']}")
                continue

            # Get the actual emitter handle from what exists
            existing = emitters_check.get("result", [])
            if isinstance(existing, list):
                emitter_handle = None
                for e in existing:
                    ename = e.get("name", "") if isinstance(e, dict) else str(e)
                    if emitter_name.lower() in ename.lower():
                        emitter_handle = ename
                        break
                if not emitter_handle:
                    emitter_handle = emitter_name

            # List renderers
            rends = _niagara("list_renderers", {"asset_path": path, "emitter": emitter_handle})
            if "error" in rends:
                report["errors"].append(f"{sys_name}/{emitter_handle}: {rends['error']}")
                continue

            rend_data = rends.get("result", [])
            if not isinstance(rend_data, list):
                report["errors"].append(f"{sys_name}/{emitter_handle}: unexpected renderer data")
                continue

            for rend in rend_data:
                rend_type = rend.get("type", "")
                rend_idx = rend.get("index", 0)
                rend_name = rend.get("name", rend_type)

                result = _niagara("set_renderer_material", {
                    "asset_path": path,
                    "emitter": emitter_handle,
                    "renderer": str(rend_idx) if isinstance(rend_idx, int) else rend_name,
                    "material": mi_path,
                })
                entry = {
                    "system": sys_name,
                    "emitter": emitter_handle,
                    "renderer": rend_name,
                    "material": mi_path,
                    "ok": "error" not in result,
                }
                if "error" in result:
                    entry["error"] = result["error"]
                report["assignments"].append(entry)

    return report


# ── Step 4: Wire MPC Bindings ────────────────────────────────────────────────

def step_wire_mpc() -> dict:
    """Wire MPC_SakuraDream parameters into the master sprite material.

    Uses material_query to set MPC bindings for SparklePulse and PetalDensity.
    Falls back to direct material parameter collection assignment.
    """
    report = {
        "step": "wire_mpc",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "bindings": [],
        "errors": [],
    }

    # Check what the material already has bound
    mat_info = _mcp_call("tools/call", {
        "name": "material_query",
        "arguments": {"action": "get_material", "params": {"asset_path": MASTER_SPRITE}},
    })

    mpc_params = ["SparklePulse", "PetalDensity", "WindStrength"]
    for param in mpc_params:
        result = _mcp_call("tools/call", {
            "name": "material_query",
            "arguments": {
                "action": "set_mpc_binding",
                "params": {
                    "asset_path": MASTER_SPRITE,
                    "mpc_path": MPC_SAKURA,
                    "parameter_name": param,
                },
            },
        })
        entry = {"parameter": param, "ok": "error" not in result}
        if "error" in result:
            entry["error"] = result["error"]
        report["bindings"].append(entry)

    # Verify by reading back
    for param in mpc_params:
        check = _mcp_call("tools/call", {
            "name": "material_query",
            "arguments": {
                "action": "get_parameter_value",
                "params": {"asset_path": MASTER_SPRITE, "parameter": param},
            },
        })
        report["bindings"].append({"parameter": param, "check": check})

    return report


# ── Step 5: Save Showcase Levels ─────────────────────────────────────────────

def step_showcase() -> dict:
    report = {
        "step": "showcase",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "actions": [],
    }

    try:
        import unreal

        # Check if showcase level already exists
        showcase_path = "/Game/EnvSandbox/VFX/_Showcase/L_VFX_Showcase"
        if unreal.EditorAssetLibrary.does_asset_exist(f"{showcase_path}.L_VFX_Showcase"):
            report["actions"].append({"level": showcase_path, "status": "exists"})
        else:
            # Spawn via library
            from setup_niagara_library import spawn_showcase_level
            result = spawn_showcase_level()
            report["actions"].append({"level": showcase_path, "status": "created", "result": result})

        # Sakura showcase
        sakura_showcase = "/Game/EnvSandbox/VFX/_Showcase/L_VFX_SakuraShowcase"
        if unreal.EditorAssetLibrary.does_asset_exist(f"{sakura_showcase}.L_VFX_SakuraShowcase"):
            report["actions"].append({"level": sakura_showcase, "status": "exists"})
        else:
            from setup_sakura_niagara import build_sakura_showcase_level
            result = build_sakura_showcase_level()
            report["actions"].append({"level": sakura_showcase, "status": "created", "result": result})

    except ImportError as exc:
        report["errors"].append(f"Cannot import unreal: {exc}")
    except Exception as exc:
        report["errors"].append(f"Showcase error: {exc}")

    return report


# ── Step 6: Audit ────────────────────────────────────────────────────────────

def step_audit() -> dict:
    report = {
        "step": "audit",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "results": {},
    }

    try:
        import unreal

        # Run sakura niagara validation
        try:
            from validate_sakura_niagara import validate
            v_result = validate()
            report["results"]["validation"] = v_result
        except Exception as exc:
            report["results"]["validation"] = {"error": str(exc)}

        # Run petal audit
        try:
            from audit_sakura_petal_niagara import main as petal_audit
            a_result = petal_audit()
            report["results"]["petal_audit"] = a_result
        except Exception as exc:
            report["results"]["petal_audit"] = {"error": str(exc)}

        # Run universal manifest
        try:
            from universal_niagara_manifest import main as uni_manifest
            m_result = uni_manifest()
            report["results"]["universal_manifest"] = m_result
        except Exception as exc:
            report["results"]["universal_manifest"] = {"error": str(exc)}

    except ImportError as exc:
        report["errors"].append(f"Cannot import unreal: {exc}")

    return report


# ── Report ───────────────────────────────────────────────────────────────────

def write_report(report: dict) -> None:
    path = REPORT_DIR / f"niagara_finalization_{report['step']}.json"
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[VFX] report -> {path}")


# ── Main ─────────────────────────────────────────────────────────────────────

def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Niagara MCP Finalization Orchestrator")
    parser.add_argument("--inspect", action="store_true", help="Inspect current state")
    parser.add_argument("--build-mis", action="store_true", help="Build sprite MIs")
    parser.add_argument("--assign-materials", action="store_true", help="Assign materials via MCP")
    parser.add_argument("--wire-mpc", action="store_true", help="Wire MPC bindings")
    parser.add_argument("--showcase", action="store_true", help="Save showcase levels")
    parser.add_argument("--audit", action="store_true", help="Run validation + audit")
    parser.add_argument("--all", action="store_true", help="Run all steps")
    args = parser.parse_args()

    # Default: run all if nothing specified
    if not any(vars(args).values()):
        args.all = True

    if args.all or args.inspect:
        print("=== Step 1: Inspect ===")
        report = step_inspect()
        write_report(report)
        systems_ok = sum(1 for s in report["systems"].values() if s["exists"])
        print(f"  Systems: {systems_ok}/{len(SAKURA_SYSTEMS)} exist")
        print(f"  Errors: {len(report['errors'])}")

    if args.all or args.build_mis:
        print("\n=== Step 2: Build Sprite MIs ===")
        report = step_build_mis()
        write_report(report)
        created = sum(1 for i in report["instances"] if i["status"] == "created")
        existed = sum(1 for i in report["instances"] if i["status"] == "exists")
        print(f"  Created: {created}, Already existed: {existed}")

    if args.all or args.assign_materials:
        print("\n=== Step 3: Assign Materials ===")
        report = step_assign_materials()
        write_report(report)
        ok = sum(1 for a in report["assignments"] if a["ok"])
        print(f"  Assignments: {ok}/{len(report['assignments'])} OK")

    if args.all or args.wire_mpc:
        print("\n=== Step 4: Wire MPC ===")
        report = step_wire_mpc()
        write_report(report)
        ok = sum(1 for b in report["bindings"] if b.get("ok"))
        print(f"  Bindings: {ok} wired")

    if args.all or args.showcase:
        print("\n=== Step 5: Showcase Levels ===")
        report = step_showcase()
        write_report(report)
        for a in report.get("actions", []):
            print(f"  {a['level']}: {a['status']}")

    if args.all or args.audit:
        print("\n=== Step 6: Audit ===")
        report = step_audit()
        write_report(report)
        for k, v in report["results"].items():
            status = "OK" if "error" not in v else f"ERROR: {v['error']}"
            print(f"  {k}: {status}")

    print("\nDone.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
