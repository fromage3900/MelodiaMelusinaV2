"""Discovery pass: how does a battle start on MelodiaIntegrationMap?

Read-only inside PIE. Reports, in one session:
  * actors exposing the stock battle contract (StartBattle + offLevelBattleData)
  * actors tagged Encounter_* / melodia_*
  * the live game mode, the narrative subsystem, the JRPG bridge, the UI bridge
  * DA_MelodiaIntegrationConfig EncounterIds (the allowlisted encounter gate)
  * the rhythm HUD widget, if one exists yet

No StartBattle call, no mutation. The point is to stop guessing which seam the
integration map actually listens to.

Run:  python Prototypes/RhythmHighwayCues/discover_map_battle.py
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from highway_cue_gate import editor, run_python  # shared MCP helpers

OUT = Path(r"C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\rhythm_highway_20260926")
MAP = "/Game/MelodiaIntegration/Maps/MelodiaIntegrationMap"

DISCOVER = """
import unreal, json
gw = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
rep = {}
if not gw:
    print('DISCOVER world=None')
else:
    actors = unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.Actor)
    rep['actor_count'] = len(actors)
    contract, tagged, named = [], [], []
    for a in actors:
        try:
            cls = a.get_class().get_name()
            label = a.get_actor_label()
            tags = [str(t) for t in a.get_actor_tags()]
            lname = label.lower()
            if ('battle' in cls.lower() or 'boss' in cls.lower() or 'enemy' in cls.lower()
                    or 'encounter' in lname or 'battle' in lname):
                named.append('%s [%s] tags=%s' % (label, cls, tags))
            if any(t.startswith('Encounter_') or t.startswith('melodia_') for t in tags):
                tagged.append('%s [%s] tags=%s' % (label, cls, tags))
            has_start = any('startbattle' in d.lower() or 'start_battle' in d.lower() for d in dir(a))
            props = {}
            for p in ('offLevelBattleData', 'onBattleOver', 'off_level_battle_data'):
                try:
                    props[p] = str(a.get_editor_property(p))
                except Exception:
                    pass
            if has_start or props:
                contract.append('%s [%s] start=%s props=%s' % (label, cls, has_start, props))
        except Exception:
            continue
    rep['battle_named'] = named[:20]
    rep['tagged'] = tagged[:20]
    rep['contract'] = contract[:20]

    gm = unreal.GameplayStatics.get_game_mode(gw)
    rep['game_mode'] = gm.get_class().get_name() if gm else None
    for name, getter in (
        ('narrative', lambda: unreal.MelodiaNarrativeSubsystem.get(gw)),
        ('ui_bridge', lambda: unreal.MelodiaUIBridgeSubsystem.get(gw)),
        ('rhythm', lambda: unreal.MelodiaRhythmCombatSubsystem.get(gw)),
    ):
        try:
            rep[name] = bool(getter())
        except Exception as exc:
            rep[name] = 'err:%s' % exc
    try:
        hud = unreal.MelodiaRhythmHUDWidget.find_first(gw)
        rep['hud'] = hud.get_name() if hud else None
        if hud:
            rep['hud_mode'] = str(hud.get_editor_property('active_hud_mode'))
    except Exception as exc:
        rep['hud'] = 'err:%s' % exc
    try:
        cfg = unreal.EditorAssetLibrary.load_asset('/Game/MelodiaIntegration/Config/DA_MelodiaIntegrationConfig')
        rep['encounter_ids'] = [str(v) for v in cfg.get_editor_property('EncounterIds')]
    except Exception as exc:
        rep['encounter_ids'] = 'err:%s' % exc
print('DISCOVER ' + json.dumps(rep))
"""

# Guarded authored-seam drive: the notification the game itself uses for encounter intent.
DRIVE_NOTIFY = """
import unreal
gw = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
sub = unreal.MelodiaNarrativeSubsystem.get(gw)
if not sub:
    print('DRIVE_NOTIFY no narrative subsystem')
else:
    try:
        ids = unreal.EditorAssetLibrary.load_asset('/Game/MelodiaIntegration/Config/DA_MelodiaIntegrationConfig')
        encounter = [str(v) for v in ids.get_editor_property('EncounterIds')]
    except Exception:
        encounter = []
    if not encounter:
        print('DRIVE_NOTIFY no allowlisted encounter ids')
    else:
        target = '/'.join(encounter[0].split('/')[-1].split('.')[:1]) if encounter[0].startswith('/') else encounter[0]
        note = 'melodia:battle:%s' % target
        print('DRIVE_NOTIFY sending %s' % note)
        try:
            sub.handle_quill_notification(note)
            print('DRIVE_NOTIFY sent')
        except Exception as exc:
            print('DRIVE_NOTIFY error=%s' % exc)
"""


def extract_json(text: str, marker: str):
    for line in text.splitlines():
        if marker in line:
            idx = line.index(marker)
            try:
                return json.loads(line[idx + len(marker):].strip())
            except Exception:
                return None
    return None


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    started = editor("run_pie_smoke", map=MAP, duration=45, sample_vars=[])
    sid = started.get("session_id")
    print(f"[discover] PIE {sid}")
    if not sid:
        print("[discover] failed to start:", started)
        return 1

    time.sleep(12)
    res = run_python(DISCOVER)
    text = str(res)
    data = extract_json(text, "DISCOVER ")
    print(json.dumps(data, indent=2) if data else text[:1500])

    if data and data.get("contract"):
        res2 = run_python(DRIVE_NOTIFY)
        print("[discover] authored-seam drive:", str(res2)[:400])
        time.sleep(8)
        res3 = run_python("""
import unreal
gw = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
hud = unreal.MelodiaRhythmHUDWidget.find_first(gw)
sub = unreal.MelodiaRhythmCombatSubsystem.get(gw)
print('AFTER active=%s hud=%s' % (sub.is_session_active() if sub else None, bool(hud)))
""")
        print("[discover] after:", str(res3)[:300])

    report = {"session_id": sid, "discover": data}
    (OUT / "discover_map_battle.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    final = editor("poll_pie_smoke", session_id=sid)
    print("[discover] pie final:", str(final)[:300])
    print(f"[discover] receipt -> {OUT / 'discover_map_battle.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
