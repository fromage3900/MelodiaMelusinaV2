# -*- coding: utf-8 -*-
"""Wire PCGComponent onto BP_MelusinaRoomShell, assign graph, Generate on SalonA.
Donor graphs: INSPECT ONLY (no overwrite). Receipt: Saved/Audit/pcgex_roomshell_wire_2026-09-20.json
"""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
import unreal

EAL = unreal.EditorAssetLibrary
SAVED = Path(unreal.Paths.project_saved_dir()) / "Audit"
OUT = SAVED / "pcgex_roomshell_wire_2026-09-20.json"

BP_PATH = "/Game/EnvSandbox/Blueprints/House/BP_MelusinaRoomShell"
GRAPH_PATH = "/Game/EnvSandbox/PCG/House/PCG_MelusinaRoomShell_PCGex"
MORNING = "/Game/Melodia/Levels/Opening/L_MelusinaMorning"
DONORS = [
    "/Game/EnvSandbox/PCG/House/PCG_MelusinaHouse_MorningDell",
    "/Game/EnvSandbox/PCG/Styles/Escher/PCG_EscherRecursiveRoom",
    "/Game/EnvSandbox/PCG/Styles/Escher/PCG_EscherRelativityRoom",
]


def _gather(bp):
    subsystem = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    library = unreal.SubobjectDataBlueprintFunctionLibrary
    handles = list(subsystem.k2_gather_subobject_data_for_blueprint(bp))
    rows = []
    for handle in handles:
        data = library.get_data(handle)
        obj = library.get_object(data)
        rows.append((handle, obj))
    return subsystem, library, rows


def _ensure_pcg(bp):
    subsystem, library, rows = _gather(bp)
    for handle, obj in rows:
        if obj is not None and isinstance(obj, unreal.PCGComponent):
            return handle, obj, "already"
    if not rows:
        raise RuntimeError("no_root_subobject")
    params = unreal.AddNewSubobjectParams(
        parent_handle=rows[0][0],
        new_class=unreal.PCGComponent,
        blueprint_context=bp,
    )
    new_handle, failure = subsystem.add_new_subobject(params)
    if not failure.is_empty():
        raise RuntimeError("add_pcg_failed: " + str(failure))
    try:
        subsystem.rename_subobject(new_handle, unreal.Text("PCG"))
    except Exception:
        pass
    subsystem, library, rows = _gather(bp)
    for handle, obj in rows:
        if obj is not None and isinstance(obj, unreal.PCGComponent):
            return handle, obj, "added"
    return new_handle, None, "added_but_not_found"


def _assign_graph(obj, graph):
    details = []
    if obj is None:
        return False, ["obj_none"]
    ok = False
    try:
        obj.set_graph(graph)
        details.append("set_graph")
        ok = True
    except Exception as e:
        details.append({"set_graph_err": str(e)})
        try:
            obj.set_editor_property("graph", graph)
            details.append("set_editor_property")
            ok = True
        except Exception as e2:
            details.append({"set_prop_err": str(e2)})
    try:
        obj.set_editor_property(
            "generation_trigger",
            unreal.PCGComponentGenerationTrigger.GENERATE_ON_DEMAND,
        )
        details.append("trigger_on_demand")
    except Exception as e:
        details.append({"trigger_err": str(e)})
    return ok, details


def _graph_inventory(path):
    """Inspect-only: nodes + user params if readable."""
    info = {"path": path, "exists": EAL.does_asset_exist(path)}
    if not info["exists"]:
        return info
    g = EAL.load_asset(path)
    info["type"] = type(g).__name__ if g else None
    nodes = []
    params = []
    try:
        # PCGGraph / PCGEx graph node iteration
        if hasattr(g, "get_nodes"):
            for n in g.get_nodes() or []:
                nodes.append({
                    "name": getattr(n, "node_title", None) or n.get_name(),
                    "class": n.get_class().get_name(),
                })
        elif hasattr(g, "nodes"):
            for n in list(g.nodes or []):
                nodes.append({
                    "name": n.get_name(),
                    "class": n.get_class().get_name(),
                })
        else:
            # fallback via editor property
            try:
                raw = g.get_editor_property("nodes")
                for n in list(raw or []):
                    nodes.append({
                        "name": n.get_name(),
                        "class": n.get_class().get_name(),
                    })
            except Exception as e:
                info["nodes_err"] = str(e)
    except Exception as e:
        info["nodes_err"] = str(e)
    # user parameters
    try:
        if hasattr(g, "get_user_parameters"):
            for p in g.get_user_parameters() or []:
                params.append(str(p))
        else:
            for prop in ["user_parameters", "graph_parameters", "parameters"]:
                try:
                    v = g.get_editor_property(prop)
                    params.append({"prop": prop, "val": str(v)[:500]})
                except Exception:
                    pass
    except Exception as e:
        info["params_err"] = str(e)
    # score room-shell closeness from node class/title keywords
    blob = " ".join(
        (n.get("name") or "") + " " + (n.get("class") or "") for n in nodes
    ).lower()
    score = 0
    reasons = []
    for kw, pts in [
        ("wall", 3), ("floor", 3), ("door", 4), ("room", 3), ("perimeter", 3),
        ("path", 2), ("rect", 2), ("grid", 2), ("socket", 2), ("pcgex", 1),
        ("spline", 1), ("spawn", 1), ("recursive", 1), ("escher", 1),
        ("house", 2), ("module", 2),
    ]:
        if kw in blob:
            score += pts
            reasons.append(kw)
    info["node_count"] = len(nodes)
    info["nodes"] = nodes[:80]
    info["params"] = params[:40]
    info["room_shell_score"] = score
    info["score_hits"] = reasons
    return info


