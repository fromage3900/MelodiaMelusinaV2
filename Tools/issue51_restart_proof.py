"""Issue #51 restart proof: durable-vector capture before a real process restart, compare after.

The restart itself is real and happens between the two phases (quit the editor, relaunch it,
load through the canonical Continue path). This script never fakes it.

    python Tools/issue51_restart_proof.py capture [--save] [--out DIR]
        PIE must be running. --save calls SaveToSlot on the first live BP_SavePoint first.
        Writes DIR/before.json.
    python Tools/issue51_restart_proof.py verify [--out DIR]
        After the relaunch + Continue load, PIE running. Writes DIR/after.json and
        DIR/restart_proof.json; exit 0 only when every durable field matches and no
        consumed reward/intent id is duplicated.

Durable vector = every UPROPERTY of FMelodiaNarrativeRecord (flags, Quill variables + persistent
blob hash, checkpoint, encounter ids/outcome, consumed intents/rewards, quests, social stats, bonds,
phase, spawn context, wardrobe owned/equipped, pull time, the record's water copy) plus the LIVE
UMelodiaWaterGameplaySubsystem state (PuzzleRevision, CompletedPuzzleIds, nodes, routes, platforms).
Sets and maps are sorted so hash order after load does not read as a difference.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import sys
import urllib.request

MCP = "http://127.0.0.1:9316/mcp"
ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "Saved" / "Audit" / f"issue51_restart_{dt.date.today():%Y%m%d}"
MARK = "R51_VECTOR "

SNIPPET = r'''
import unreal, json, hashlib
out = {"errors": []}
gw = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
if not gw:
    out["errors"].append("no PIE game world")
else:
    if __DO_SAVE__:
        sp = [a for a in unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.Actor)
              if "SavePoint" in a.get_class().get_name()]
        if sp:
            try:
                sp[0].call_method("SaveToSlot")
                out["saved_via"] = sp[0].get_name()
            except Exception as exc:
                out["errors"].append("SaveToSlot: %s" % exc)
        else:
            out["errors"].append("no BP_SavePoint in world")

    def norm(v):
        if v is None or isinstance(v, (bool, int, float, str)):
            return v
        if isinstance(v, (unreal.Name, unreal.Text)):
            return str(v)
        if isinstance(v, unreal.EnumBase):
            return str(v.name)
        if isinstance(v, unreal.GameplayTag):
            return str(v.tag_name)
        if isinstance(v, unreal.Map):
            return sorted([[json.dumps(norm(k)), norm(x)] for k, x in v.items()])
        if isinstance(v, (unreal.Array, unreal.Set, list, tuple, set)):
            items = [norm(x) for x in v]
            return sorted(items, key=lambda x: json.dumps(x, sort_keys=True)) if isinstance(v, (unreal.Set, set)) else items
        if isinstance(v, unreal.StructBase):
            return {"__text__": v.export_text()}
        return str(v)

    RECORD_FIELDS = ["version", "flags", "quill_variables", "script_checkpoint", "last_encounter_id",
        "last_encounter_command_id", "last_encounter_outcome", "consumed_intent_ids", "active_quest_ids",
        "completed_quest_ids", "consumed_reward_ids", "social_stats", "bond_ranks", "phase_index",
        "spawn_context", "owned_cosmetic_ids", "equipped_cosmetic_ids", "last_pull_unix_seconds"]
    WATER_FIELDS = ["schema_version", "completed_puzzle_ids", "puzzle_revision", "node_states",
        "route_states", "platform_states"]

    def fields(struct, names):
        d = {}
        for n in names:
            try:
                d[n] = norm(struct.get_editor_property(n))
            except Exception as exc:
                out["errors"].append("%s: %s" % (n, exc))
        return d

    gi = unreal.GameplayStatics.get_game_instance(gw)
    narr = unreal.MelodiaNarrativeSubsystem.get_melodia_narrative_subsystem(gw)
    if narr:
        rec = narr.get_narrative_record()
        out["record"] = fields(rec, RECORD_FIELDS)
        blob = bytes(rec.get_editor_property("quill_persistent_data"))
        out["record"]["quill_persistent_data_sha1"] = hashlib.sha1(blob).hexdigest()
        out["record"]["quill_persistent_data_len"] = len(blob)
        out["record"]["water_gameplay_state"] = fields(rec.get_editor_property("water_gameplay_state"), WATER_FIELDS)
    else:
        out["errors"].append("no UMelodiaNarrativeSubsystem")
    water = unreal.MelodiaWaterGameplaySubsystem.get(gw)
    if water:
        live = unreal.MelodiaWaterGameplaySaveData()
        res = water.capture_save_state(live)
        live = res if isinstance(res, unreal.MelodiaWaterGameplaySaveData) else live
        out["live_water"] = fields(live, WATER_FIELDS)
    else:
        out["errors"].append("no UMelodiaWaterGameplaySubsystem")
    out["map"] = gw.get_map_name() if hasattr(gw, "get_map_name") else gw.get_name()
print("__MARK__" + json.dumps(out, sort_keys=True))
'''


def monolith(tool: str, args: dict, timeout: int = 120) -> dict:
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                       "params": {"name": tool, "arguments": args}}).encode()
    req = urllib.request.Request(MCP, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        result = json.loads(resp.read().decode()).get("result", {})
    text = (result.get("content") or [{}])[0].get("text", "")
    if result.get("isError"):
        raise RuntimeError(f"monolith {tool}: {text[:400]}")
    try:
        return json.loads(text) if text else {}
    except Exception:
        return {"raw": text}


def capture_vector(do_save: bool) -> dict:
    code = SNIPPET.replace("__DO_SAVE__", "True" if do_save else "False").replace("__MARK__", MARK)
    resp = monolith("editor_query", {"action": "run_python", "command": code})
    lines = resp.get("output") if isinstance(resp, dict) else None
    lines = [str(x.get("output", "")) if isinstance(x, dict) else str(x) for x in lines] if isinstance(lines, list) \
        else str(resp).splitlines()
    for line in lines:
        if MARK in line:
            return json.loads(line[line.index(MARK) + len(MARK):])
    raise RuntimeError(f"no vector in run_python output: {str(resp.get('message', resp))[:900]}")


def save_file_facts() -> dict:
    sav = ROOT / "Saved" / "SaveGames" / "MelodiaJRPGSlot0.sav"
    if not sav.exists():
        return {"path": str(sav), "exists": False}
    st = sav.stat()
    return {"path": str(sav), "exists": True, "bytes": st.st_size,
            "mtime": dt.datetime.fromtimestamp(st.st_mtime).isoformat(timespec="seconds")}


def diff(a, b, path="") -> list[str]:
    if isinstance(a, dict) and isinstance(b, dict):
        out = []
        for k in sorted(set(a) | set(b)):
            out += diff(a.get(k, "<missing>"), b.get(k, "<missing>"), f"{path}.{k}" if path else k)
        return out
    return [] if a == b else [f"{path}: before={json.dumps(a)[:200]} after={json.dumps(b)[:200]}"]


def duplicates(record: dict) -> dict:
    dup = {}
    for key in ("consumed_intent_ids", "consumed_reward_ids", "completed_quest_ids"):
        ids = record.get(key) or []
        extra = len(ids) - len(set(map(str, ids)))
        if extra:
            dup[key] = extra
    return dup


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("phase", choices=["capture", "verify"])
    ap.add_argument("--save", action="store_true", help="capture: SaveToSlot on the first live BP_SavePoint first")
    ap.add_argument("--out", type=pathlib.Path, default=DEFAULT_OUT)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now().isoformat(timespec="seconds")

    vec = capture_vector(args.save and args.phase == "capture")
    vec["save_file"] = save_file_facts()
    vec["captured_at"] = stamp

    if args.phase == "capture":
        (args.out / "before.json").write_text(json.dumps(vec, indent=1, sort_keys=True))
        print(f"before.json written ({len(vec.get('errors', []))} errors) -> {args.out}")
        for e in vec.get("errors", []):
            print("  ERROR", e)
        return 1 if vec.get("errors") else 0

    before_path = args.out / "before.json"
    if not before_path.exists():
        print(f"missing {before_path}; run capture first")
        return 2
    before = json.loads(before_path.read_text())
    (args.out / "after.json").write_text(json.dumps(vec, indent=1, sort_keys=True))
    diffs = diff(before.get("record", {}), vec.get("record", {}), "record")
    diffs += diff(before.get("live_water", {}), vec.get("live_water", {}), "live_water")
    dups = duplicates(vec.get("record", {}))
    errors = before.get("errors", []) + vec.get("errors", [])
    ok = not diffs and not dups and not errors and bool(vec.get("record"))
    report = {"schema": "melodia.issue51.restart_proof.v1", "ok": ok, "before_at": before.get("captured_at"),
              "after_at": stamp, "save_file_before": before.get("save_file"), "save_file_after": vec["save_file"],
              "map_after": vec.get("map"), "field_diffs": diffs, "duplicate_ids": dups, "errors": errors,
              "note": "Only valid if the editor process was quit and relaunched between capture and verify."}
    (args.out / "restart_proof.json").write_text(json.dumps(report, indent=1))
    print(("PASS" if ok else "FAIL") + f" restart proof -> {args.out / 'restart_proof.json'}")
    for line in diffs + [f"duplicate {k}: {v}" for k, v in dups.items()] + errors:
        print("  ", line)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
