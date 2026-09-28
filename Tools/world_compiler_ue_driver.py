#!/usr/bin/env python3
"""Sequence the World Compiler UE lane through Monolith (one editor, :9316, single writer).

    python Tools/world_compiler_ue_driver.py Saved/WorldCompiler/morning_rainbow_bloom_3900 [--fx] [--reload] [--no-cleanup]

Required spatial preflight (agent, not a new framework): before any WC / PCG /
Monolith spatial edit, run ``scene_context_cycle.begin()`` in the already-open
editor; after the edit, ``scene_context_cycle.end()``. Tools:
``Content/Python/scene_context_snapshot.py`` and ``scene_context_cycle.py``.
Packets under ``Saved/Audit/SceneContext/`` are ephemeral evidence, not status.
One editor only — Monolith ``http://127.0.0.1:9316/mcp``. Do not start a second
editor or a second spatial AI.

Each step is a separate ``editor.run_python`` call so PCG generation, saves and
reloads land on real frame boundaries (no ``time.sleep`` inside the editor).
The driver:

    1. preflight            (abort unless the recipe's level is open)
    2. ensure row struct    (Monolith blueprint.create_user_defined_struct, once)
    3. cleanup              (tagged actors + known rainbow husks)
    4. materials            (7 band MIs, BaseTint only)
    5. table                (fill DT_<recipe>_Points from points.csv)
    6. volume + generate    (only if the owner-authored template graph exists)
    7. count                (poll until 'generated' and counts stable, max ~60 s)
    8. save
    9. --reload: Monolith mesh.load_level -> count again
    10. --fx: fx_materials, fx_place, fx_audit
    11. beauty (automatic when the bundle carries ue_lane.beauty_feed):
        render target + sender actor + Spout2 plugin reflected (frames proven
        by the TD lookdev_comp Spout In intake, never by this driver)

Writes Saved/Audit/world_compiler_<recipe>_proof_<date>.json with every step's
payload and the gate verdicts. Never touches PCG graph structure, MPCs or masters.
"""
from __future__ import annotations

from mcp_client import post_envelope

import argparse
import json
import sys
import time
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UE_SCRIPT = ROOT / "Content" / "Python" / "world_compiler_ue.py"
MONOLITH = "http://127.0.0.1:9316/mcp"
_rpc_id = [0]


def _rpc(method: str, params: dict, timeout: int = 180) -> dict:
    _rpc_id[0] += 1
    body = {"jsonrpc": "2.0", "id": _rpc_id[0], "method": method, "params": params}
    try:
        return post_envelope(body, timeout=timeout, raise_on_error=True)
    except json.JSONDecodeError:
        # Not parseable as the JSON-RPC envelope (this used to walk `data:`
        # SSE frames and fall back to the raw body text).
        return {"_raw": f"non-JSON response from {MONOLITH}"}


def call(tool: str, args: dict, timeout: int = 180):
    r = _rpc("tools/call", {"name": tool, "arguments": args}, timeout=timeout)
    res = r.get("result", r)
    for block in res.get("content") or []:
        if block.get("type") == "text":
            try:
                return json.loads(block["text"])
            except Exception:
                return {"text": block["text"], "isError": res.get("isError")}
    return res


def run_step(bundle_dir: Path, step: str, unattended: bool = True) -> dict:
    cmd = f"{UE_SCRIPT.as_posix()} {bundle_dir.as_posix()} {step}"
    res = call("editor_query", {"action": "run_python", "params": {"command": cmd, "mode": "execute_file", "unattended": unattended, "file_scope": "private"}})
    out = bundle_dir / "ue" / f"{step}.json"
    if not out.exists():
        return {"step": step, "error": "no step output written", "monolith": res}
    payload = json.loads(out.read_text(encoding="utf-8"))
    payload["monolith_success"] = res.get("success") if isinstance(res, dict) else None
    return payload


def ensure_struct(manifest: dict) -> dict:
    struct_path = manifest["ue_lane"].get("row_struct")
    spec = json.loads((ROOT / "specs" / "schemas" / "world_compiler_point_row.v1.json").read_text(encoding="utf-8"))
    # Monolith add_variable type strings: bare "Vector" silently falls back to bool; structs need the "struct:" prefix.
    type_map = {"int32": "int", "float": "float", "FName": "name", "FString": "string", "FVector": "struct:Vector", "FRotator": "struct:Rotator"}
    fields = [{"name": c["name"], "type": type_map[c["type"]]} for c in spec["columns"]]
    res = call("blueprint_query", {"action": "create_user_defined_struct", "params": {"save_path": struct_path, "fields": fields}})
    return {"struct": struct_path, "fields": [f["name"] for f in fields], "monolith": res}


