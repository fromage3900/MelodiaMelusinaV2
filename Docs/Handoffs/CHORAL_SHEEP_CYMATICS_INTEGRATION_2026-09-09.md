# Choral Sheep Cymatics Integration — Night Record 2026-09-09

> **2026-09-09 late closeout:** PR #149 is superseded by later Sheep/material work already on `main`. This record is retained as historical proof/provenance only. The unique `MPC_Cymatics_Driver`, morning probe, visual evidence, integration record, and probe harness were surgically salvaged onto current `main`; stale binary content from #149 was not merged. `M_Scratch_Test.uasset` was accidentally promoted by a later material closeout and is removed in the same cleanup. Do not reopen #149 as a merge candidate.

**Branch:** `feature/choral-sheep-root-c-material-proof-2026-09-08` (pushed through `7871c5ef`)
**Goal:** sheep reacts to audio, proven in the morning level, merged to main when ready.
**Status:** behavioral + VFX proof BANKED with screenshots; Chladni nodal-line pixel proof still owed (close-up session).

## 1. What was wrong at the start of the night

- Wool master was duplicated from the wrong base (`M_Master_Toon_Universal` instead of the Nikki master).
- The 12 coat MIs' authored `Character*` overrides dangled on the wool master (different param namespace) — coats rendered defaults.
- `DA_ChoralSheepDefinition` failed `IsValid` twice over: NPC role `Ambient` (needs `Companion`), then `npc_id` empty (needs stable ID). Every interaction — Graze, Harmonize, Guide — returned False.
- `MPC_Cymatics_Driver` existed only on this PC (untracked); writer contract names `MI_Copernicus_*`/`MI_FarawayMother_*` as consumers; **no master in the sheep's lineage sampled the driver** (Universal 12/12 readers = palette only; NikkiChain 6; Toon_Character 1).
- No `MF_Chladni*`/`MF_Cymatic*` function exists anywhere in the repo.

## 2. What was done (commits on the feature branch)

| Commit | Content |
|---|---|
| `0c55a900` | Mocap docs (benchmark take, Cascadeur LiveLink, Meet2 corner) + in-content README |
| `2d1f8b49` | B2 C++: Harmonize Tick ramp (`HarmonizeActive` on cached MID), dual reactivity registration, null-safe interaction entry — **verified live in the running build via CDO reflection** |
| `f6076362` | Root-C content: rig/BP/DA/MIs, C fixture texture + PNG + generator script |
| `36663933` | Lookdev batch (Melusina MIs + Nikki/Toon masters) |
| `e87c0dbd` | Wool master v1 (Universal dup, later replaced) + 11 coats + lace MI + GlitterPile function force-adds |
| `aa52d12f` | 12-coat value migration to wool-native params (8 mapped each, 12 distinct pitch tints live); PCC reparent finished; Body blessed revert-safe |
| `0f6b6cfc` | **Wool master rebased on `M_Master_Toon_Universal_NikkiChain`** (379 params, same namespace, coats carry over); DA role Ambient→Companion |
| `7871c5ef` | **Cymatics wiring + morning proof**: 2 driver-MPC readers + pattern chain (C_ROOT × pearl × Intensity × Harmonize × driver beat × driver emissive → emissive path, one-op rollback); MPC driver force-added; DA npc_id fix; morning probe script + 2 evidence JSONs |

## 3. Morning proof (map file untouched, PIE-only summon)

- `Docs/Evidence/CHORAL_SHEEP_MORNING_PROBE_2026-09-09.json` — apply True, begin True, weight 0→1→0, clean stop. **Live-proven.**
- `Docs/Evidence/CHORAL_SHEEP_HARMONIZE_VISUAL_2026-09-09.json` — sheep floats in Harmonize with note VFX over morning cliffs. **Live-observed.**
- Captures: `Saved/SemesterEvidence/2026-W37/ChoralSheep/ChladniFleece/CF_A02_C_HARMONIZE.png`, `CF_A03_C_FIELD.png`.
- Harness: `Tools/run_choral_sheep_morning_probe.py` (force-added; `Tools/` is otherwise ignored).

## 4. Honest boundaries (not claimed)

- **Chladni nodal lines not resolved in pixels** at capture range — fleece reads cream. Pattern wiring is compiled with live values; close-up proof still owed.
- **Screenshots are probe-driven** (summon/teleport), not real-key play. No ledger row recorded.
- **PIE dies ~60–70s after start** on cold boot (both maps, no crash context; warmed sessions hold). Tests must stay short or split until root-caused.
- **Read-only file flip:** saved `.uasset` files become read-only within minutes; every save path must clear → save → verify mtime. Setter unidentified (no live UE workers per owner).
- `MI_ChoralSheep_Body` carries a pre-existing change of unknown authorship (blessed revert-safe; parent/compile/overrides verified).
- Untouched/others': SDF master edits, GlitterPile MI edit, `BP_JRPGFunctionLibrary`, Sea Above deferred files, `M_Scratch_Test` (scratch, still untracked), `.codex/config.toml`.
- PC albedo import (real color system) still pending; legacy textures still feed all 12 coats.
- Giant pink wall actor blocks the morning spawn camera — frame around it; actor itself unexamined.

## 5. Loose-end ledger

| Item | State | Next |
|---|---|---|
| Pattern pixel proof | open | close-up PIE session (this doc's §6) |
| `feature/...` → `main` PR | open after proof | PR #133 (unify) still open; stack after it lands |
| PIE ~70s death | open defect | root-cause session |
| RO setter | open mystery | hunt when fresh |
| PC albedos | pending | daylight + owner eyes |
| Pink wall actor | unexamined | identify (likely spawn-blocker) |

## 6. Next session: close-up pattern proof

PIE morning (or prototype), summon, PCC on mesh, camera ≤150 units, Harmonize, capture fleece fill-frame at beat peaks. If nodal lines absent: raise `ChladniEmissiveStrength` on PCC (instance-only, safe) and/or confirm writer publishes nonzero `Cymatic_BeatPulse` (poll MPC instance values in PIE). Pass = pattern visible in pixels + values logged next to frames.

## 7. 02:44 UTC blocker — MODAL_OPEN (owner action needed)

At 02:44:34–35 the editor raised `MODAL_OPEN` ("asset editor has no docked tabs") three times and Monolith port 9316 went deaf (TCP refused; RiderLink stays connected; editor process healthy). This dialog fires repeatedly after material duplicate/rename batches — likely a dockless asset editor spawned by the ops. **All Monolith work (PIE, material, editor calls) is blocked until the dialog is dismissed in the editor UI (one click).** No data at risk: wool + coats + DA all flushed to disk and committed through `7871c5ef`; in-editor dirty state was 0 content packages at last check (Body phantom flag excepted — disk file blessed, do not save it). After dismissing: re-run the close-up (§6), then open the `feature/...` → `main` PR (stacked after PR #133).
