# HDA Lane — BS_GodFile Houdini 22.0.368 + UE5.8

**Engine plugin:** `Plugins/HoudiniEngine` (22.0.368 / 5.8) — copied 2026-08-27, `Enabled:true`
**Smoke:** `py Content/Python/smoke_houdini_engine_pcg.py` → **PASS** (hython, WP25600, .uproject, spec)

## Quick Start (next 5 min)

1. **License (blocking):** Open `Houdini License Administrator` → Sign in SideFX → **Houdini Engine for Unreal FREE** (10 licenses/studio). Until `hserver -l` shows a license, HDAs will not cook. Apprentice cannot cook Engine HDAs.
   ```powershell
   & "C:\Program Files\Side Effects Software\Houdini 22.0.368\bin\hserver.exe" -l
   # want: Used Licenses: Houdini Engine ...  (not "None")
   ```

2. **First HDA (ArpeggioStair):** Open Houdini 22.0.368 → File/New → `hda/ArpeggioStair_1.0.hda`
   - See `Docs/WorldGen/HOUDINI_ENGINE_SMOKE_SPEC_2026-08-27.md` §4 for parameter list (seed, stepCount 16, laneCount 4, spacing, baseMidiNote, scale, heightPerDegree).
   - Network: `Grid (stepCount x laneCount) → Point Wrangle (seed/midi/lane) → Copy mesh → Output`. Save as HDA.

3. **UE cook:** Copy `.hda` to `Content/HDA/` (or `hda/` then import) → drag into `L_HDA_Smoke` → set `seed = stable_chunk_seed(3900,0,0)` → Cook → **Bake to Actors** → assign `DL_Musical_HeroGameplay`.

4. **Verify:** PIE → `SetPressedForActor` on pad → `PlayMusicalNote` → `ScoreState total=64 hit=1 streak=1`.

## Helpers

- `Content/Python/create_hda_arpeggio_stair.py` — generates the HDA headlessly via `hython` (no GUI). Run:
  ```powershell
  & "C:\Program Files\Side Effects Software\Houdini 22.0.368\bin\hython.exe" Content/Python/create_hda_arpeggio_stair.py
  ```
- `Content/Python/smoke_houdini_engine_pcg.py --json` — pre-flight before opening editor.

## You already have

- `Docs/WorldGen/PURCHASE_RESEARCH_2026-08-27.md` — live Fab scan, fit scores (MeshTerrain-only)
- `Docs/WorldGen/CALYSTO_MESHPARTITION_ADAPTER_SPEC_2026-08-27.md` — Calysto 70 biomes → MeshPartition without Landscape
- `Docs/WorldGen/HOUDINI_ENGINE_SMOKE_SPEC_2026-08-27.md` — install + HDA spec + UE wiring

## Blockers today

- `hserver` shows **0 licenses** — get FREE Engine license first.
- Do not create `ALandscape` — P0 is MeshTerrain-only. HDA must output meshes/HISM.

Next: verify UE5.8 compiles `HoudiniEngine` modules on next editor launch, then cook first HDA.
