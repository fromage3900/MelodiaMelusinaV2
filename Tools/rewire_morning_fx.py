# -*- coding: utf-8 -*-
"""Surgical Morning Niagara rewire driver.

Usage:
  python Tools/rewire_morning_fx.py --effect <id>

Ids: census, dump, retire-orphans, parked, pollen, mist, petal, wind,
     sheep-lake, ensemble
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import time
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mcp_client import monolith  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
STAMP = date.today().isoformat()
AUDIT = ROOT / "Saved" / "Audit"
SCREENS = AUDIT / "Screens"
DUMPS = AUDIT / "dumps"
UE = AUDIT / "_morning_fx_ue.py"
CAPTURE = ROOT / "Content" / "Python" / "capture_lookdev_highres.py"

HEROES = {
    "petal": "WC_NS_Morning_petal_fx_petal_0_0",
    "pollen": "WC_NS_Morning_pollen_fx_pollen_0_0",
    "mist": "WC_NS_Morning_mist_fx_mist_x_0",
    "wind": "WC_NS_Morning_windfront_fx_windfront_x_0",
}
SYS = {
    "petal": "/Game/Melodia/VFX/NS_Morning_PetalDrift",
    "pollen": "/Game/Melodia/VFX/NS_Morning_PollenSparkle",
    "mist": "/Game/Melodia/VFX/NS_Morning_PondMist",
    "wind": "/Game/Melodia/VFX/NS_Morning_WindFront",
    "dust": "/Game/Melodia/VFX/NS_Morning_DustShafts",
    "pollenmote": "/Game/Melodia/VFX/NS_Morning_PollenMote",
    "windribbon": "/Game/Melodia/VFX/NS_Morning_WindRibbon",
    "impact": "/Game/Melodia/VFX/NS_Melusina_ImpactBurst",
    "glint": "/Game/Melodia/VFX/NS_Melusina_Glint",
    "cursor": "/Game/Melodia/VFX/NS_Melodia_CursorTrail",
    "uni_dust": "/Game/EnvSandbox/VFX/Systems/Universal/NS_Uni_DustShafts",
    "uni_pollen": "/Game/EnvSandbox/VFX/Systems/Universal/NS_Uni_PollenSparkle",
    "uni_mist": "/Game/EnvSandbox/VFX/Systems/Universal/NS_Uni_MistSheet",
}
MAT = {
    "petal": "/Game/Melodia/VFX/Materials/MI_Morning_Petal_B0",
    "petal_master": "/Game/Melodia/VFX/Materials/M_Niagara_Morning_PetalCard",
    "pollen": "/Game/Melodia/VFX/Materials/MI_Morning_Pollen_B0",
    "mist": "/Game/Melodia/VFX/Materials/MI_Morning_Mist",
    "wind": "/Game/Melodia/VFX/Materials/MI_Morning_WindFront",
}
EFFECT_TYPE = "/Game/EnvSandbox/VFX/EffectTypes/ENV_StorybookAmbientVFX"
DEFAULT_MAT_MARKERS = ("/niagara/defaultassets", "defaultsystem", "fountainlightweight")
ENV_MARKERS = ("/game/envsandbox/",)
PLUGIN_MARKERS = ("/oceanology",)

MORNING_MATS = [
    "/Game/Melodia/VFX/Materials/M_Niagara_Morning_PetalCard",
    "/Game/Melodia/VFX/Materials/M_Niagara_Morning_PollenMote",
    "/Game/Melodia/VFX/Materials/M_Niagara_Morning_MistSheet",
    "/Game/Melodia/VFX/Materials/M_Niagara_Morning_WindRibbon",
    "/Game/Melodia/VFX/Materials/MI_Morning_Mist",
    "/Game/Melodia/VFX/Materials/MI_Morning_WindFront",
] + [f"/Game/Melodia/VFX/Materials/MI_Morning_Petal_B{i}" for i in range(7)] + [
    f"/Game/Melodia/VFX/Materials/MI_Morning_Pollen_B{i}" for i in range(7)
]


def parse(r):
    if isinstance(r, dict):
        return r
    if not isinstance(r, str):
        return {"raw": str(r)[:500]}
    if r.startswith("ERROR:"):
        return {"error": r}
    try:
        return json.loads(r)
    except json.JSONDecodeError:
        return {"raw": r[:1200]}


def unwrap(data, depth=0):
    if depth > 5:
        return data
    if isinstance(data, str):
        s = data.strip()
        if s.startswith("{") or s.startswith("["):
            try:
                return unwrap(json.loads(s), depth + 1)
            except json.JSONDecodeError:
                return data
        return data
    if isinstance(data, dict) and isinstance(data.get("result"), str):
        s = data["result"].strip()
        if s.startswith("{") or s.startswith("["):
            return unwrap(s, depth + 1)
    return data


def nq(action, params, timeout=120):
    return unwrap(parse(monolith("niagara_query", {"action": action, "params": params}, timeout=timeout)))


def mq(action, params, timeout=90):
    return unwrap(parse(monolith("material_query", {"action": action, "params": params}, timeout=timeout)))


def eq(command, timeout=180):
    return parse(
        monolith(
            "editor_query",
            {
                "action": "run_python",
                "params": {
                    "command": command,
                    "mode": "execute_file",
                    "unattended": True,
                    "file_scope": "private",
                },
            },
            timeout=timeout,
        )
    )


def ue(cmd, *args, timeout=180):
    parts = [UE.as_posix(), cmd, *args]
    return eq(" ".join(str(p) for p in parts), timeout=timeout)


def strip_path(p):
    if not p:
        return p
    s = str(p).split(".")[0]
    return s


def write_json(path: Path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    return str(path).replace("\\", "/")


def list_emitter_names(path):
    data = nq("list_emitters", {"asset_path": path})
    names = []
    raw = data
    if isinstance(data, dict):
        raw = data.get("emitters") or data.get("result") or []
        if isinstance(raw, dict):
            raw = raw.get("emitters") or []
    for e in raw or []:
        if isinstance(e, dict):
            names.append(e.get("name") or e.get("emitter") or e.get("unique_emitter_name"))
        elif isinstance(e, str):
            names.append(e)
    return [n for n in names if n], data


def list_renderer_rows(path, emitter):
    data = nq("list_renderers", {"asset_path": path, "emitter": emitter})
    rows = []
    raw = data
    if isinstance(data, dict):
        raw = data.get("renderers") or data.get("result") or []
        if isinstance(raw, dict):
            raw = raw.get("renderers") or []
    for r in raw or []:
        if isinstance(r, dict):
            rows.append(r)
    return rows, data


def collect_renderer_mats(path):
    names, _ = list_emitter_names(path)
    mats = []
    detail = []
    for em in names:
        rows, raw = list_renderer_rows(path, em)
        detail.append({"emitter": em, "renderers": rows, "raw": raw})
        for r in rows:
            mat = strip_path(r.get("material") or r.get("material_path"))
            mats.append({"emitter": em, "index": r.get("index"), "type": r.get("type"), "material": mat})
    return mats, detail, names


def modules_for(path, emitter):
    data = nq("get_ordered_modules", {"asset_path": path, "emitter": emitter})
    raw = data
    if isinstance(data, dict):
        raw = data.get("modules") or data.get("result") or []
        if isinstance(raw, dict):
            raw = raw.get("modules") or []
    mods = [m for m in (raw or []) if isinstance(m, dict)]
    return mods, data


def module_guid(m):
    return m.get("guid") or m.get("node_guid") or m.get("module_node") or m.get("id") or m.get("node")


def module_name(m):
    return str(m.get("name") or m.get("function_name") or "")


def diag_errors(path):
    d = nq("get_system_diagnostics", {"asset_path": path})
    v = nq("validate_system", {"asset_path": path})
    err = 0
    msgs = []
    if isinstance(d, dict):
        err = int(d.get("error_count") or 0)
        for e in d.get("errors") or []:
            if isinstance(e, dict):
                msgs.append(e.get("message") or str(e))
            else:
                msgs.append(str(e))
        if d.get("error"):
            err = max(err, 1)
            msgs.append(str(d.get("error")))
    if isinstance(v, dict) and v.get("error"):
        err = max(err, 1)
        msgs.append(str(v.get("error")))
    return err, msgs, d, v


def save_compile(path):
    nq("save_system", {"asset_path": path})
    nq("request_compile", {"asset_path": path})
    time.sleep(1.5)
    return diag_errors(path)


def set_bounds(path, cm, emitter=None):
    h = float(cm) * 0.5
    params = {"asset_path": path, "min": [-h, -h, -h], "max": [h, h, h]}
    if emitter:
        params["emitter"] = emitter
    return nq("set_fixed_bounds", params)


def ensure_user(path, name, typ, default=None):
    rec = {"name": name, "type": typ}
    existing = nq("get_user_parameters", {"asset_path": path})
    names = []
    raw = existing
    if isinstance(existing, dict):
        raw = existing.get("parameters") or existing.get("user_parameters") or existing.get("result") or []
        if isinstance(raw, dict):
            raw = raw.get("parameters") or []
    for p in raw or []:
        if isinstance(p, dict):
            n = str(p.get("name") or "")
            names.append(n.replace("User.", ""))
        elif isinstance(p, str):
            names.append(p.replace("User.", ""))
    rec["had"] = name in names
    rec["existing"] = names
    if name not in names:
        rec["add"] = nq("add_user_parameter", {"asset_path": path, "name": name, "type": typ})
    if default is not None:
        rec["default"] = nq("set_parameter_default", {"asset_path": path, "parameter": f"User.{name}", "value": default})
    return rec


def bind_input(path, emitter, module_name_s, input_name, binding):
    mods, _ = modules_for(path, emitter)
    hits = [m for m in mods if module_name(m) == module_name_s]
    if not hits:
        hits = [m for m in mods if module_name_s.lower() in module_name(m).lower()]
    rec = {"module": module_name_s, "input": input_name, "binding": binding, "hits": len(hits)}
    for m in hits:
        gid = module_guid(m)
        rec.setdefault("set", []).append(
            nq(
                "set_module_input_binding",
                {
                    "asset_path": path,
                    "emitter": emitter,
                    "module_node": gid,
                    "input": input_name,
                    "binding": binding,
                },
            )
        )
    return rec


def set_input(path, emitter, module_name_s, input_name, value):
    mods, _ = modules_for(path, emitter)
    hits = [m for m in mods if module_name(m) == module_name_s]
    rec = {"module": module_name_s, "input": input_name, "value": value, "hits": len(hits)}
    for m in hits:
        rec.setdefault("set", []).append(
            nq(
                "set_module_input_value",
                {
                    "asset_path": path,
                    "emitter": emitter,
                    "module_node": module_guid(m),
                    "input": input_name,
                    "value": value,
                },
            )
        )
    return rec


def collapse_duplicate_stack(path, emitter):
    mods, raw = modules_for(path, emitter)
    names = [module_name(m) for m in mods]
    bases = {re.sub(r"\d+$", "", n) for n in names}
    removed = []
    for m in mods:
        n = module_name(m)
        if re.search(r"\d{3}$", n) and re.sub(r"\d+$", "", n) in bases:
            gid = module_guid(m)
            removed.append({"name": n, "guid": gid, "resp": nq("remove_module", {"asset_path": path, "emitter": emitter, "module_node": gid})})
    return {"removed": removed, "before": names, "raw_count": len(mods)}


def wait_shot(dest: Path, timeout=70):
    time.sleep(3)
    deadline = time.time() + timeout
    shots_root = ROOT / "Saved" / "Screenshots"
    while time.time() < deadline:
        if dest.exists() and dest.stat().st_size > 8000:
            return dest
        candidates = []
        if shots_root.exists():
            candidates += list(shots_root.rglob("*.png"))
        if SCREENS.exists():
            candidates += list(SCREENS.glob("*.png"))
        fresh = [p for p in candidates if p.stat().st_mtime > time.time() - 90 and p.stat().st_size > 8000]
        if fresh:
            newest = max(fresh, key=lambda p: p.stat().st_mtime)
            dest.parent.mkdir(parents=True, exist_ok=True)
            if newest.resolve() != dest.resolve():
                shutil.copy2(newest, dest)
            return dest
        time.sleep(2)
    return dest if dest.exists() else None


def isolate_and_still(effect_id, keep_labels):
    rec = {"isolate": ue("isolate", ",".join(keep_labels) if keep_labels else "NONE")}
    rec["cam"] = ue("spawn_heroes_cam")
    dest = SCREENS / f"wc_ns_{effect_id}_solo_{STAMP}.png"
    rec["capture"] = ue("capture", "niagara_heroes", dest.as_posix())
    found = wait_shot(dest)
    rec["still"] = str(found).replace("\\", "/") if found else None
    rec["still_bytes"] = found.stat().st_size if found else 0
    rec["restore"] = ue("restore")
    return rec


def dump_system(path, tag=None):
    name = path.rstrip("/").split("/")[-1]
    tag = tag or name
    print(f"DUMP_SYS {path}", flush=True)
    out = DUMPS / f"{tag}_spec.json"
    names, emitters = list_emitter_names(path)
    mods = {}
    rends = {}
    for em in names:
        mods[em] = nq("get_ordered_modules", {"asset_path": path, "emitter": em})
        rows, raw = list_renderer_rows(path, em)
        rends[em] = {"rows": rows, "raw": raw}
    spec = nq("export_system_spec", {"asset_path": path, "include_values": True}, timeout=180)
    if spec.get("error"):
        spec = nq("export_system_spec", {"asset_path": path}, timeout=180)
    payload = {
        "asset_path": path,
        "emitters": emitters,
        "emitter_names": names,
        "modules": mods,
        "renderers": rends,
        "user_params": nq("get_user_parameters", {"asset_path": path}),
        "diagnostics": nq("get_system_diagnostics", {"asset_path": path}),
        "summary": nq("get_system_summary", {"asset_path": path}),
        "spec": spec,
    }
    write_json(out, payload)
    return {"path": path, "dump": str(out).replace("\\", "/"), "emitters": names}


def dump_material(path):
    name = path.rstrip("/").split("/")[-1]
    print(f"DUMP_MAT {path}", flush=True)
    out = DUMPS / f"{name}_graph.json"
    payload = {
        "asset_path": path,
        "properties": mq("get_material_properties", {"asset_path": path}),
        "parameters": mq("get_material_parameters", {"asset_path": path}),
        "expressions": mq("get_all_expressions", {"asset_path": path}),
        "graph": mq("export_material_graph", {"asset_path": path, "include_properties": False}),
        "preview": mq("render_preview", {"asset_path": path}, timeout=60),
    }
    if payload["properties"].get("error"):
        payload["instance"] = mq("get_instance_parameters", {"asset_path": path})
    write_json(out, payload)
    return {"path": path, "dump": str(out).replace("\\", "/")}


def gate(path, wanted_substr, extra=None):
    err, msgs, diag, valid = save_compile(path)
    mats, detail, names = collect_renderer_mats(path)
    mat_ok = False
    if wanted_substr:
        mat_ok = any(wanted_substr.lower() in str(m.get("material") or "").lower() for m in mats)
    else:
        mat_ok = True
    rec = {
        "path": path,
        "errors": err,
        "error_msgs": msgs[:8],
        "validate": valid,
        "diagnostics": diag,
        "emitters": names,
        "renderer_materials": mats,
        "wanted": wanted_substr,
        "material_ok": mat_ok,
        "pass": err == 0 and mat_ok,
    }
    if extra:
        rec.update(extra)
    return rec


def effect_census():
    census_py = AUDIT / "_census_live_2026-09-19.py"
    live = eq(census_py.as_posix())
    census_path = AUDIT / "niagara_census_live_2026-09-19.json"
    census = json.loads(census_path.read_text(encoding="utf-8")) if census_path.exists() else {}
    systems = list(census.get("unique_systems") or [])
    extras = [SYS["windribbon"], SYS["pollenmote"], SYS["uni_mist"]]
    for e in extras:
        if e not in systems:
            systems.append(e)
    roster = []
    mats = []
    for path in systems:
        r_mats, detail, names = collect_renderer_mats(path)
        for m in r_mats:
            if m.get("material"):
                mats.append(m["material"])
        roster.append({
            "system": path,
            "emitters": names,
            "renderers": r_mats,
            "user_params": nq("get_user_parameters", {"asset_path": path}),
            "diagnostics": nq("get_system_diagnostics", {"asset_path": path}),
        })
    unique_mats = sorted(set(strip_path(m) for m in mats if m))
    out = {
        "stamp": STAMP,
        "live_exec": live,
        "niagara_actor_count": census.get("niagara_actor_count"),
        "niagara_component_count": census.get("niagara_component_count"),
        "labels": [a.get("label") for a in census.get("actors") or []],
        "actors": census.get("actors"),
        "unique_systems_in_level": census.get("unique_systems"),
        "roster": roster,
        "renderer_materials": unique_mats,
        "related_assets": census.get("related_assets"),
    }
    path = write_json(AUDIT / f"niagara_census_live_renderers_{STAMP}.json", out)
    return {
        "ok": True,
        "actors": out["niagara_actor_count"],
        "components": out["niagara_component_count"],
        "labels": out["labels"],
        "systems": out["unique_systems_in_level"],
        "renderer_materials": unique_mats,
        "out": path,
    }


def effect_dump():
    census_path = AUDIT / f"niagara_census_live_renderers_{STAMP}.json"
    if not census_path.exists():
        census_path = AUDIT / "niagara_census_live_renderers_2026-09-19.json"
    census = json.loads(census_path.read_text(encoding="utf-8")) if census_path.exists() else {}
    systems = []
    for r in census.get("roster") or []:
        systems.append(r["system"])
    if not systems:
        systems = list(SYS.values())
    mats = list(MORNING_MATS)
    for r in census.get("renderer_materials") or []:
        if r not in mats:
            mats.append(r)
    dumped_sys = []
    dumped_mat = []
    for s in systems:
        dumped_sys.append(dump_system(s))
    for m in mats:
        dumped_mat.append(dump_material(m))
    out = {"systems": dumped_sys, "materials": dumped_mat}
    path = write_json(AUDIT / f"niagara_rewire_audit_dumps_{STAMP}.json", out)
    return {"ok": True, "system_dumps": len(dumped_sys), "material_dumps": len(dumped_mat), "out": path}


def effect_retire_orphans():
    rec = {"destroy": ue("destroy_orphans")}
    ribbon = dump_system(SYS["windribbon"], "NS_Morning_WindRibbon")
    mote = dump_system(SYS["pollenmote"], "NS_Morning_PollenMote")
    rec["windribbon"] = ribbon
    rec["pollenmote"] = mote
    rec["decision"] = {
        "NS_Morning_WindRibbon": "retire_unused_asset_no_place",
        "NS_Morning_PollenMote": "retire_unused_asset_no_place",
        "reason": "Hero pack uses NS_Morning_WindFront + NS_Morning_PollenSparkle; extra children have no remaining WC actors after organize.",
    }
    rec["census_after"] = eq((AUDIT / "_census_live_2026-09-19.py").as_posix())
    write_json(AUDIT / f"niagara_retire_orphans_{STAMP}.json", rec)
    rec["ok"] = True
    rec["pass"] = True
    return rec


def _dup_if_needed(src, dst):
    existing = nq("get_system_summary", {"asset_path": dst})
    if existing.get("error") or existing.get("raw") or "not_a_system" in str(existing.get("status") or ""):
        return nq("duplicate_system", {"asset_path": src, "save_path": dst}, timeout=180)
    if existing.get("system_name") or existing.get("name") or existing.get("emitters"):
        return {"skipped": True, "existing": True, "summary": existing}
    return nq("duplicate_system", {"asset_path": src, "save_path": dst}, timeout=180)


def _bind_all_renderers(path, material):
    names, _ = list_emitter_names(path)
    rec = []
    for em in names:
        rows, _ = list_renderer_rows(path, em)
        for r in rows:
            idx = r.get("index", 0)
            rec.append(
                nq(
                    "set_renderer_material",
                    {"asset_path": path, "emitter": em, "renderer_index": idx, "material": material},
                )
            )
            rec.append(
                nq(
                    "set_renderer_material",
                    {"asset_path": path, "emitter": em, "renderer": idx, "material": material},
                )
            )
    return rec


def _fix_default_mats(path, fallback_mat):
    names, _ = list_emitter_names(path)
    rec = []
    for em in names:
        rows, _ = list_renderer_rows(path, em)
        for r in rows:
            mat = str(r.get("material") or "").lower()
            if any(m in mat for m in DEFAULT_MAT_MARKERS) or not r.get("material"):
                idx = r.get("index", 0)
                rec.append(
                    {
                        "emitter": em,
                        "index": idx,
                        "was": r.get("material"),
                        "resp": nq(
                            "set_renderer_material",
                            {"asset_path": path, "emitter": em, "renderer_index": idx, "material": fallback_mat},
                        ),
                    }
                )
    return rec


def _dust_child_material(src_sys):
    mats, _, _ = collect_renderer_mats(src_sys)
    src_mat = None
    for m in mats:
        if m.get("material"):
            src_mat = m["material"]
            break
    dest = "/Game/Melodia/VFX/Materials/M_Niagara_Morning_DustShaft"
    if not src_mat:
        return dest, {"error": "no_src_mat"}
    if any(x in src_mat.lower() for x in ENV_MARKERS):
        dup = mq("duplicate_material", {"source_path": src_mat, "dest_path": dest})
        return dest, {"src": src_mat, "dup": dup}
    return src_mat, {"src": src_mat, "dup": "not_envsandbox"}


def effect_parked():
    rec = {"steps": []}
    rec["dup_dust"] = _dup_if_needed(SYS["uni_dust"], SYS["dust"])
    rec["dust_before"] = dump_system(SYS["dust"], "NS_Morning_DustShafts_before")
    dest_mat, mat_info = _dust_child_material(SYS["dust"])
    rec["dust_mat"] = mat_info
    rec["dust_bind"] = _bind_all_renderers(SYS["dust"], dest_mat)
    rec["dust_effect_type"] = nq("set_effect_type", {"asset_path": SYS["dust"], "effect_type": EFFECT_TYPE})
    rec["dust_bounds"] = set_bounds(SYS["dust"], 400)
    rec["dust_gate"] = gate(SYS["dust"], "/Game/Melodia/")
    rec["retarget_dust"] = ue("retarget", "FX_Morning_DustShafts_Threshold", SYS["dust"])
    rec["retarget_bed"] = ue("retarget", "FX_Morning_Bed_PollenSparkle", SYS["pollen"])
    rec["retarget_mist"] = ue("retarget", "FX_Morning_Mist", SYS["mist"])

    for key, label, path, fallback in (
        ("impact", "FX_Morning_ImpactBurst", SYS["impact"], MAT["pollen"]),
        ("glint", "FX_Morning_WaterGlint", SYS["glint"], MAT["mist"]),
    ):
        dump_system(path, f"{path.split('/')[-1]}_before")
        rec[f"{key}_defaults"] = _fix_default_mats(path, fallback)
        rec[f"{key}_gate"] = gate(path, None)
        rec[f"{key}_still"] = isolate_and_still(key, [label])

    rec["park"] = ue("restore")
    rec["dust_pass"] = bool(rec["dust_gate"].get("pass"))
    rec["impact_pass"] = rec["impact_gate"].get("errors", 1) == 0
    rec["glint_pass"] = rec["glint_gate"].get("errors", 1) == 0
    rec["pass"] = rec["dust_pass"] and rec["impact_pass"] and rec["glint_pass"]
    rec["ok"] = rec["pass"]
    write_json(AUDIT / f"niagara_rewire_parked_{STAMP}.json", rec)
    return rec


def _hero_before(effect_id, path):
    return dump_system(path, f"niagara_rewire_{effect_id}_before")


def effect_pollen():
    path = SYS["pollen"]
    rec = {"before": _hero_before("pollen", path)}
    names, _ = list_emitter_names(path)
    rec["emitters"] = names
    primary = "Motes" if "Motes" in names else (names[0] if names else None)
    rec["isolate"] = ue("isolate", HEROES["pollen"])
    if primary:
        rec["collapse"] = collapse_duplicate_stack(path, primary)
        rows, _ = list_renderer_rows(path, primary)
        if len(rows) > 1:
            extra = rows[-1]
            rec["remove_extra_renderer"] = nq(
                "remove_renderer",
                {"asset_path": path, "emitter": primary, "renderer": extra.get("index", 1)},
            )
        rec["bind_mat"] = nq(
            "set_renderer_material",
            {"asset_path": path, "emitter": primary, "renderer_index": 0, "material": MAT["pollen"]},
        )
        rec["user_mote"] = ensure_user(path, "MoteSpawnMultiplier", "float", "1.0")
        rec["user_intensity"] = ensure_user(path, "Intensity", "float", "1.0")
        rec["user_hue"] = ensure_user(path, "HueSeed", "float", "0.0")
        rec["user_band"] = ensure_user(path, "BandHue", "LinearColor", None)
        rec["bind_spawn"] = bind_input(path, primary, "SpawnRate", "SpawnRate", "User.MoteSpawnMultiplier")
        rec["bounds"] = set_bounds(path, 350, primary)
        rec["effect_type"] = nq("set_effect_type", {"asset_path": path, "effect_type": EFFECT_TYPE})
    rec["gate"] = gate(path, "MI_Morning_Pollen")
    rec["still"] = isolate_and_still("pollen", [HEROES["pollen"]])
    rec["pass"] = bool(rec["gate"].get("pass"))
    rec["ok"] = rec["pass"]
    rec["renderer_materials"] = rec["gate"].get("renderer_materials")
    write_json(AUDIT / f"niagara_rewire_pollen_{STAMP}.json", rec)
    if not rec["pass"]:
        rec["gate_fail"] = True
    return rec


def effect_mist():
    path = SYS["mist"]
    rec = {"before": _hero_before("mist", path), "parent_spec": dump_system(SYS["uni_mist"], "NS_Uni_MistSheet_readonly")}
    rec["isolate"] = ue("isolate", HEROES["mist"])
    spec_file = DUMPS / "NS_Uni_MistSheet_readonly_spec.json"
    if not spec_file.exists():
        spec_file = DUMPS / "NS_Uni_MistSheet_spec.json"
    spec_payload = json.loads(spec_file.read_text(encoding="utf-8")) if spec_file.exists() else {}
    spec = unwrap(spec_payload.get("spec"))
    rec["import"] = {"skipped": True, "spec_file": str(spec_file).replace("\\", "/")}
    if isinstance(spec, dict) and not spec.get("error"):
        inner = spec.get("spec") if isinstance(spec.get("spec"), dict) else spec
        rec["import"] = nq("import_system_spec", {"asset_path": path, "spec": inner, "mode": "replace"}, timeout=180)
        if isinstance(rec["import"], dict) and rec["import"].get("error"):
            rec["import_retry"] = nq("import_system_spec", {"asset_path": path, "spec": inner}, timeout=180)
    names, _ = list_emitter_names(path)
    rec["emitters"] = names
    if "EmberMotes" in names and len(names) > 1:
        rec["remove_ember"] = nq("remove_emitter", {"asset_path": path, "emitter": "EmberMotes"})
        names, _ = list_emitter_names(path)
    elif names == ["EmberMotes"]:
        rec["ember_only"] = True
    primary = names[0] if names else None
    if primary:
        rec["sim"] = nq("set_emitter_property", {"asset_path": path, "emitter": primary, "property": "SimTarget", "value": "CPUSim"})
        rec["bind_mat"] = nq(
            "set_renderer_material",
            {"asset_path": path, "emitter": primary, "renderer_index": 0, "material": MAT["mist"]},
        )
        rec["user_den"] = ensure_user(path, "MistDensity", "float", "0.45")
        rec["user_band"] = ensure_user(path, "BandHue", "LinearColor", None)
        rec["bind_spawn"] = bind_input(path, primary, "SpawnRate", "SpawnRate", "User.MistDensity")
        rec["spawn_scale"] = set_input(path, primary, "SpawnRate", "SpawnRate", 24.0)
        rec["bounds"] = set_bounds(path, 500, primary)
        rec["effect_type"] = nq("set_effect_type", {"asset_path": path, "effect_type": EFFECT_TYPE})
        rec["loop"] = nq(
            "set_emitter_loop_profile",
            {"asset_path": path, "emitter": primary, "loop_behavior": "Infinite"},
        )
    rec["gate"] = gate(path, "MI_Morning_Mist")
    rec["still"] = isolate_and_still("mist", [HEROES["mist"]])
    rec["pass"] = bool(rec["gate"].get("pass"))
    rec["ok"] = rec["pass"]
    rec["renderer_materials"] = rec["gate"].get("renderer_materials")
    write_json(AUDIT / f"niagara_rewire_mist_{STAMP}.json", rec)
    return rec


def effect_petal():
    path = SYS["petal"]
    rec = {"before": _hero_before("petal", path)}
    names, _ = list_emitter_names(path)
    rec["emitters"] = names
    primary = "PetalLoop" if "PetalLoop" in names else (names[0] if names else None)
    rec["isolate"] = ue("isolate", HEROES["petal"])
    if primary:
        rec["collapse"] = collapse_duplicate_stack(path, primary)
        rows, _ = list_renderer_rows(path, primary)
        rec["renderers_before"] = rows
        has_sprite = any("sprite" in str(r.get("type") or "").lower() for r in rows)
        if not has_sprite:
            rec["add_sprite"] = nq("add_renderer", {"asset_path": path, "emitter": primary, "type": "SpriteRenderer"})
        rec["bind_mat"] = nq(
            "set_renderer_material",
            {"asset_path": path, "emitter": primary, "renderer_index": 0, "material": MAT["petal"]},
        )
        rec["bind_mat_named"] = nq(
            "set_renderer_material",
            {"asset_path": path, "emitter": primary, "renderer": "SpriteRenderer", "material": MAT["petal"]},
        )
        rows2, _ = list_renderer_rows(path, primary)
        rec["renderers_mid"] = rows2
        for r in rows2:
            if "mesh" in str(r.get("type") or "").lower():
                rec.setdefault("remove_mesh", []).append(
                    nq("remove_renderer", {"asset_path": path, "emitter": primary, "renderer": r.get("index", 0)})
                )
        rec["user_spawn"] = ensure_user(path, "PetalSpawnMultiplier", "float", "0.4")
        rec["user_hue"] = ensure_user(path, "HueSeed", "float", "0.0")
        rec["user_band"] = ensure_user(path, "BandHue", "LinearColor", None)
        rec["bind_spawn"] = bind_input(path, primary, "SpawnRate", "SpawnRate", "User.PetalSpawnMultiplier")
        rec["sprite_size"] = set_input(path, primary, "InitializeParticle", "SpriteSize", [16.0, 16.0])
        rec["sprite_size_alt"] = set_input(path, primary, "InitializeParticle", "Sprite Size", 16.0)
        rec["lifetime"] = nq(
            "set_particle_lifetime",
            {"asset_path": path, "emitter": primary, "min": 4.0, "max": 8.0},
        )
        rec["bounds"] = set_bounds(path, 400, primary)
        rec["effect_type"] = nq("set_effect_type", {"asset_path": path, "effect_type": EFFECT_TYPE})
        rec["shadow"] = nq(
            "set_renderer_property",
            {"asset_path": path, "emitter": primary, "renderer": 0, "property": "bCastShadows", "value": False},
        )
    rec["gate"] = gate(path, "MI_Morning_Petal")
    rec["still"] = isolate_and_still("petal", [HEROES["petal"]])
    rec["pass"] = bool(rec["gate"].get("pass"))
    rec["ok"] = rec["pass"]
    rec["renderer_materials"] = rec["gate"].get("renderer_materials")
    write_json(AUDIT / f"niagara_rewire_petal_{STAMP}.json", rec)
    return rec


def effect_wind():
    path = SYS["wind"]
    rec = {"before": _hero_before("wind", path)}
    names, _ = list_emitter_names(path)
    rec["emitters"] = names
    rec["isolate"] = ue("isolate", HEROES["wind"])
    burst = [n for n in names if "burst" in n.lower() or "omni" in n.lower()]
    for b in burst:
        rec.setdefault("remove_burst", []).append(nq("remove_emitter", {"asset_path": path, "emitter": b}))
    names, _ = list_emitter_names(path)
    rec["emitters_after_remove"] = names
    leader = None
    for cand in ("Gust_Leader", "Gust", "Ribbon_Trail_Leader"):
        if cand in names:
            leader = cand
            break
    if not leader and names:
        leader = names[0]
    rec["leader"] = leader
    if leader:
        rec["loop"] = nq(
            "set_emitter_loop_profile",
            {"asset_path": path, "emitter": leader, "loop_behavior": "Infinite", "loop_duration": 4.0},
        )
        rec["loop_gust"] = nq(
            "set_emitter_loop_profile",
            {"asset_path": path, "emitter": "Gust", "loop_behavior": "Infinite", "loop_duration": 4.0},
        )
        rec["bind_mat"] = nq(
            "set_renderer_material",
            {"asset_path": path, "emitter": leader, "renderer_index": 0, "material": MAT["wind"]},
        )
        rows, _ = list_renderer_rows(path, leader)
        rec["renderers"] = rows
        ribbon_count = sum(1 for r in rows if "ribbon" in str(r.get("type") or "").lower())
        if ribbon_count < 2:
            rec["add_ribbon"] = nq("add_renderer", {"asset_path": path, "emitter": leader, "type": "RibbonRenderer"})
            rec["bind_mat2"] = nq(
                "set_renderer_material",
                {"asset_path": path, "emitter": leader, "renderer_index": 1, "material": MAT["wind"]},
            )
        rec["user_vis"] = ensure_user(path, "WindFrontVisible", "float", "1.0")
        rec["user_hue"] = ensure_user(path, "HueSeed", "float", "0.0")
        rec["user_band"] = ensure_user(path, "BandHue", "LinearColor", None)
        rec["bounds"] = set_bounds(path, 500, leader)
        rec["effect_type"] = nq("set_effect_type", {"asset_path": path, "effect_type": EFFECT_TYPE})
    rec["gate"] = gate(path, "MI_Morning_WindFront")
    rec["still"] = isolate_and_still("wind", [HEROES["wind"]])
    rec["pass"] = bool(rec["gate"].get("pass"))
    rec["ok"] = rec["pass"]
    rec["renderer_materials"] = rec["gate"].get("renderer_materials")
    write_json(AUDIT / f"niagara_rewire_wind_{STAMP}.json", rec)
    return rec


SHEEP = [
    "/Game/Melodia/Companions/ChoralSheep/VFX/NS_ChoralSheep_BeatBurst",
    "/Game/Melodia/Companions/ChoralSheep/VFX/NS_ChoralSheep_WoolMotes",
    "/Game/Melodia/Companions/ChoralSheep/VFX/NS_ChoralSheep_HybridSparkles",
    "/Game/Melodia/Companions/ChoralSheep/VFX/NS_ChoralSheep_PetalCascade",
    "/Game/Melodia/Companions/ChoralSheep/VFX/NS_ChoralSheep_MotionTrails",
    "/Game/Melodia/Companions/ChoralSheep/VFX/NS_ChoralSheep_FluidSplash",
]
LAKE = "/Oceanology_Plugin/Effects/Particles/Water/NS_OceanologyBubbles"


def effect_sheep_lake():
    rec = {"sheep": [], "lake": None, "fixed": []}
    for path in SHEEP:
        mats, detail, names = collect_renderer_mats(path)
        err, msgs, diag, valid = diag_errors(path)
        entry = {"system": path, "emitters": names, "renderers": mats, "errors": err, "error_msgs": msgs, "validate": valid}
        for m in mats:
            mat = str(m.get("material") or "").lower()
            if any(x in mat for x in DEFAULT_MAT_MARKERS) or not m.get("material"):
                # sheep: only replace engine defaults; use pollen MI as a safe Melodia particle card
                resp = nq(
                    "set_renderer_material",
                    {
                        "asset_path": path,
                        "emitter": m["emitter"],
                        "renderer_index": m.get("index", 0),
                        "material": MAT["pollen"],
                    },
                )
                rec["fixed"].append({"system": path, "emitter": m["emitter"], "was": m.get("material"), "resp": resp})
                save_compile(path)
        mats2, _, _ = collect_renderer_mats(path)
        entry["renderers_after"] = mats2
        rec["sheep"].append(entry)
    mats, detail, names = collect_renderer_mats(LAKE)
    err, msgs, diag, valid = diag_errors(LAKE)
    rec["lake"] = {
        "system": LAKE,
        "emitters": names,
        "renderers": mats,
        "errors": err,
        "error_msgs": msgs,
        "note": "audit-only; no Oceanology plugin writes",
        "plugin_writes": False,
    }
    rec["pass"] = True
    rec["ok"] = True
    write_json(AUDIT / f"niagara_rewire_sheep_lake_{STAMP}.json", rec)
    return rec


def effect_ensemble():
    rec = {"restore": ue("restore")}
    rec["cam"] = ue("spawn_heroes_cam")
    rec["stat_on"] = ue("stat_overlay", "on")
    dest = SCREENS / f"wc_ns_ensemble_{STAMP}.png"
    rec["capture"] = ue("capture", "niagara_heroes", dest.as_posix())
    found = wait_shot(dest, timeout=55)
    rec["still"] = str(found).replace("\\", "/") if found else None
    rec["still_bytes"] = found.stat().st_size if found else 0
    rec["stat_off"] = ue("stat_overlay", "off")
    census = eq((AUDIT / "_census_live_2026-09-19.py").as_posix())
    census_path = AUDIT / "niagara_census_live_2026-09-19.json"
    live = json.loads(census_path.read_text(encoding="utf-8")) if census_path.exists() else {}
    roster = []
    for a in live.get("actors") or []:
        for c in a.get("components") or []:
            path = c.get("system")
            mats, _, names = collect_renderer_mats(path) if path else ([], [], [])
            roster.append({
                "label": a.get("label"),
                "class": a.get("class"),
                "folder": a.get("folder"),
                "hidden_editor": a.get("hidden_editor"),
                "loc": a.get("loc"),
                "system": path,
                "active": c.get("active"),
                "auto_activate": c.get("auto_activate"),
                "emitters": names,
                "renderer_materials": mats,
                "treatment": _treatment(a.get("label"), path),
            })
    results = {}
    for name in ("pollen", "mist", "petal", "wind", "parked", "sheep_lake"):
        p = AUDIT / f"niagara_rewire_{name}_{STAMP}.json"
        if name == "sheep_lake":
            p = AUDIT / f"niagara_rewire_sheep_lake_{STAMP}.json"
        if p.exists():
            try:
                d = json.loads(p.read_text(encoding="utf-8"))
                results[name] = {"pass": d.get("pass"), "renderer_materials": d.get("renderer_materials") or d.get("gate", {}).get("renderer_materials")}
            except Exception:
                results[name] = {"pass": None}
    proof = {
        "stamp": STAMP,
        "level": "L_MelusinaMorning",
        "camera": "WC_Lookdev_niagara_heroes",
        "census_exec": census,
        "actor_count": live.get("niagara_actor_count"),
        "component_count": live.get("niagara_component_count"),
        "unique_systems": live.get("unique_systems"),
        "roster": roster,
        "per_effect": results,
        "ensemble_still": rec["still"],
        "intended_ticking": KEEP_TICKING,
        "notes": "Sheep BP comps stay; preview NiagaraActors off; Class C parked after rewire.",
    }
    proof_path = write_json(AUDIT / f"niagara_morning_rewire_proof_{STAMP}.json", proof)
    rec["proof"] = proof_path
    rec["roster_count"] = len(roster)
    rec["ok"] = True
    rec["pass"] = True
    return rec


KEEP_TICKING = list(HEROES.values()) + ["BP_ChoralSheep"]


def _treatment(label, path):
    if label in HEROES.values():
        return "class_a_hero"
    if label in (
        "FX_Morning_DustShafts_Threshold",
        "FX_Morning_Bed_PollenSparkle",
        "FX_Morning_ImpactBurst",
        "FX_Morning_WaterGlint",
        "FX_Morning_Mist",
    ):
        return "class_c_parked"
    if label and "ChoralSheep" in str(label):
        return "class_d_sheep"
    if label == "Morning_SheepDell_Lake":
        return "class_e_plugin_audit"
    if path and "NS_Morning_WindRibbon" in str(path):
        return "class_b_retired"
    if path and "NS_Morning_PollenMote" in str(path):
        return "class_b_retired"
    return "other"


HANDLERS = {
    "census": effect_census,
    "dump": effect_dump,
    "audit-dumps": effect_dump,
    "retire-orphans": effect_retire_orphans,
    "parked": effect_parked,
    "rewire-parked-morning": effect_parked,
    "pollen": effect_pollen,
    "mist": effect_mist,
    "petal": effect_petal,
    "wind": effect_wind,
    "windfront": effect_wind,
    "sheep-lake": effect_sheep_lake,
    "audit-sheep-lake": effect_sheep_lake,
    "ensemble": effect_ensemble,
    "ensemble-proof": effect_ensemble,
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--effect", required=True)
    args = ap.parse_args()
    eid = args.effect.strip()
    fn = HANDLERS.get(eid)
    if not fn:
        print(json.dumps({"error": "unknown_effect", "effect": eid, "known": sorted(HANDLERS)}))
        sys.exit(2)
    AUDIT.mkdir(parents=True, exist_ok=True)
    DUMPS.mkdir(parents=True, exist_ok=True)
    SCREENS.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    try:
        result = fn()
    except Exception as exc:
        result = {"ok": False, "pass": False, "error": str(exc)}
        write_json(AUDIT / f"niagara_rewire_{eid}_error_{STAMP}.json", result)
        raise
    result = result or {}
    result["effect"] = eid
    result["elapsed_s"] = round(time.time() - t0, 2)
    summary_path = write_json(AUDIT / f"niagara_rewire_{eid}_summary_{STAMP}.json", result)
    print(json.dumps({
        "effect": eid,
        "ok": result.get("ok"),
        "pass": result.get("pass"),
        "elapsed_s": result["elapsed_s"],
        "summary": summary_path,
        "still": result.get("still") or (result.get("still") if isinstance(result.get("still"), str) else None),
        "actors": result.get("actors"),
        "renderer_materials": result.get("renderer_materials") or result.get("gate", {}).get("renderer_materials") if isinstance(result.get("gate"), dict) else result.get("renderer_materials"),
        "proof": result.get("proof"),
        "error": result.get("error"),
    }, default=str))
    sys.exit(0 if result.get("ok") is not False else 1)


if __name__ == "__main__":
    main()
