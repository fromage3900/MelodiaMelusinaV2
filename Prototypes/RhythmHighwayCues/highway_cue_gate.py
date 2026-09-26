"""HL1-HL5 gate: drive a rhythm battle in PIE and read the HUD widget's cue state.

Evidence for the 2026-09-26 rhythm-highway goal. Why this shape:

  * The widget's new cue state is a BlueprintReadOnly UPROPERTY set, so "the cues
    fire" is asserted from live object state, not from frames (a Slate overlay in a
    PNG cannot show a 117 ms overshoot curve).
  * A run_python call cannot sleep through a chart -- python runs on the game
    thread, so sleeping freezes the PIE world. Samples are separate quick calls
    interleaved by this orchestrator, as the project's PIE-evidence skill prescribes.
  * The battle is started the way the game starts it: the authored
    `melodia:battle:<EncounterId>` notification through the narrative subsystem,
    with the bridge entry point (HandleNarrativeBattleRequested) as the documented
    fallback. The tagged battle actor is matched by the bridge; this script never
    spawns one.
  * register_lane_hit is the documented direct-input fallback: a green run proves
    the cues respond to the native seam, NOT that a player pressing keys sees them.
    The owner's eye is the beauty gate; frames are captured mid-chart for it.

Run:  uv run --no-sync python Prototypes/RhythmHighwayCues/highway_cue_gate.py [--map PATH]
Receipt: Saved/Audit/rhythm_highway_20260926/highway_cue_gate.json
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.request
from pathlib import Path

MCP = "http://127.0.0.1:9316/mcp"
ROOT = Path(r"C:\EnvironmentPortfolio\BS_GodFile")
OUT = ROOT / "Saved" / "Audit" / "rhythm_highway_20260926"
FRAMES = OUT / "frames"
DEFAULT_MAP = "/Game/EnvSandbox/Environments/L_KaleidoNave"
ENCOUNTER = "melodia_smoke_encounter"
SKILL_CLASS_PATH = "/Game/Experiments/MelodiaJRPG/Skills/BP_MelusinaPetalCadence.BP_MelusinaPetalCadence_C"
DURATION = 90
CAPTURE_INTERVAL = 2.0


def monolith(tool: str, args: dict, timeout: int = 120):
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                       "params": {"name": tool, "arguments": args}}).encode()
    req = urllib.request.Request(MCP, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode())
    result = data.get("result", {})
    if result.get("isError"):
        text = result.get("content", [{}])[0].get("text", "")
        raise RuntimeError(f"monolith {tool} error: {text[:400]}")
    content = result.get("content", [{}])
    text = content[0].get("text", "") if content else ""
    if not text:
        return {}
    try:
        return json.loads(text)
    except Exception:
        return {"raw": text}


def editor(action: str, **kwargs):
    return monolith("editor_query", {"action": action, **kwargs})


def run_python(code: str):
    return editor("run_python", command=code)


def out_lines(resp) -> list[str]:
    """run_python answers with [{type, output}, ...]; flatten to plain text lines."""
    if isinstance(resp, dict):
        out = resp.get("output")
        if isinstance(out, list):
            return [str(x.get("output", "")) if isinstance(x, dict) else str(x) for x in out]
    return str(resp).splitlines()


def pick(lines: list[str], marker: str):
    for line in lines:
        if marker in line:
            payload = line[line.index(marker) + len(marker):].strip()
            try:
                return json.loads(payload)
            except Exception:
                return payload
    return None


# --- in-editor snippets -------------------------------------------------------

PROBE = """
import unreal, json
gw = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
rep = {'world': bool(gw)}
if gw:
    sub = unreal.MelodiaRhythmCombatSubsystem.get(gw)
    hud = unreal.MelodiaRhythmHUDWidget.find_first(gw)
    rep['session_active'] = bool(sub.is_session_active()) if sub else None
    rep['session_id'] = sub.get_active_session_id() if sub else None
    rep['hud'] = hud.get_name() if hud else None
    battle_actors = []
    for a in unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.Actor):
        cls = a.get_class().get_name()
        low = cls.lower()
        if any(k in low for k in ('battle', 'boss', 'enemy', 'swordsman', 'encounter')):
            tags = []
            try:
                tags = [str(t) for t in a.get_actor_tags()]
            except Exception:
                pass
            props = {}
            for p in ('offLevelBattleData', 'enemyList'):
                try:
                    props[p] = 'set' if a.get_editor_property(p) is not None else 'null'
                except Exception:
                    props[p] = 'missing'
            battle_actors.append('%s [%s] tags=%s %s' % (a.get_actor_label(), cls, tags, props))
    rep['battle_actors'] = battle_actors[:12]
