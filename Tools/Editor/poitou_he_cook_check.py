#!/usr/bin/env python
"""Headless cook check for the Poitou level's Houdini actors.

Run headlessly (no editor GUI, no GPU):

    UnrealEditor-Cmd.exe BS_GodFile.uproject -run=pythonscript \
        -script=".../poitou_he_cook_check.py" -unattended -nopause -nosplash \
        -nullrhi -stdout -FullStdOutLogOutput

Why this exists
---------------
The in-theme gate (Tools/Poitou/poitou_intheme_gate.py) proves the HDA is
healthy: it cooks the HDA in Houdini and asserts what comes out.  It says
NOTHING about whether the LEVEL is fed, because that is the Houdini Engine
plugin's job and it lives on the UE side.

That gap is exactly where a silent regression hides.  On 2026-10-21 the
level's `Poitou_Layout_v6` actor was cooking a stale embedded HDA
(`poitou_layout_roomshell_candidate`) and that cook was finishing "with
errors" - so the actor produced nothing and the level read empty - while
the Houdini-side gate stayed green the whole time.

This script closes the gap.  Loading the map makes the Houdini Engine
plugin cook every Houdini actor in it, and the plugin logs the result:

    Poitou_Layout_v6 FinishedCooking.                    <- good
    Poitou_Layout_v6 FinishedCooking with errors - ...   <- broken

So: load the map, let the cooks run, then read the log back.  The result
is written to Saved/Audit/PoitouConvergence_20261020/he_cook_check.json
and the process exits non-zero if any Houdini actor cooked with errors.

This is the check that would have caught the empty level before it was
found by eye.
"""
from __future__ import annotations

import json
import os
import re
import time

import unreal

REPO = os.environ.get("MELODIA_POITOU_REPO", r"C:\EnvironmentPortfolio\BS_GodFile")
OUT_DIR = os.path.join(REPO, "Saved", "Audit", "PoitouConvergence_20261020")
RESULT = os.path.join(OUT_DIR, "he_cook_check.json")
MAP = os.environ.get("MELODIA_POITOU_MAP", "/Game/EnvSandbox/Poitou/L_Poitou_v2")
LOG = os.path.join(REPO, "Saved", "Logs", "BS_GodFile.log")

res = {"map": MAP, "started": time.strftime("%H:%M:%S"), "actors": [], "ok": False}

try:
    unreal.EditorLoadingAndSavingUtils.load_map(MAP)
    # let the plugin's async cooks land (a plain sleep: the cook runs on
    # HAPI's own thread and only the log needs to catch up)
    import time as _t
    _t.sleep(8.0)
    asub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actors = list(asub.get_all_level_actors())
    res["actor_count"] = len(actors)
    houdini = [a for a in actors if "Houdini" in a.get_class().get_name()]
    res["houdini_actor_count"] = len(houdini)
    res["houdini_actors"] = [a.get_actor_label() for a in houdini]
except Exception as e:
    res["error"] = str(e)

# ---- read the cooks back out of the log ------------------------------
# UE rotates Saved/Logs/BS_GodFile.log every time a second Unreal process
# starts, so the owner's live editor log can be BS_GodFile.log OR
# BS_GodFile_2.log depending on whether a commandlet ran in between.
# Scan every log in the folder and keep the NEWEST cook line per actor.
cooks = []
LOG_DIR = os.path.join(REPO, "Saved", "Logs")
if os.path.isdir(LOG_DIR):
    logs = []
    for fn in os.listdir(LOG_DIR):
        if fn.endswith(".log"):
            fp = os.path.join(LOG_DIR, fn)
            try:
                logs.append((os.path.getmtime(fp), fp))
            except OSError:
                pass
    logs.sort()
    for _mt, fp in logs:
        try:
            text = open(fp, "r", encoding="utf-8", errors="replace").read()
        except Exception:
            continue
        for m in re.finditer(
                r"(\d{4}\.\d{2}\.\d{2}-\d{2}\.\d{2}\.\d{2}:\d+).*?LogHoudiniEngine:\s+(.*)", text):
            line = m.group(2).strip()
            for a in re.findall(r"([A-Za-z0-9_]+) FinishedCooking(.*)", line):
                cooks.append({"actor": a[0], "tail": a[1].strip(),
                              "stamp": m.group(1), "log": os.path.basename(fp)})
    res["logs_scanned"] = [os.path.basename(f) for _m, f in logs]
# keep the newest entry per actor
newest = {}
for c in cooks:
    k = c["actor"]
    if k not in newest or c["stamp"] >= newest[k]["stamp"]:
        newest[k] = c
cooks = list(newest.values())
res["cooks"] = cooks
by_actor = {}
for c in cooks:
    by_actor.setdefault(c["actor"], []).append(c["tail"])
res["cook_result"] = {k: ("ERROR" if any("with errors" in t for t in v) else "OK") for k, v in by_actor.items()}
broken = [k for k, v in res["cook_result"].items() if v == "ERROR"]
res["broken_actors"] = broken
res["ok"] = (not broken) and (len(by_actor) > 0)

os.makedirs(OUT_DIR, exist_ok=True)
with open(RESULT, "w", encoding="utf-8") as fh:
    json.dump(res, fh, indent=1, default=str)
unreal.log("[he_cook] actors=%s" % res.get("houdini_actors"))
unreal.log("[he_cook] cook_result=%s" % json.dumps(res["cook_result"]))
unreal.log("[he_cook] broken=%s" % broken)
unreal.log("[he_cook] wrote %s" % RESULT)
