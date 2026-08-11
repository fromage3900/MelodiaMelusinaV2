# Texture Duplicate Audit — Decision 032
**Date:** 2026-08-03
**Source:** Monolith project_query search for T_Melodia_ textures across all Content roots

## Finding: 4 texture locations, ~50 duplicated textures

| Location | Role | Status |
|---|---|---|
| /Game/Melodia/UI/Textures/Universal/ | NEW canonical set (T_Melodia_Universal_*) | 10 textures, actively wired by Kiro |
| /Game/EnvSandbox/Textures/Melodia/GameUI/ | OLDER production set | 20+ textures, used by WBP_MainMenu |
| /Game/EnvSandbox/Textures/Source/MelodiaGameUI/ | IMPORT source (original PNG imports) | 20+ textures, not directly referenced |
| /Game/EnvSandbox/Alphas_Melodia/ | ALPHA/mask variants | Partial overlap (NoteHead, Hitline, SheenSweep, etc.) |

## SoftMG Textures (Unique to GameUI)
These 7 textures exist ONLY in /Game/EnvSandbox/Textures/Melodia/GameUI/:
T_Melodia_SoftMG_Parchment, T_Melodia_SoftMG_SealSP, T_Melodia_SoftMG_SealULT, T_Melodia_SoftMG_ScrollEdge, T_Melodia_SoftMG_LaneInk, T_Melodia_SoftMG_Hitline, T_Melodia_SoftMG_PillowChip

## Concluson
The **Universal** texture set at /Game/Melodia/UI/Textures/Universal/ is the actively-referenced canonical set (10 textures pre-wired in Kiro's Foundation WBPs). The **GameUI** set is the production fallback. The **Source** set is the import origin. The **Alphas** set has partial overlap.

## Recommendation
1. Consolidate all active widget references to point to the Universal set
2. Do NOT delete the GameUI set — still referenced by WBP_MainMenu (SoftMG_Parchment)
3. Do NOT delete the Source set — it's the import origin
4. Alphas can be quarantined after verifying no active widget references them