print('BD ' + json.dumps(rep))
"""

START_BATTLE = """
import unreal, json
gw = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
enc = '__ENCOUNTER__'
steps = []
actors = unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.Actor)

# a) the authored in-level path: the encounter trigger the player would overlap.
triggers = [a for a in actors if 'MelodiaEncounterTrigger' in a.get_class().get_name()]
steps.append('triggers=%d' % len(triggers))
for t in triggers:
    try:
        fired = t.start_encounter_for_player()
        steps.append('start_encounter_for_player=%s label=%s' % (fired, t.get_actor_label()))
        break
    except Exception as exc:
        steps.append('trigger_err=%s' % str(exc)[:90])

# b) the production owner, driven directly: StartTaggedJRPGBattle matches an actor whose
#    TAG equals the encounter id (bridge source: ActorHasTag(EncounterId)), then runs that
#    actor's StartBattle with the actor's own offLevelBattleData + enemyList. The tag is
#    added to the actor that already carries the full stock contract -- the documented
#    wiring step from Content/Python/tag_kaleido_encounter.py, PIE-scoped and never saved.
contract = [a for a in actors if 'InteractionBattle' in a.get_class().get_name()]
steps.append('contract_actors=%d' % len(contract))
gi = unreal.GameplayStatics.get_game_instance(gw)
bridge = unreal.MelodiaExternalJRPGBridgeSubsystem.get_game_instance_subsystem(gi)
if bridge and contract:
    a = contract[0]
    try:
        tags = list(a.get_editor_property('tags'))
        if unreal.Name(enc) not in tags:
            tags.append(unreal.Name(enc))
            a.set_editor_property('tags', tags)
        steps.append('tags_now=%s' % [str(t) for t in a.get_editor_property('tags')])
    except Exception as exc:
        steps.append('tag_err=%s' % str(exc)[:90])
    try:
        started = bridge.call_method('StartTaggedJRPGBattle', (unreal.Name(enc),))
        steps.append('start_tagged=%s active=%s' % (started, bridge.get_active_encounter_id()))
    except Exception as exc:
        steps.append('start_tagged_err=%s' % str(exc)[:90])
elif not bridge:
    steps.append('no_bridge')
print('START ' + json.dumps(steps))
"""

DRIVE_SKILL = """
import unreal, json
gw = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
def by(frag):
    return [a for a in unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.Actor)
            if frag in a.get_class().get_name()]
sub = unreal.MelodiaRhythmCombatSubsystem.get(gw)
ctrl = by('BP_BattleController_C')
enemies = by('BP_BossEnemy_C') or by('Enemy') or by('Boss')
state = {}
if ctrl:
    for p in ('currentTurn', 'currentAttackingUnit', 'currentSkill', 'isBattleOver'):
        try:
            state[p] = str(ctrl[0].get_editor_property(p))
        except Exception:
            state[p] = 'unreadable'
rep = 'state=%s' % json.dumps(state)

if sub and sub.is_session_active():
    print('DRIVE_SKILL already_active ' + rep)
elif not ctrl or not enemies:
    print('DRIVE_SKILL blocked ctrl=%d enemies=%d %s' % (len(ctrl), len(enemies), rep))
else:
    # The stock seam only accepts a skill on the player's turn; driving earlier is a
    # silent no-op, which is why this reports state instead of claiming success.
    attacker = state.get('currentAttackingUnit', '')
    is_player_unit = any(k in attacker for k in ('PlayerUnit', 'Melusina', 'Presentation'))
    if not is_player_unit:
        print('DRIVE_SKILL waiting_player_turn ' + rep)
    else:
        c = ctrl[0]
        cls = unreal.load_class(None, '__SKILL_CLASS__')
        sent = []
        try:
            c.call_method('OnSkillSelectedHandler', (cls,))
            sent.append('select')
        except Exception as exc:
            sent.append('select_err=%s' % str(exc)[:40])
        try:
            c.call_method('UseSkill', (enemies[0],))
            sent.append('use')
        except Exception as exc:
            sent.append('use_err=%s' % str(exc)[:40])
        spawned = ''
        try:
            spawned = str(c.get_editor_property('currentSkill'))
        except Exception:
            pass
        print('DRIVE_SKILL sent %s spawned_skill=%s %s' % (sent, spawned, rep))
