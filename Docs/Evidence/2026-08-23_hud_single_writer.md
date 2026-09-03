# HUD/rhythm single-writer evidence — 2026-08-23

## Committed scope

- `UMelodiaJRPGBattleOverlaySubsystem` is retained only as a compatibility
  observer and no longer creates viewport widgets.
- `UMelodiaUIBridgeSubsystem` is the sole owner of the battle widget, keyboard
  legend, and collapsed rhythm prompt.
- `WBP_MelodiaRhythmHighway` remains the native rhythm-HUD widget asset; the
  associated skill and room-mod data stay data-only.

## Saved and current evidence

- `Saved/Dashboards/bp_sweep.json` contains the
  `/Game/Melodia/UI/Rhythm/WBP_MelodiaRhythmHighway` sweep record with
  `error: null` and parent
  `/Script/MelodiaCore.MelodiaRhythmHUDWidget`.
- `Saved/Echo/BattleIntegrationMap/hud_single_writer_source_20260822_report.json`
  records the source ownership boundary and its offline contract result. Its
  `live_proof` is intentionally `PENDING`.
- `python -B Tools/test_melodia_hud_ownership_contract.py` passed on
  2026-08-23.
- `python -B Tools/test_melodia_skill_bridge_contract.py` passed on
  2026-08-23.
- The current UE 5.8 native build completed UHT, compilation, and linking of
  `BS_GodFile.exe`; it validates the source owners, not the UMG viewport.

## Explicit remaining gate

A clean editor session must still run a focused battle viewport smoke and
prove one visible Melodia HUD owner with no duplicate widgets. This commit does
not claim that live proof, does not load a map, and does not alter capture or
webfront state.
