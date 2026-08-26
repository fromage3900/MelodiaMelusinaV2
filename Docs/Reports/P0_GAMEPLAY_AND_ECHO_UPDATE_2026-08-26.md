# P0 Gameplay and Echo Update — 2026-08-26

## Outcome

The First Dream Harmony completion defect is closed in commit `3912f570`. The
authored scene now sends one atomic `questcomplete` command containing the
quest, completion flag, reward, stable intent, and restart checkpoint. The
content generator emits the same command, and the route contract prevents the
two sources from drifting apart.

This session also established a healthy build and scoped runtime baseline. It
did **not** complete the player-visible or durable P0 golden run, so no current
rhythm, HUD, wardrobe, Glide, music-key, four-outcome, or restart gate is
promoted here.

## Verified evidence

| Tier | Check | Result |
| --- | --- | --- |
| T1 offline | `python -B Tools/test_melodia_first_dream_route_contract.py` | PASS — 4 checks |
| T1 offline | `python -B Tools/test_melodia_progression_contract.py` | PASS — 6 checks |
| T1 offline | `python -B Tools/test_melodia_chapter_content_package_contract.py` | PASS — 6 checks |
| T1 offline | `python -B Tools/test_echo_contract.py` | PASS — 77/77 |
| T1 editor-static | `python -B Tools/echo_run.py run static_gates` | `graph_reachability` PASS; `bp_live_path` PASS |
| T1 build | Closed-editor `BS_GodFile Win64 Development -NoUnity` | PASS — 104/104 actions; `BS_GodFile.exe` produced |
| T1 editor automation | `Melodia.Integration` | PASS — 8/8 |
| T1 editor automation | `Melodia.Wiring` | PASS — 5/5 |
| T2 scoped runtime | `/Game/MelodiaIntegration/Maps/MelodiaIntegrationMap`, session `pie_smoke_1_170122`, marker `MELODIA_P0_BASELINE_20260825` | PASS — 8.02 s, 380 samples, expected Melusina pawn/AnimBP identity, zero forbidden runtime matches |

The scoped PIE smoke counted zero `Blueprint Runtime Error`, `Accessed None`,
`LogChooser`, `Ensure condition failed`, `Fatal error`, and
`MELODIA_INTENT_REJECTED` matches after the marker. It was an idle health test;
no battle was started.

## Ledger interpretation

- `P0-NARR-01`: **closed** by `3912f570`.
- `static_gates`: remains **fail** until the full Blueprint sweep, UI, and
  material-baseline chain passes against one frozen baseline.
- `battle_integration_map`: remains **hold** because victory, defeat, fled, and
  unavailable were not exercised in this session.
- `rhythm_owner`, `hud_single_writer`, `rhythm_grade_to_result`,
  `wardrobe_equip_roundtrip`, `wardrobe_gameplay_hook`, and `music_world_key`:
  remain **open** at their required player-visible or durable proof tier.

## Next P0 proof

On one frozen checkout and one editor, run a real-input battle through the
instantiated stock battle UI. Capture one miss and one stronger rhythm grade,
all four terminal outcomes, exactly-once Quill resume/abort, and the owning HUD
identity. Then run the wardrobe/Glide and music-world-key save/restart paths.
Only those captured assertions may promote the remaining gates.