def _ensure_morning():
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    name = world.get_name() if world else None
    if name != "L_MelusinaMorning":
        ok = les.load_level(MORNING)
        world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
        return {"loaded": bool(ok), "world": world.get_name() if world else None}
    return {"already": True, "world": name}


def main():
    report = {
        "schema": "melodia.pcgex_roomshell_wire.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "bp": BP_PATH,
        "graph": GRAPH_PATH,
        "donor_policy": "inspect_only_no_overwrite",
        "steps": [],
        "ok": False,
    }

    lvl = _ensure_morning()
    report["steps"].append({"level": lvl})

    if not EAL.does_asset_exist(BP_PATH) or not EAL.does_asset_exist(GRAPH_PATH):
        report["error"] = "missing_assets"
        OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print("WIRE_ERR missing")
        return 1

    # Donor inspect (no overwrite)
    donors = [_graph_inventory(p) for p in DONORS]
    current = _graph_inventory(GRAPH_PATH)
    report["donors"] = donors
    report["current_graph"] = {
        "path": current["path"],
        "node_count": current.get("node_count"),
        "room_shell_score": current.get("room_shell_score"),
        "score_hits": current.get("score_hits"),
        "nodes_sample": current.get("nodes", [])[:30],
        "params": current.get("params"),
    }
    ranked = sorted(
        [d for d in donors if d.get("exists")],
        key=lambda d: d.get("room_shell_score", 0),
        reverse=True,
    )
    report["donor_recommendation"] = {
        "closest": (ranked[0]["path"] if ranked else None),
        "score": (ranked[0].get("room_shell_score") if ranked else None),
        "hits": (ranked[0].get("score_hits") if ranked else None),
        "note": "inspect_only — await MA green before content swap",
    }

    bp = EAL.load_asset(BP_PATH)
    graph = EAL.load_asset(GRAPH_PATH)

    try:
        handle, obj, how = _ensure_pcg(bp)
        report["steps"].append({
            "ensure_pcg": {"how": how, "obj": (obj.get_name() if obj else None)}
        })
        assigned, details = _assign_graph(obj, graph)
        report["steps"].append({"assign": {"ok": assigned, "details": details}})
    except Exception as e:
        report["steps"].append({"ensure_err": str(e)})

    try:
        unreal.BlueprintEditorLibrary.compile_blueprint(bp)
        report["steps"].append({"compile": True})
    except Exception as e:
        report["steps"].append({"compile_err": str(e)})
    EAL.save_asset(BP_PATH)
    report["steps"].append({"saved": True})

    # Verify template has PCG
    try:
        _, _, rows = _gather(bp)
        report["steps"].append({
            "after_scs": [
                {"name": (o.get_name() if o else None),
                 "class": (o.get_class().get_name() if o else None)}
                for _, o in rows
            ]
        })
        report["ok"] = any(
            o and isinstance(o, unreal.PCGComponent) for _, o in rows
        )
    except Exception as e:
        report["steps"].append({"verify_err": str(e)})

    # Generate on live SalonA
    live = {"found": False}
    try:
        svc = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
        for a in svc.get_all_level_actors():
            if (a.get_actor_label() or "") != "WC_HouseRoomShell_SalonA":
                continue
            live["found"] = True
            t = a.get_actor_location()
            live["loc"] = [round(t.x, 1), round(t.y, 1), round(t.z, 1)]
            comps = list(a.get_components_by_class(unreal.PCGComponent) or [])
            live["comps"] = len(comps)
            for c in comps:
                try:
                    c.set_graph(graph)
                    live["set_graph"] = True
                except Exception as e:
                    live["set_graph_err"] = str(e)
                try:
                    g = c.get_graph()
                    live["get_graph"] = g.get_path_name() if g else None
                except Exception as e:
                    live["get_graph_err"] = str(e)
                try:
                    c.generate(True)
                    live["generate"] = True
                except Exception as e:
                    try:
                        c.cleanup_local_generation()
                        c.generate(True)
                        live["generate"] = True
                    except Exception as e2:
                        live["generate_err"] = [str(e), str(e2)]
            break
        if live["found"]:
            try:
                unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
                live["level_saved"] = True
            except Exception as e:
                live["level_save_err"] = str(e)
    except Exception as e:
        live["err"] = str(e)
    report["live_salona"] = live

    # BP params: still deferred
    report["bp_vars"] = {
        "status": "deferred_EdGraphPinType",
        "wanted": [
            "Width_cm", "Depth_cm", "Height_cm", "ModuleSize_cm",
            "Door_N", "Door_E", "Door_S", "Door_W",
        ],
    }

    OUT.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print("WIRE " + json.dumps({
        "ok": report.get("ok"),
        "donor_recommendation": report.get("donor_recommendation"),
        "live": live,
        "current_nodes": report.get("current_graph", {}).get("node_count"),
        "donors": [
            {"path": d["path"], "nodes": d.get("node_count"), "score": d.get("room_shell_score"), "hits": d.get("score_hits")}
            for d in donors
        ],
    }, default=str)[:6000])
    unreal.log("WIRE wrote " + str(OUT))
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