def wire_mapping(scaffold: dict) -> dict:
    """Write the Load Data Table attribute-mapping selectors through Monolith reflection.

    UE Python cannot author FPCGAttributePropertyInputSelector values (protected members; the blueprint
    helpers mutate a by-value copy), so every mapping value stays '@Last' and PCG leaves all points at
    the origin. blueprint.set_property_at_path runs C++ ImportText on the exact map entry instead.
    """
    target = scaffold.get("load_settings_path")
    out = {"settings": target, "writes": [], "all_ok": False}
    if not target:
        out["error"] = "scaffold did not report load_settings_path"
        return out
    for m in scaffold.get("mapping_targets", []):
        res = call("blueprint_query", {"action": "set_property_at_path", "params": {
            "asset_path": target, "path": f"AttributeMapping[{m['column']}]", "value": m["import_text"],
            "strict": True, "save": False}})
        # live write returns {old_value, new_value}; dry_run returns {field_writes:[{current, proposed, ok}]}
        ok = isinstance(res, dict) and res.get("new_value") == m["import_text"] and not res.get("errors")
        out["writes"].append({"column": m["column"], "selector": m["selector"], "ok": ok,
                              "old_value": res.get("old_value") if isinstance(res, dict) else None,
                              "new_value": res.get("new_value") if isinstance(res, dict) else None,
                              "raw": None if ok else str(res)[:400]})
    out["all_ok"] = bool(out["writes"]) and all(w["ok"] for w in out["writes"])
    return out