""".replace("__SKILL_CLASS__", SKILL_CLASS_PATH)

SAMPLE = """
import unreal, json
gw = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
out = {'world': bool(gw)}
if gw:
    hud = unreal.MelodiaRhythmHUDWidget.find_first(gw)
    sub = unreal.MelodiaRhythmCombatSubsystem.get(gw)
    clock = unreal.MelodiaMusicClockSubsystem.get(gw)
    if sub:
        out['session_active'] = bool(sub.is_session_active())
        out['session_id'] = sub.get_active_session_id()
        out['hits'] = sub.get_session_hit_count()
        out['misses'] = sub.get_session_miss_count()
    if clock:
        mt = clock.get_music_time()
        out['bpm'] = round(mt.tempo_bpm, 3)
        out['clock_beats'] = round(mt.total_beats, 3)
        out['clock_valid'] = bool(mt.valid)
    if hud:
        out['hud'] = hud.get_name()
        out['hud_active'] = bool(getattr(hud, 'note_highway_active', False))
        out['hud_mode'] = str(hud.get_editor_property('active_hud_mode'))
        out['notes'] = len(getattr(hud, 'highway_notes', []))
        out['prev_notes'] = len(getattr(hud, 'previous_highway_notes', []))
        out['bursts'] = int(getattr(hud, 'total_hit_bursts', 0)) or len(getattr(hud, 'highway_bursts', []))  # cumulative: rings live 234 ms
        out['resolved'] = len(getattr(hud, 'resolved_notes', []))
        out['resolved_misses'] = len([r for r in getattr(hud, 'resolved_notes', [])
                                      if not getattr(r, 'counts_as_hit', False)])
        out['beat_pos'] = round(getattr(hud, 'highway_beat_position', -1.0), 4)
        out['sec_per_beat'] = round(getattr(hud, 'seconds_per_beat', -1.0), 5)
        out['pop_time'] = round(getattr(hud, 'last_grade_pop_time', -1000.0), 3)
        out['pop_grade'] = str(getattr(hud, 'last_pop_grade', ''))
        out['judgment'] = str(getattr(hud, 'last_judgment_text', ''))
        lf = getattr(hud, 'lane_flash_times', None)
        if lf is not None:
            out['lane_flash'] = [round(v, 3) for v in lf]
print('HL_SAMPLE ' + json.dumps(out))
"""

PRESS = """
import unreal
gw = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
sub = unreal.MelodiaRhythmCombatSubsystem.get(gw) if gw else None
if sub and sub.is_session_active():
    grades = []
    for lane in (0, 1):
        try:
            grades.append(str(sub.register_lane_hit(lane)))
        except Exception as exc:
            grades.append('err:%s' % str(exc)[:40])
    print('HL_PRESS grades=%s hits=%s misses=%s' % (grades, sub.get_session_hit_count(), sub.get_session_miss_count()))
