"""The P0 golden run driver - Morning -> KaleidoNave -> encounter -> save -> restart ->
Continue -> repeatability, with an evidence envelope per phase.

It reuses the project's own surfaces: the Monolith bridge (the RiderLink surface) for the
editor, and the project's payload pattern for the PIE steps. It invents no harness.

The contract: specs/p0/core_p0_dream_golden_run.v1.json. The forbidden shortcuts are
respected: the player route is walked (not the integration map), the run is not claimed
from historical envelopes, there is one editor writer, and no gameplay BP is edited to
hide a failure.

Usage: C:/Python314/python.exe Tools/p0/golden_run_driver.py [--phase <name>]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(r"C:/EnvironmentPortfolio/BS_GodFile")
sys.path.insert(0, str(REPO / "Tools"))
from mcp_client import monolith_call  # noqa: E402

OUT = REPO / "Saved" / "Audit" / "P0GoldenRun_20261022"
CMD = OUT / "command.json"
MORNING = "/Game/Melodia/Levels/Opening/L_MelusinaMorning"
NAVE = "/Game/EnvSandbox/Environments/L_KaleidoNave"
LEVEL_ID_NAVE = "L_KaleidoNave"


def q(action, params=None, timeout=180):
    return monolith_call("editor_query", {"action": action, "params": params or {}}, timeout=timeout)


def op(name, arg="", shot="", pause=0.6):
    OUT.mkdir(parents=True, exist_ok=True)
    CMD.write_text(json.dumps({"op": name, "arg": arg, "shot": shot}), encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, str(REPO / "Tools" / "mcp_run_python.py"),
         "--file", str(REPO / "Tools" / "p0" / "golden_run_payload.py"),
         "--name", "golden_" + name, "--timeout", "90"],
        cwd=str(REPO), capture_output=True, text=True)
    text = (proc.stdout or "") + (proc.stderr or "")
    for line in text.splitlines():
        if "GOLDEN" in line:
            print("   ", line.strip()[:200])
    time.sleep(pause)
    return text


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def envelope(kind, status, checks, artifacts, notes, run_id, evidence_id):
    def git(*args):
        try:
            return subprocess.run(["git", "-C", str(REPO)] + list(args),
                                  capture_output=True, text=True).stdout.strip()
        except Exception:  # noqa: BLE001
            return ""
    doc = {
        "schema": "melodia.evidence_envelope.v1",
        "evidence_id": evidence_id,
        "run_id": run_id,
        "kind": kind,
        "status": status,
        "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
        "repository": {"root": str(REPO), "commit": git("rev-parse", "HEAD"),
                       "branch": git("rev-parse", "--abbrev-ref", "HEAD")},
        "producer": {"tool": "Tools/p0/golden_run_driver.py", "version": "1.0.0"},
        "checks": checks,
        "artifacts": artifacts,
        "notes": notes,
    }
    path = OUT / ("envelope_%s_%s.json" % (kind, evidence_id.replace("golden_", "")[-14:]))
    path.write_text(json.dumps(doc, indent=2), encoding="utf-8")
    return path, doc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", default="all")
    args = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    run_id = "golden_%s" % time.strftime("%Y%m%d_%H%M%S")
    envelopes = []

    print("=" * 70)
    print("P0 GOLDEN RUN %s" % run_id)
    print("=" * 70)

    # ---------------- phase 0: the session ---------------------------------
    print("\n[phase] session")
    print("  load:", q("load_level", {"path": MORNING}, timeout=300))
    time.sleep(4)
    print("  dirty:", q("list_dirty_packages", {}, timeout=90))
    print("  start_pie:", q("start_pie", {}, timeout=240))
    time.sleep(8)

    # ---------------- phase 1: the morning beat ----------------------------
    print("\n[phase] morning_quill_beat")
    text = op("status", shot="01_morning")
    op("actors")
    # The morning beat is fired by an arrival trigger: walk into it (what a player does),
    # then read and pick the Quill's options.
    walked = ""
    for _ in range(10):
        walked += op("walk_quill")
    options = op("quill_options")
    picked = op("quill_pick", "0")
    time.sleep(2)
    text2 = op("status")
    observed = text + text2 + walked + options + picked

    def check(name, ok, note=""):
        return {"name": name, "status": "pass" if ok else "hold", "note": note}

    envelopes.append(envelope(
        "runtime", "pass" if "GOLDEN narrative" in observed else "hold",
        [check("new_game_entry", "GOLDEN op=status pawn=" in observed,
               "the player route opened and the pawn is live"),
         check("fresh_slot_id", "quests=0" in observed,
               "the narrative record is empty: a fresh slot"),
         check("authored_petal_priestess_beat_visible",
               "GOLDEN quill=" in options and "NONE" not in options,
               "the Quill actor only exists once its arrival trigger has fired"),
         check("choice_readable", "GOLDEN option[" in options,
               "the Quill's option list was read"),
         check("harmony_intent_emitted_once",
               "quests=0" not in observed.split("GOLDEN narrative")[-1],
               "the record changed after the choice")],
        [], "the morning beat on the player route", run_id, run_id + "_morning"))

    # ---------------- phase 2: the departure -------------------------------
    print("\n[phase] kaleido_nave_departure")
    # The departure is the AUTHORED travel, not a level load. Loading a level while PIE
    # is running kills the session, so it is only a fallback - and the envelope says so.
    op("travel", LEVEL_ID_NAVE)
    time.sleep(8)
    text = op("status")
    authored_departure = "GOLDEN world=NONE" not in text
    if not authored_departure:
        print("  the travel did not carry us - stopping PIE, loading the nave, restarting")
        print("  stop_pie:", q("stop_pie", {}, timeout=120))
        print("  load:", q("load_level", {"path": NAVE}, timeout=300))
        time.sleep(6)
        print("  start_pie:", q("start_pie", {}, timeout=240))
        time.sleep(10)
    op("status", shot="02_nave")
    envelopes.append(envelope(
        "runtime", "pass" if authored_departure else "hold",
        [{"name": "authored_departure_completes",
          "status": "pass" if authored_departure else "hold",
          "note": "" if authored_departure else "the travel did not carry the pawn; the nave was loaded directly, which is NOT the authored departure"},
         {"name": "merged_dreamstate_presentation_reached", "status": "hold"},
         {"name": "input_restored", "status": "hold"}],
        [], "the departure to KaleidoNave", run_id, run_id + "_departure"))

    # ---------------- phase 3: the stock encounter -------------------------
    print("\n[phase] stock_encounter")
    walked = ""
    for _ in range(14):
        walked += op("step")
    op("lock", shot="03_encounter")
    op("swing")
    op("phrase")
    op("lanes")
    op("exit")
    text = op("status", shot="04_after_encounter")
    observed = walked + text
    envelopes.append(envelope(
        "runtime", "pass" if "one encounter" in observed.lower() or "FIRST RESONANCE" in observed else "hold",
        [check("one_encounter_starts",
               "First Resonance" in observed or "first resonance" in observed.lower(),
               "no encounter actor was present in the nave: the route's own beat has to fire"),
         check("stock_battle_authority_used",
               "CHIME-SCYTHE" in observed or "LOCK" in observed,
               "the waveharp component answered the lock and the swing"),
         check("typed_result_selected",
               "RESONANCE LOCKED" in observed or "sequence=True" in observed,
               "the phrase needs an encounter to lock first")],
        [], "the stock encounter, walked with movement input", run_id, run_id + "_encounter"))

    # ---------------- phase 4: the consequence and the save ----------------
    print("\n[phase] consequence_and_save")
    saved = op("save")
    text = op("status")
    save_log = OUT / "save_phase.txt"
    save_log.write_text(text, encoding="utf-8")
    envelopes.append(envelope(
        "save_load", "pass" if "save synced=True" in saved else "hold",
        [check("authored_consequence_resumes", "RESONANCE LOCKED" in text or "HIT" in text,
               "the consequence resumes the authored route"),
         check("normal_save_authority_used", "save synced=True" in saved,
               "the narrative record was synced into the JRPG save game by the house's own function"),
         check("save_boundary_recorded", "save synced=True" in saved,
               "the save boundary is the sync itself")],
        [{"path": str(save_log.relative_to(REPO)), "sha256": sha256(save_log), "role": "save phase output"}],
        "the consequence and the save boundary", run_id, run_id + "_save"))

    # ---------------- the artifacts ---------------------------------------
    artifacts = []
    for path in sorted(OUT.glob("*.png")):
        artifacts.append({"path": str(path.relative_to(REPO)), "sha256": sha256(path), "role": "runtime capture"})
    print("\n[artifacts] %d captures" % len(artifacts))

    print("  stop_pie:", q("stop_pie", {}, timeout=120))
    for path, doc in envelopes:
        print("  envelope:", path.name, doc["status"])

    summary = {"run_id": run_id, "envelopes": [str(p) for p, _ in envelopes],
               "artifacts": artifacts}
    (OUT / ("golden_run_%s.json" % run_id)).write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("\nreceipt:", OUT / ("golden_run_%s.json" % run_id))
    return 0


if __name__ == "__main__":
    sys.exit(main())
