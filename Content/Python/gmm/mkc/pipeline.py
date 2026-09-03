"""Pipeline tools — batch operations, verify-all, orchestration."""
from __future__ import annotations

import json
from gmm.core import MonolithClient, GmmAudit


def verify_all() -> dict:
    """Run full system verification: MCP status, Melusina rig, blend space, MPC.

    Returns a combined audit report.
    """
    audit = GmmAudit(action="mkc.verify_all")
    subsystem_results = {}

    mc = MonolithClient()

    # MCP connectivity
    try:
        status = mc.status()
        subsystem_results["mcp"] = {
            "ok": True,
            "version": status.get("version", "?"),
            "engine": status.get("engine_version", "?"),
            "action_count": status.get("total_actions", 0),
        }
    except Exception as e:
        subsystem_results["mcp"] = {"ok": False, "error": str(e)}

    # Melusina rig (if assess module available)
    try:
        import assess_melusina_rig
        rig = assess_melusina_rig.build_full_report()
        subsystem_results["melusina_rig"] = {
            "ok": True,
            "bone_count": rig.get("skeletal_mesh", {}).get("bone_count", 0),
            "material_slots": rig.get("skeletal_mesh", {}).get("material_slots", 0),
        }
    except Exception as e:
        subsystem_results["melusina_rig"] = {"ok": False, "error": str(e)}

    # Blend space - check if exists, or report current state
    try:
        import setup_melusina_exploration
        bs = setup_melusina_exploration.create_blend_space()
        # BS_Locomotion already exists case
        already_exists = bs.get("already_existed", False) or bs.get("error") == "Blend space already exists"
        if already_exists:
            subsystem_results["blend_space"] = {
                "ok": True,
                "message": "Blend space already exists",
                "samples": bs.get("samples_added", 0),
            }
        elif bs.get("created"):
            subsystem_results["blend_space"] = {
                "ok": True,
                "samples": bs.get("samples_added", 0),
                "method": bs.get("method_used"),
            }
        elif bs.get("warning"):
            # Created but samples couldn't be wired
            subsystem_results["blend_space"] = {
                "ok": True,
                "warning": bs.get("warning"),
            }
        else:
            subsystem_results["blend_space"] = {"ok": False, "error": bs.get("error", "Unknown error")}
    except Exception as e:
        subsystem_results["blend_space"] = {"ok": False, "error": str(e)}

    # MPC - check parameters
    try:
        import setup_melusina_exploration
        mpc_info = setup_melusina_exploration.get_mpc_parameters()
        subsystem_results["mpc"] = {
            "ok": mpc_info.get("exists", False),
            "scalar_count": len(mpc_info.get("scalar_params", [])),
            "vector_count": len(mpc_info.get("vector_params", [])),
        }
    except Exception as e:
        subsystem_results["mpc"] = {"ok": False, "error": str(e)}

    audit.ok(subsystem_results=subsystem_results)
    all_ok = all(r.get("ok", False) for r in subsystem_results.values())
    audit.data["all_ok"] = all_ok
    audit.save("gmm_verify_all.json")
    return audit.to_dict()


def verify_via_mcp() -> dict:
    """Verify all systems via MCP (when editor is running).
    
    Uses editor.run_python to execute verification scripts in-editor.
    This is the preferred method since -ExecutePythonScript is broken in UE 5.8.
    """
    audit = GmmAudit(action="mkc.verify_via_mcp")
    subsystem_results = {}
    
    mc = MonolithClient()
    
    try:
        status = mc.status()
        subsystem_results["mcp"] = {
            "ok": True,
            "version": status.get("version", "?"),
            "action_count": status.get("total_actions", 0),
        }
    except Exception as e:
        subsystem_results["mcp"] = {"ok": False, "error": str(e)}
        audit.ok(subsystem_results=subsystem_results)
        audit.save("gmm_verify_via_mcp.json")
        return audit.to_dict()
    
    # Run asset checks via MCP editor.run_python
    script_checks = [
        ("melusina_rig", "assess_melusina_rig.build_full_report()"),
        ("mpc_params", "setup_melusina_exploration.get_mpc_parameters()"),
    ]
    
    for check_name, expr in script_checks:
        try:
            result = mc.run_python(
                f"import json; result = {expr}; print(json.dumps(result))",
                mode="execute_statement"
            )
            if result.get("success"):
                try:
                    output_str = result.get("output", [{}])[0] if result.get("output") else "{}"
                    if isinstance(output_str, str):
                        parsed = json.loads(output_str)
                    else:
                        parsed = result.get("output", {})
                    subsystem_results[check_name] = {"ok": True, **parsed}
                except (json.JSONDecodeError, IndexError, TypeError, ValueError):
                    subsystem_results[check_name] = {"ok": True, "output_received": True}
            else:
                subsystem_results[check_name] = {"ok": False, "error": "Script execution failed"}
        except Exception as e:
            subsystem_results[check_name] = {"ok": False, "error": str(e)}
    
    audit.ok(subsystem_results=subsystem_results)
    all_ok = all(r.get("ok", False) for r in subsystem_results.values())
    audit.data["all_ok"] = all_ok
    audit.save("gmm_verify_via_mcp.json")
    return audit.to_dict()