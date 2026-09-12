# Brass Rebuild + P2 Enhanced-Fabric Reparent — Execution Record — 2026-09-10

**Branch:** `cleanup/brass-p2-reparent-2026-09-10` (14 files).

## Brass: 8/8 rebuilt (replaces admitted GildedLoom byte-copy stubs)

- Pre-flight found the stubs' inner object is literally `MI_Copernicus_GildedLoom`
  (filename ≠ object name) — bare-path `load_asset`/`delete_asset` fail silently.
  All 8 verified **0 referencers**, binaries backed up to Temp `qol_backup/brass_stubs/`,
  deleted via full object paths, recreated with the ORIGINAL
  `Content/Python/_mi_brass_animated_create.py` unmodified:
  8 created, 0 exist-skips, 0 failed (tex=5, scalars=17 each; Iridescence/Opacity
  channels have no source PNGs — recorded gap).
- 8/8 `load_asset` OK. 0 dirty packages at close.

## P2: 6/6 rescued from phantom parent

- All 6 MIs had `parent=None` (M_Master_Nikki absent from Content) and ZERO params —
  empty 6.6KB shells. Reparented to `M_Universal_Enhanced_Fabric` per owner call,
  with per-suite values from the sheen doc remapped to the real schema
  (Metallic/Roughness/UVScale/AudioReactivity scalars + BaseColor vector).
  Nikki-only params (SheenWidth/Bias/bSheenUsesNormal/RoughnessMax) have no
  counterpart and were dropped — documented, not silent.
- Verified live: Gown parent + 4 scalars + BaseColor confirmed via redump.
- The PBR_Auto `T_FarawayMother_*` twins belong to the phantom-master LOD chain,
  not these MIs — left for the LOD-remap task.

## Proof

- PIE smoke `LV_SeaAbove_Prototype` (session pie_smoke_1_222220): 58 samples,
  0 errors, clean teardown. Evidence JSON alongside this record.

## Incident (same session, recovered)

- GPU driver crash (`D3D12RHI: texture 16384x4096x2`) killed the editor between
  stub deletion and rebuild; crash folder `Saved/Crashes/UECC-…-2AC03DB7…_0000`.
  Relaunch produced a two-editor state; held all mutations until owner confirmed
  single editor (PID 44488). No half-written assets (report file still 09-04
  dated until the successful rerun).

**Evidence level:** live-proven (rebuild report + redumps + PIE smoke).
