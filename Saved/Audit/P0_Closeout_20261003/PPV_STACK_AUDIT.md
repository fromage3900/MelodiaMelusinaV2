# PPV_NikkiDream stack audit (Morning) — 2026-10-03, read-only
| # | Master | Domain | PS instr | MPC reads |
|---|--------|--------|---------|-----------|
| 1 | M_PP_StorybookOutline_Render2026 | POST_PROCESS | 332 | Palette: RhythmPulse only (+ MPC_Palette_RhythmPulse) |
| 2 | M_PP_StarryNightOverlay_Candidate | POST_PROCESS | 347 | Palette: Melusina_Lavender/SoftWhite, R1999_Gold/Navy (static colours, no beat) |
| 3 | M_PP_MeluColorGrade_Frozen | POST_PROCESS | 222 | Palette: BeatIntensity, BeatPulse, GlobalEmissiveBoost, MeluPrimary, RhythmPulse, VictoryPulse; MPC_MelodiaInk: InkSyncVision |
| 4 | M_PP_MelodiaInk_Frozen | POST_PROCESS | 226 | Palette: BeatPulse, BreakPulse, ComboNormalized, EnemyTension, MeluPrimary, VictoryPulse; MPC_MelodiaInk: 8 Ink* |
| 5 | M_PP_EdgeDesat | POST_PROCESS | 91 | none |
All five compile. Monolith get_all_expressions fails to load them (export_asset_text works); Python load_asset works.
Findings: Bass/Mid/Treble (OSC band values) are read by NO PP master; Ink* are driven only via MPC_MelodiaInk;
a second MPC_Melodia_Palette exists at /Game/_PROJECT/04_Materials (17 scalars) besides the 54-scalar canonical one.
Known from earlier: slot-1 ZenForestTest MI_StarryNight_VanGogh is surface-domain (dropped); weight 0.18 vs canonical 0.69; label PPV_Dreamprint_Candidate vs PPV_NikkiDream.
