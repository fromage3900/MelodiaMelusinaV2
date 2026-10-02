# Bow HUD v4 — Figma tokens for UE staging

**Status:** canonical staging payload — 2026-10-01  
**Figma:** https://www.figma.com/design/wroE3kZTyOVXpjVlJw5Y6g  
**UE destination:** `/Game/EnvSandbox/Textures/Melodia/GameUI/BowHUD_v4`

This package contains the individual visual atoms from the current **Bow HUD v4 FINAL CANON** component library. Text-bearing Vitals / Quest / Dialogue / RhythmHighway composites are intentionally excluded; labels, keys, numbers, health values and cooldowns remain live UMG text.

## Tonight: stage in Unreal

From the Unreal Editor Python console:

```python
import stage_bow_hud_v4_tokens as s
s.main()
```

The script hydrates the exact transparent Figma PNG @2x bytes into `Saved/Staging/BowHUD_v4`, imports them into `/Game/EnvSandbox/Textures/Melodia/GameUI/BowHUD_v4`, and applies UI-safe texture settings.

## Why the payloads end in `.png.b64`

The repository routes `*.png` through Git LFS. The GitHub connector can create normal Git blobs but cannot upload the required LFS backing objects. Committing raw PNG blobs would violate the repo contract. Each `.png.b64` is the exact Figma PNG encoded as text; the staging script decodes it losslessly under `Saved/` before import.

## Export contract

- PNG @2x, transparent, trimmed to component bounds.
- No baked text, key letters, cooldown numbers, gameplay values or flattened screen captures.
- Reticle center remains optically clear; state reconfiguration belongs to assembly/motion.
- Timing authority: **117 ms snap → 234 ms ripple → 469 ms handoff**.
- Bayer/dither remains a UE material concern, not baked token art.

## Token inventory

| Token | Figma node | Native | Export | Runtime filename |
|---|---:|---:|---:|---|
| `OuterFiligree` | `5:2` | 220×220 | 440×440 | `T_UI_BowHUD_OuterFiligree.png` |
| `InnerScore` | `6:2` | 174×174 | 348×348 | `T_UI_BowHUD_InnerScore.png` |
| `CoreStar` | `6:31` | 78×78 | 156×156 | `T_UI_BowHUD_CoreStar.png` |
| `PerfectCrest` | `6:38` | 54×72 | 108×144 | `T_UI_BowHUD_PerfectCrest.png` |
| `ModeCrest` | `6:70` | 122×36 | 244×72 | `T_UI_BowHUD_ModeCrest.png` |
| `PromptCartouche` | `6:49` | 270×54 | 540×108 | `T_UI_BowHUD_PromptCartouche.png` |
| `TargetCartouche` | `6:60` | 226×66 | 452×132 | `T_UI_BowHUD_TargetCartouche.png` |
| `ReleaseCrest` | `6:153` | 74×74 | 148×148 | `T_UI_BowHUD_ReleaseCrest.png` |
| `ScoreBloomTerminal` | `6:142` | 132×96 | 264×192 | `T_UI_BowHUD_ScoreBloomTerminal.png` |
| `EdgeGlint` | `14:169` | 48×12 | 96×24 | `T_UI_BowHUD_EdgeGlint.png` |
| `FeatherTick` | `14:163` | 58×22 | 116×44 | `T_UI_BowHUD_FeatherTick.png` |
| `PearlJoint` | `14:156` | 18×18 | 36×36 | `T_UI_BowHUD_PearlJoint.png` |
| `StorybookCorner` | `6:76` | 180×132 | 360×264 | `T_UI_BowHUD_StorybookCorner.png` |
| `StorybookGlint` | `6:131` | 18×18 | 36×36 | `T_UI_BowHUD_StorybookGlint.png` |
| `ShellStarDivider` | `6:110` | 920×88 | 1840×176 | `T_UI_BowHUD_ShellStarDivider.png` |
| `Cursor_Default` | `6:160` | 60×66 | 120×132 | `T_UI_BowHUD_Cursor_Default.png` |
| `Cursor_Hover` | `6:174` | 60×66 | 120×132 | `T_UI_BowHUD_Cursor_Hover.png` |
| `Cursor_Pressed` | `6:188` | 60×66 | 120×132 | `T_UI_BowHUD_Cursor_Pressed.png` |

## Assembly shorthand

Base reticle: `OuterFiligree + InnerScore + CoreStar`.  
Aim / Target: introduce `FeatherTick + PearlJoint + EdgeGlint` asymmetrically.  
Perfect: add `PerfectCrest + ReleaseCrest + ScoreBloomTerminal`.  
Cursor uses the separate `Default / Hover / Pressed` CelestialQuill textures.
