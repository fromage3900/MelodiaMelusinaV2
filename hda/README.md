# HDA Lane — BS_GodFile Houdini 22.0.368 + UE5.8

**Engine plugin:** `Plugins/HoudiniEngine` (22.0.368 / 5.8) — copied 2026-08-27, `Enabled:true`
**Smoke:** `py Content/Python/smoke_houdini_engine_pcg.py` → **PASS** (hython, WP25600, .uproject, spec)

## Inventory + verification (2026-10-06) — current

Machine authority: [`Tools/Houdini/hda_verify/hda_registry.v1.json`](../Tools/Houdini/hda_verify/hda_registry.v1.json).
One command proves the lane works:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Houdini\hda_verify\run_hda_verify.ps1
```

Latest live result: **0 FAIL** (Gate 0 inventory + Gate 2 cook, Houdini 22.0.368 Education) —
receipts `Saved/Audit/hda_verify/v3_closeout_20261006/`.

| File | State | Cooked output (Gate 2) |
|---|---|---|
| `hda/ArpeggioStair_1.0.hda` | ACTIVE (24,644 B, sha `2c42c43a…`, 8 parms on type) | `output0` 512 pts / 384 prims, 0 node errors |
| `Content/HDA/ArpeggioStair_1.0.hda` | mirror, byte-identical → feeds `Content/HDA/ArpeggioStair_1_0.uasset` (uasset stale until reimported) | — |
| `hda/HDA_Melodia_CrystalCathedral_1.0.hda` | ACTIVE (32,034 B, sha `b9c09beb…`, 14 parms on type) | `OUT_Cathedral` 9278/8641 · `OUT_Rose` 1032/288 · `OUT_Collision` 1682/1608 |
| `hda/CrystalCathedralV3.hda` | ACTIVE (38,254 B, sha `35bc95ee…`, 18 parms on type) — V1 cathedral + V2 corridor, built via `Saved/HDA_build/` + copy so rebuilds never touch `hda/backup/` | cathedral pins identical to V1 · `OUT_Corridor` 1/1 fog volume · LOD tiers [14, 8, 5] |
| `hda/backup/*.hda` (9 files) | **STUBS** — no `Contents.gz`, 866–1,002 B | cannot be cooked; they are shells, **do not restore from them** |
| `hda/SpaceTraversal_OrbitalRings_1.0.hda`, `hda/CorridorNetwork_1_0.hda`, `hda/CrystalCathedralV2.hda`, `hda/HDA_Foundry_FieldAtlas_1.0.hda` | OWED — builders/recipes exist, files never written (V2 superseded by V3, kept as provenance) | reported as WARN by the gate |
| `Plugins/HoudiniEngine/Content/**` (15) | VENDOR examples/tools | counted only |

**Controls promotion — resolved 2026-10-06** (this was the old "both active HDAs
expose 0 parameters" finding): every active HDA now declares its controls **on the
HDA type** — ArpeggioStair 8, CrystalCathedral 14, CrystalCathedralV3 18
(`chain_type`/`lod_count` intentionally stay inner build-time config). Builders run
`Tools/Houdini/hda_promote_controls.py` stage1 (before `createDigitalAsset` —
instance content is locked after) and stage2 (spares → definition). Gate 2 enforces
it: `expect.parms` must exist on a fresh instance, and `parm_drive` probes set a
parm, prove the geometry moved, then restore and re-prove the golden pins.

Everything below this line is 2026-09-02 provenance (dates, blockers), not current status.

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
