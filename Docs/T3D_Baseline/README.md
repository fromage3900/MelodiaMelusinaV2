# T3D Material Baseline

**Created:** 2026-08-07 · **Engine:** UE 5.8 (CL-55116800) · **Source:** live editor via Monolith `project_query/export_asset_text`

A committed, hash-verified T3D snapshot of the toon/material spine — the assets that carry this
project's art direction. Unlike `Saved/T3D/` (gitignored, so every prior catalog was a one-off
document that could not be diffed), this lives under tracked `Docs/` and is checked by a script that
exits non-zero on drift.

## Contents

| Path | What |
|---|---|
| `materials/*.t3d` | 55 raw T3D payloads, LF-normalised — line-diffable by `git diff` |
| `materials/_export_results.json` | Per-asset export record |
| `material_catalog.json` | Catalog with SHA-256 of each T3D payload — the drift baseline |
| `verify_baseline.py` | The gate: re-export from live editor, diff against hashes |

## Coverage

| Family | Assets | Payload | Nodes |
|---|---:|---:|---:|
| Master Materials | 10 | 4,049,443 | 3,100 |
| Material Functions | 27 | 2,572,556 | 2,185 |
| Toon Profiles | 17 | 8,203 | 17 |
| Parameter Collections | 1 | 6,287 | 1 |
| **Total** | **55** | **6,636,489** | **5,303** |

Largest: `M_Master_Toon_Universal` (1,201 nodes), `M_Master_Toon_Cosmic` (1,042),
`MF_MooaToonBaseInput` (378), `MF_SDF_BandRelief` (373), `M_Master_Toon_Landscape_HeightBlend` (301).

For scale: the entire 23-widget UI catalog is 5,649 nodes. This spine is 5,303 in 55 assets — the
material stack is roughly the same authoring weight as all of the UI, and it is the half that
carries the look.

## Usage

Check for drift (exit 0 = clean, 1 = drift or failure):

```bash
python Docs/T3D_Baseline/verify_baseline.py
```

Show what changed:

```bash
python Docs/T3D_Baseline/verify_baseline.py --diff
```

Accept drift after an intentional material edit, then commit the result:

```bash
python Docs/T3D_Baseline/verify_baseline.py --update
```

Requires the editor running with Monolith on `127.0.0.1:9316`.

## ⚠️ `max_bytes` — read before adding assets

`export_asset_text` defaults to a **256 KiB** budget. Over that it returns a ~166-byte plain-text
notice *while the MCP call still reports success*. A naive harness records that as a healthy export
with zero nodes. Five of the six most important assets here hit it on the first pass —
including `M_Master_Toon_Universal`, the single most complex asset in the project.

This is the same failure that produced the 171-byte `BP_QuestNotification` stub in the 08-05 widget
catalog (see `CompatibilityLabs/Snapshot_2026-08-06/Saved_T3D/LIVE_VS_CATALOG_2026-08-06.md`).

`verify_baseline.py` guards against it in `export()`: an envelope is only accepted when it parses as
JSON, has `success: true`, **and** `full_bytes == returned_bytes`. Any new export tooling must
enforce all three. Ceiling is 4 MiB.

## Selection rule

Included: all `ToonProfile`; `M_Master_*` materials in `Masters/`; `MPC_Melodia_Palette`; and the
material functions carrying identity — `MF_Nikki*`, `MF_Melu*`, `MF_Mooa*`, `MF_Impressionist_*`,
`MF_Gemstone`, `MF_ClothWindDrape`, `MF_Itto`, `MF_Madoka`, `MF_AnimeSkinWrap`, `MF_SDF_BandRelief`,
`MF_LandscapeStorybookSDF`, `MF_Triplanar_Stable`, `MF_ColorRamp3`, `MF_IridescenceSheen`.

Excluded: the 483 `MaterialInstanceConstant` leaves (they follow their masters), `_Archive/`,
`_Scratch/` duplicates, `MaterialFunctions_Legacy/`, and dated variant copies —
`_BACKUP_*`, `_QUARANTINE_*`, `_AUTHORED_RESTORED_*`, `_LIVE_RENDER_REPAIR_*`,
`_LIVING_STORYBOOK_*`, `_SAFE_FALLBACK_*`, `_TRIPLANAR_WORK_*`.

> `M_Master_Toon_Landscape_HeightBlend` alone has **9** dated sibling copies in `Masters/`. Only the
> undated asset is baselined. Which of the nine (if any) is still authoritative is unresolved and
> not decided here — see "Open" below.

## Open

- `M_Master_Nikki` / `M_Master_Nikki_Landscape` live in `Materials/_Scratch/`, not `Masters/`.
  Baselined from their current location; promotion is an art-direction call.
- Duplicate asset *names* across `Masters/`, `Instances/`, `_Scratch/`, `_Archive/`
  (`M_Master_Toon_Universal_Inst` exists in three places). Not resolved.
- Widget catalog is not yet under this gate; it still lives in `CompatibilityLabs/`.
