# Nikki master drop — 2026-09-09

**Status:** INCIDENT RECORD, not current gameplay authority  
**Asset:** `Content/EnvSandbox/Materials/Masters/M_Master_Nikki.uasset`

## What went missing

The Nikki **character** master left `main`. The landscape master `M_Master_Nikki_Landscape.uasset` stayed. Sheep lookdev had already been locked to `M_Master_Toon_Character`; the missing file is the NikkiHero / glitter / showcase master, not the Sheep body parent.

## Why

This was not an Unreal save loss and not a missing LFS object.

1. Commit `f19b6459` (`merge(cross-line): unify origin/main with Line A`) **deleted the file even though both merge parents still had it.**
2. The same merge dropped 11 sibling EnvSandbox materials (Toon Cosmic, Grand Water v6, stained glass, three showcase MIs, two water MIs, Mandelbulb master, enhanced fabric).
3. `.gitignore` has `Content/EnvSandbox/*` and did **not** un-ignore `Materials/Masters/`. After the merge, `git add` would not put the master back. A later lookdev batch (`36663933`) could update the landscape/toon masters that were still tracked, but could not resurrect `M_Master_Nikki.uasset`.

Last good blob: `f19b6459^1` — LFS pointer `sha256:6016b1389ca4acc8e530d72cfae12651f482f6f049c28f37c8a997ccc426f255` (186008 bytes).

Guard: `python Tools/guard_protected_assets.py --base origin/main` (also in Echo CI). Restore a dropped master with `git checkout f19b6459^1 -- <path>`, not a new file.

## What this does not change

Do not reparent Choral Sheep off `M_Master_Toon_Character`. Owner lock for Sheep remains Nikki-quality character lookdev + Chladni child, not a new wool master and not a random landscape/water master.
