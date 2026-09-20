# UI label map — 2026-09-17

**Live tip (fromage):** `C:\EnvironmentPortfolio\BS_GodFile`  
**Do not use:** `D:\_relocated\BS_GodFile_studio` (relocated mirror)

Stamped from Melodia UI Lookdev verify + Melodia study bot ACK. Materials LABEL_MAP stays materials-only (`Docs/Materials/LABEL_MAP_2026-09-09.md`).

## SHIP (P0 WBP)

| Asset | Notes |
|-------|-------|
| `/Game/Melodia/Blueprints/WBP_RhythmHUD` | P0-A rhythm/combat HUD shell (default apply surface) |
| `/Game/Melodia/UI/Rhythm/WBP_MelodiaRhythmHighway` | P0-A note highway **authority** (SoftMG + FiligreeBatchO_Baroque SSOT) |
| `/Game/Melodia/UI/WBP_Battle_Rhythm` | P0-A battle rhythm surface |
| `/Game/Melodia/UI/WBP_GradePop` | P0-A grade feedback · NS-UI-01 slot (WAIT) |
| `/Game/Melodia/UI/Quill/WBP_MelodiaQuill*` | P0-B dialogue |
| `/Game/MelodiaIntegration/UI/WBP_MelodiaInteractPrompt` | P0-B companion/interact · NS-UI-03 slot (WAIT) |
| `/Game/Melodia/UI/WBP_DialogueBubble` | P0-B |
| `/Game/Melodia/UI/WBP_MainMenu` + settings/save/quest | P0-C pause/nav |

## MISSING / do not target

| Asset | Notes |
|-------|-------|
| `/Game/Melodia/UI/Rhythm/WBP_MelodiaRhythmTrack` | **MISSING on disk** — use Highway |

## Figma sources

| Source | Key / Path | Notes |
|--------|------------|-------|
| Melodia game UI (design SSOT) | file key `Yx8ud7n39NdWZvnNvo4Xlf` | ART_SOURCE + melodia-motion-connect; **not** open in desktop at ~2:46pm ET |
| Active desktop tab | Untitled · `ewS0yt17hiWq2KXPa5RfCX` | open ~2:46pm ET |
| Also open | Update Accessory Viewer Page · `1jSzK6eFu73A4vqoCRGoNS` | |
| In-engine pack (~339, ~2026-08-04) | `/Game/Melodia/UI/Textures/Figma/` | |
| Site pull | `C:\Users\froma\my-site\generated\assets\melodia-game-ui\` | figma_complete / figma_pull / redesign |
| Motion connect | `C:\Users\froma\my-site\wix\melodia-motion-connect.json` | SoftMG highway |
| Motion channels | `Imports/UI/Specs/_MOTION_CHANNELS.md` | |
| Rhythm board | Game/RhythmReactivityBoard 41:242 | SoftMG + FiligreeBatchO_Baroque |

## Motion / NS

- Motion stub: `Saved/Audit/ui_lookdev/UI_MOTION_PARALLAX_PLAN_STUB_2026-09-17.md`
- Rhythm HUD apply: `Saved/Audit/ui_lookdev/UI_RHYTHM_HUD_APPLY_PLAN_2026-09-17.md`
- NS↔WBP slots NS-UI-01..03: **WAIT** for New Bot + Melodia study intake — do not wire