def poll_count(bundle_dir: Path, max_seconds: int = 90) -> dict:
    last = None
    stable = 0
    started = time.time()
    history = []
    while time.time() - started < max_seconds:
        c = run_step(bundle_dir, "count")
        history.append({"t": round(time.time() - started, 1), "generated": c.get("generated"), "total": c.get("instances_total")})
        key = (c.get("generated"), c.get("instances_total"))
        if c.get("generated") and key == last:
            stable += 1
            if stable >= 2:
                c["poll_history"] = history
                return c
        else:
            stable = 0
        last = key
        time.sleep(2.0)  # driver-side wait; the editor itself never sleeps
    c = run_step(bundle_dir, "count")
    c["poll_history"] = history
    c["timed_out"] = True
    return c


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("bundle_dir", type=Path)
    parser.add_argument("--fx", action="store_true")
    parser.add_argument("--reload", action="store_true")
    parser.add_argument("--no-cleanup", action="store_true")
    parser.add_argument("--skip-struct", action="store_true")
    parser.add_argument("--skip-scaffold", action="store_true", help="do not (re)build the template graph or its attribute mapping")
    parser.add_argument("--lookdev", action="store_true", help="hide Houdini overlays, spawn recipe cameras, capture stills, bookmark DA")
    args = parser.parse_args()
    bundle_dir = args.bundle_dir if args.bundle_dir.is_absolute() else (ROOT / args.bundle_dir)
    manifest = json.loads((bundle_dir / "manifest.json").read_text(encoding="utf-8"))
    recipe_id = manifest["recipe_id"]

    proof: dict = {
        "schema": "melodia.world_compiler_proof.v1",
        "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
        "compile_id": manifest["compile_id"],
        "manifest_sha256_prefix": None,
        "bundle_dir": str(bundle_dir.relative_to(ROOT)).replace("\\", "/"),
        "steps": {},
        "gates": {},
        # Ground-aware placement context so the proof is honest about *where* the field could land.
        "terrain": manifest.get("terrain"),
        "field": {k: manifest.get("place", {}).get(k) for k in ("anchor_cm", "sector_deg", "ground_mask")},
    }
    status = call("monolith_status", {})
    proof["monolith"] = {k: status.get(k) for k in ("version", "port", "uptime") if isinstance(status, dict)}

    # Spatial edits (volume / generate / fx / lookdev) assume the agent already
    # ran scene_context_cycle.begin() on this same editor (127.0.0.1:9316).
    # This driver does not wrap a new spatial framework; end() after the run.
    pre = run_step(bundle_dir, "preflight")
    proof["steps"]["preflight"] = pre
    if not pre.get("ok_to_proceed"):
        proof["gates"]["preflight"] = "FAIL"
        return _finish(proof, recipe_id, 1)
    proof["gates"]["preflight"] = "PASS"

    if not args.skip_struct and not pre.get("row_struct_exists"):
        proof["steps"]["ensure_struct"] = ensure_struct(manifest)
    if not args.no_cleanup:
        proof["steps"]["cleanup"] = run_step(bundle_dir, "cleanup")
    proof["steps"]["materials"] = run_step(bundle_dir, "materials")
    mats = proof["steps"]["materials"]
    all_mis = list(mats.get("band_mis", [])) + list((mats.get("wind_lane") or {}).get("band_mis", []))
    proof["gates"]["band_mis"] = "PASS" if all_mis and all("error" not in r for r in all_mis) and "error" not in (mats.get("wind_lane") or {}) else "FAIL"
    proof["steps"]["table"] = run_step(bundle_dir, "table")
    if proof["steps"]["table"].get("struct_drift") and not args.skip_struct:
        # Column contract changed since the row struct was forged: drop DT + struct and rebuild from the spec.
        proof["steps"]["table_first_attempt"] = proof["steps"]["table"]
        proof["steps"]["reset_table"] = run_step(bundle_dir, "reset_table")
        proof["steps"]["ensure_struct"] = ensure_struct(manifest)
        proof["steps"]["table"] = run_step(bundle_dir, "table")
    proof["gates"]["data_table"] = "PASS" if proof["steps"]["table"].get("match") else ("BLOCKED" if proof["steps"]["table"].get("blocked") else "FAIL")

    if not args.skip_scaffold:
        scaffold = run_step(bundle_dir, "template_scaffold")
        proof["steps"]["template_scaffold"] = scaffold
        mapping = wire_mapping(scaffold)
        proof["steps"]["wire_mapping"] = mapping
        # save the graph after the reflection write so the selectors persist
        proof["steps"]["template_save"] = call("blueprint_query", {"action": "save_asset", "params": {"asset_path": manifest["ue_lane"]["pcg_template_graph"]}})
        proof["gates"]["pcg_template_graph"] = "PASS" if scaffold.get("edges_verified") and mapping.get("all_ok") else "FAIL"
        pre["template_graph_exists"] = True

    if pre.get("template_graph_exists"):
        proof["steps"]["volume"] = run_step(bundle_dir, "volume")
        proof["steps"]["generate"] = run_step(bundle_dir, "generate")
        count = poll_count(bundle_dir)
        proof["steps"]["count_after_generate"] = count
        proof["gates"]["spawner_counts"] = "PASS" if count.get("match") else ("FAIL" if count.get("generated") else "TIMEOUT")
        proof["steps"]["save"] = run_step(bundle_dir, "save")
        proof["gates"]["save"] = "PASS" if proof["steps"]["save"].get("level_saved") else "FAIL"
        if args.reload:
            lvl = manifest["place"]["level"]
            proof["steps"]["reload"] = call("mesh_query", {"action": "load_level", "params": {"level_path": lvl}}, timeout=300)
            time.sleep(3.0)
            recount = poll_count(bundle_dir, max_seconds=60)
            proof["steps"]["count_after_reload"] = recount
            proof["gates"]["reload_recount"] = "PASS" if recount.get("instances_total") == count.get("instances_total") and count.get("match") else "FAIL"
    else:
        proof["gates"]["pcg_template_graph"] = "BLOCKED_OWNER_WIRES_TEMPLATE"
        proof["gates"]["spawner_counts"] = "SKIPPED"
        proof["steps"]["save"] = run_step(bundle_dir, "save")

    if args.fx:
        proof["steps"]["fx_materials"] = run_step(bundle_dir, "fx_materials")
        proof["steps"]["fx_place"] = run_step(bundle_dir, "fx_place")
        proof["steps"]["fx_audit"] = run_step(bundle_dir, "fx_audit")
        audit = proof["steps"]["fx_audit"]
        placed = proof["steps"]["fx_place"].get("placed", [])
        proof["gates"]["fx"] = "PASS" if audit.get("all_exist") and placed and not proof["steps"]["fx_place"].get("blocked") else ("BLOCKED_HERO_PARENTS" if not audit.get("all_exist") else "FAIL")
        proof["steps"]["fx_save"] = run_step(bundle_dir, "save")

    if args.lookdev:
        proof["steps"]["lookdev_cameras"] = run_step(bundle_dir, "lookdev_cameras")
        proof["steps"]["lookdev_capture"] = run_step(bundle_dir, "lookdev_capture")
        proof["steps"]["ensure_euw"] = run_step(bundle_dir, "ensure_euw")
        shots = proof["steps"]["lookdev_capture"].get("shots") or []
        proof["gates"]["lookdev_stills"] = "PASS" if shots and all(s.get("bytes", 0) > 0 for s in shots) else "FAIL"
        proof["steps"]["lookdev_save"] = run_step(bundle_dir, "save")

    if manifest.get("ue_lane", {}).get("beauty_feed"):
        proof["steps"]["beauty"] = run_step(bundle_dir, "beauty")
        bstep = proof["steps"]["beauty"]
        if bstep.get("skipped") or bstep.get("error"):
            proof["gates"]["beauty_feed"] = "SKIPPED" if bstep.get("skipped") else "FAIL"
        else:
            proof["gates"]["beauty_feed"] = "PASS" if bstep.get("assets_ok") and bstep.get("plugin_loaded") else "FAIL"

    hard = [g for g in proof["gates"].values() if g in ("FAIL", "TIMEOUT")]
    return _finish(proof, recipe_id, 1 if hard else 0)


def _finish(proof: dict, recipe_id: str, code: int) -> int:
    proof["verdict"] = "FAIL" if code else ("PASS" if all(g == "PASS" for g in proof["gates"].values()) else "PARTIAL_BLOCKED")
    out = ROOT / "Saved" / "Audit" / f"world_compiler_{recipe_id}_proof_{date.today().isoformat()}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(proof, indent=2, default=str), encoding="utf-8")
    print(json.dumps({"verdict": proof["verdict"], "gates": proof["gates"], "proof": str(out)}, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