else:
    print('HL_PRESS skipped active=%s' % (sub.is_session_active() if sub else None))
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--map", default=DEFAULT_MAP)
    ap.add_argument("--duration", type=int, default=DURATION)
    args = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    FRAMES.mkdir(parents=True, exist_ok=True)
    report: dict = {"schema": "melodia.rhythm_highway_cue_gate/1", "map": args.map,
                    "encounter": ENCOUNTER, "started": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "samples": [], "log": []}

    started = editor("capture_pie_movement_clip", map=args.map, duration=args.duration,
                     capture_interval=CAPTURE_INTERVAL, output_path=str(FRAMES),
                     discard_first_frames=3, sample_vars=[])
    sid = started.get("session_id")
    report["session_id"] = sid
    print(f"[gate] PIE {sid} on {args.map}")
    if not sid:
        report["fatal"] = f"capture_pie_movement_clip -> {started}"
        (OUT / "highway_cue_gate.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        return 1

    time.sleep(14)  # PIE boot + map load (host-side wait; editor python must never sleep)

    probe = pick(out_lines(run_python(PROBE)), "BD ")
    report["log"].append({"t": "probe", "data": probe})
    print("[gate] probe:", json.dumps(probe)[:500])

    if not (probe or {}).get("session_active"):
        start = pick(out_lines(run_python(START_BATTLE.replace("__ENCOUNTER__", ENCOUNTER))), "START ")
        report["log"].append({"t": "start_battle", "data": start})
        print("[gate] start:", json.dumps(start)[:400])
        time.sleep(8)
        probe2 = pick(out_lines(run_python(PROBE)), "BD ")
        report["log"].append({"t": "probe_after_start", "data": probe2})
        print("[gate] after start:", json.dumps(probe2)[:500])

    # Wait for the battle to reach the player's turn, then drive the skill. Driving
    # before the turn is a silent no-op, so success is "sent" (after the turn check),
    # never "the call did not raise".
    for attempt in range(10):
        drive = pick(out_lines(run_python(DRIVE_SKILL)), "DRIVE_SKILL ")
        report["log"].append({"t": f"drive_skill_{attempt}", "data": drive})
        print(f"[gate] drive {attempt}:", drive)
        if isinstance(drive, str) and ("sent" in drive or "already_active" in drive):
            break
        time.sleep(4)

    # The chart is short (a handful of notes) and the FX windows are ~1/4 beat, so this
    # samples tightly right after the drive, pressing lanes whenever the session is live
    # -- a press outside the active window is a no-op and proves nothing.
    deadline = time.time() + 34
    n = 0
    pressed = 0
    while time.time() < deadline:
        if n < 14:
            sample = pick(out_lines(run_python(SAMPLE)), "HL_SAMPLE ")
            if isinstance(sample, dict):
                sample["n"] = n
                report["samples"].append(sample)
                print(f"[gate] {n}: active={sample.get('session_active')} hud={sample.get('hud')} "
                      f"notes={sample.get('notes')} bursts={sample.get('bursts')} "
                      f"resolved={sample.get('resolved')} spb={sample.get('sec_per_beat')} "
                      f"bpm={sample.get('bpm')} judgment={sample.get('judgment')}")
                if sample.get("session_active") and pressed < 10:
                    press = pick(out_lines(run_python(PRESS)), "HL_PRESS ")
                    report["log"].append({"t": f"press_{n}", "data": press})
                    print("[gate] press:", press)
                    pressed += 1
                elif not sample.get("session_active") and n % 3 == 2 and n < 9:
                    again = pick(out_lines(run_python(DRIVE_SKILL)), "DRIVE_SKILL ")
                    report["log"].append({"t": f"redrive_{n}", "data": again})
                    print("[gate] redrive:", again)
            time.sleep(0.4)
        else:
            time.sleep(1.5)
        n += 1

    final = editor("poll_pie_smoke", session_id=sid)
    report["pie_report"] = {k: final.get(k) for k in
                            ("status", "duration", "frames_captured", "errors", "warnings",
                             "sample_count", "elapsed_seconds")}
    print("[gate] pie:", json.dumps(report["pie_report"])[:300])

    # The ring and lane flash live 1/8 note, shorter than any remote poll, so the receipt
    # takes its counts from the cue log the widget writes where the moment happens.
    live_logs = sorted((ROOT / "Saved" / "Logs").glob("BS_GodFile_*.log"),
                       key=lambda p: p.stat().st_mtime, reverse=True)
    cues = {"bursts": 0, "misses": 0, "burst_lines": []}
    if live_logs:
        text = live_logs[0].read_text(errors="ignore")
        for line in text.splitlines():
            if "HL_CUE burst" in line:
                cues["bursts"] += 1
                cues["burst_lines"].append(line.split("LogTemp:")[-1].strip())
            elif "HL_CUE miss" in line:
                cues["misses"] += 1
        cues["log"] = str(live_logs[0])
    report["cue_log"] = cues
    print(f"[gate] cue log: bursts={cues['bursts']} misses={cues['misses']}")

    s = [x for x in report["samples"] if isinstance(x, dict)]
    active = any(x.get("session_active") for x in s)
    hud_active = any(x.get("hud_active") for x in s)
    notes = max([x.get("notes", 0) for x in s] or [0])
    bursts = max([x.get("bursts", 0) for x in s] or [0])
    resolved = max([x.get("resolved", 0) for x in s] or [0])
    pops = {x.get("pop_time") for x in s
            if isinstance(x.get("pop_time"), float) and x["pop_time"] > -999}
    bpm = next((x.get("bpm") for x in s if x.get("bpm")), None)
    spb = next((x.get("sec_per_beat") for x in s if x.get("sec_per_beat", -1) > 0), None)
    report["assertions"] = {
        "session_active_seen": active,
        "hud_highway_active_seen": hud_active,
        "chart_notes_seen": notes,
        "hit_bursts_seen": bursts,                              # HL2
        "resolution_records_seen": resolved,                    # HL2/HL3 bookkeeping
        "grade_pop_distinct_times": len(pops),                  # HL1
        "beat_position_advanced": len({x.get("beat_pos") for x in s}) > 1,
        "clock_bpm": bpm,
        "widget_sec_per_beat": spb,
        "beat_lock_ratio": (round(spb / (60.0 / bpm), 3) if (spb and bpm) else None),
        "pie_errors": report["pie_report"].get("errors"),
    }
    verdict = bool(active and hud_active and notes > 0 and (bursts > 0 or resolved > 0))
    report["verdict"] = "PASS" if verdict else "PARTIAL"
    report["finished"] = time.strftime("%Y-%m-%d %H:%M:%S")
    (OUT / "highway_cue_gate.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"[gate] verdict={report['verdict']} -> {OUT / 'highway_cue_gate.json'}")
    print(json.dumps(report["assertions"], indent=2))
    return 0 if verdict else 2


if __name__ == "__main__":
    sys.exit(main())
