# Live Editor Verification Kit — P0 Orchestra Gates

**Run with one editor instance on port 9316 (AGENTS.md § Safe working rules).**

## Gates to Verify LIVE (not probe)

| Gate | Contract `PROJECT.md:107-116` | Live Proof | Command |
|---|---|---|---|
| `rhythm_owner` | One rhythm path → JRPG damage | PIE Q/W/O/P highway → damage delta vs `melodia.Rhythm.Disable 1` | `python Tools/verify_p0_live.py --gate rhythm_owner` |
| `hud_single_writer` | One writer per HUD surface | No ambient clear of highway (`bExecutionDrivingHighway` check) | `python Tools/bp_sweep.py` + visual `UMelodiaRhythmHUDWidget` |
| `wardrobe_equip_roundtrip` | Equip→save→restart→load correct outfit | VRM4U outfit + `MelodiaWardrobeSubsystem` roundtrip | `python Tools/verify_p0_live.py --gate wardrobe_equip_roundtrip` |
| `rhythm_grade_to_result` | Grade changes result; Quill resumes once | Full campaign `Docs/ECHO/campaign_01_rhythm_damage_delta.md` | `python Tools/rhythm_battle_runtime_probe.py` then `echo_run.py record` |
| `music_world_key` | Phrase opens world object | Piano `Source/BS_GodFile/Piano/` beyond water → room-shell | PIE: play phrase → tag probe |
| `wardrobe_gameplay_hook` | Outfit → observable gameplay | One outfit stat/ability delta (not just visual) | PIE + `DT_MelodySlime_RoomMods.json` |

## How to Run (one editor)

1. Ensure single `UnrealEditor` process, `curl http://localhost:9316/health` → `{"status":"ok","tools":16}`.
2. `python Tools/project_state.py --view integration` — confirm `runtime` etc PASS ledger.
3. `python Tools/bp_live_path.py Content/MelodiaIntegration/Blueprints/BP_MelodiaJRPGGameInstance` → LIVE.
4. Run kit: `python Tools/verify_p0_live.py --all` — writes `Saved/Echo/live_verify_*.json` (frames + assertions; never just PNG).
5. Record only with real input evidence: `python Tools/echo_run.py record <gate> pass --note "PIE Q/W/O/P ..."` — no probe-only `pass`.

## Safety
Never `git clean -fd` / `git checkout -- .` (bulk Content untracked). One editor only. Check `list_errored_blueprints` before T3D inject.

## Reference
- `AGENTS.md` Evidence standard 2026-08-11
- `Tools/rhythm_battle_runtime_probe.py` (now fixed: skill_class scoping)
- `specs/echo_pipeline.json` orchestra stage
