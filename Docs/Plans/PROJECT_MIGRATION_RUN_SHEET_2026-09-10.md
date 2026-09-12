# Run Sheet — _PROJECT Texture Migration + Class-A Twin Verify — 2026-09-10

**Single-editor session. One holder. Owner Ctrl+S. No second MCP surface.**
**Headless pre-verification DONE:** all 170 embedded `/Game/` refs across the 96
pretty twins resolve to files on disk (`mi_twin_missing_refs_2026-09-10.csv` =
0 missing). Editor pass confirms live reference integrity, not existence.

## Batch 1 — Texture migration (editor Asset Movers only, NO code changes)

Move with the editor (redirectors fix the 7 twins automatically). Never
filesystem-move `.uasset`.

| # | Source (under `…/_PROJECT/04_Materials/`) | Destination | Why |
|---|---|---|---|
| 1 | `Textures/Violin/` minus `screensnap_000*` (35 files) | NEW `/Game/EnvSandbox/Textures/Melusina/Violin/` (matches Cello/Crystal/Note convention) | Bound by 5 twins: BezierDetails, Foot, Strings, ViolinBase, ViolinTop |
| 2 | `Textures/Violin/screensnap_0001–0007` | OUTSIDE `Content/` (scratch) | Editor screenshots, not shippable |
| 3 | `Textures/Textures/T_Sand_BSS_ao`, `T_Sand_BSS_height` | `/Game/EnvSandbox/Textures/PBR_Sets/Sand/` (siblings already there) | Bound by `MI_T_Sand` |
| 4 | `Textures/Tileables/Untitled_material_*` (8 files) | NEW `/Game/EnvSandbox/Textures/PBR_Sets/Untitled/` | Bound by `MI_Untitled_material` |

Verify after each move: open the bound twin, confirm maps still linked
(redirector or re-link), Ctrl+S. Then `verify_baseline` + one map-load PIE smoke.

## Batch 2 — Class-A twin verify (same session, 24 twins)

For each wired twin in `MI_TWIN_REVIEW_2026-09-10.md` Class A: confirm bound
maps resolve live → mark Orphan quarantinable. For the 72 scalar-only twins:
spot-check override values are intentional (batches ≤25).

## EXCLUDED from this session — MPC move is a C++ task

`/Game/Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette` is hardcoded in:
- `Plugins/MelodiaWardrobe/Source/…/MelodiaMagicalTransformTypes.h:112`
  (`CollectionPath`, needs closed-editor rebuild after change)
- `Plugins/MelodiaCore/Source/…/MelodiaRhythmReactivitySubsystem.cpp:22`
  (`AudioCollectionPath`)
- ~6 `Content/Python/*.py` scripts + TouchDesigner/OSC/specs references

**Do NOT move the MPC in-editor** — it would desync the C++ writer paths and
silently kill all audio reactivity (writes to a stale path are no-ops).
Canonical target when scheduled: `/Game/Melodia/Materials/MPC_Melodia_Palette`
(empty dir, mirrors `MPC_Cymatics_Driver` in `Melodia/Cymatics/`). Requires:
header edits → closed-editor `Build.bat` → PIE reactivity re-proof → script/spec
path sweep. `MPC_MelodiaInk` (same folder) has only doc-level refs — move it in
the same C++ task or leave; it is not load-bearing for P0.

## Done definition

Batch 1+2 green: `_PROJECT` holds no twin-bound textures; `verify_baseline`
clean; PIE smoke 0 errors; ledger `static_gates` row. `_PROJECT` emptying of
house/assets follows as a separate session.
