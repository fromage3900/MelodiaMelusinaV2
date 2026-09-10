# Receipt - TextureWeight Universal/Wool scan - 2026-09-09

**Status:** LIVE PASS (set_instance_parameter; **no** Monolith save) - **owner Ctrl+S confirmed** (2026-09-09 eve)  
**Index:** [Docs/Materials/README.md](README.md) - **Labels:** [LABEL_MAP_2026-09-09.md](LABEL_MAP_2026-09-09.md)  
**Clean-env:** [RECEIPT_MATERIALS_CLEAN_ENV_2026-09-09.md](RECEIPT_MATERIALS_CLEAN_ENV_2026-09-09.md)  
**Local audit:** `Saved/Audit/TEXTUREWEIGHT_SCAN_2026-09-09.md` (+ `.csv`)

## Summary

| Metric | Count |
|--------|------:|
| Scanned (Melodia+EnvSandbox, Universal/Wool parent) | **2128** |
| Already OK | **2094** |
| Set `TextureWeight=1.0` (had tex overrides, TW missing/0) | **34** |
| Skipped `MI_ChoralSheep_Coat*` | **12** |
| Skipped (no TW on parent: Niagara/VFX, Nikki landscape, etc.) | (not counted as defects) |

Default used: **1.0** (not sheep coat **1.3944**).

## Notable assets in the 34

Includes Shorewake dress (`MI_Melusina_Dress_Shorewake`), Melusina iris/outline, SirMelodious, Starskiff set, SeaAbove reef/cloth, NikkiHero x5, basetrim/concretetrim/landscape_grass, jelly, Universal Inst1/2.

Full numbered list: local `Saved/Audit/TEXTUREWEIGHT_SCAN_2026-09-09.md`.

## Hard rules

- No Monolith `save_packages` / `recompile_material`.
- Owner Ctrl+S for the 34 dirty MIs (plus any stubbed SM packages from the same evening).