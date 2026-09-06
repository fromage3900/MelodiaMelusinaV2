# Build takeover handoff — 2026-09-03 (Claude quota-out → build lane)

## Editor state

- UnrealEditor PID 19336, Monolith live on 9316, level `MelodiaIntegrationMap` loaded,
  PIE stopped. **1 dirty package: `MI_KleinVeil_CymaticReactive`** — not written by this
  session (both klein_veil runs abort before any set/save; likely load/rescan artifact).
  Verify by re-read before deciding; do not save blindly, do not discard blindly.

## Done this session (all committed on `main`)

| Item | Commit / row |
|---|---|
| `package_launch` → PASS ledger row (cook #3 exit 0, packaged boot 0 fatals, IoStore 3484-pkg, MainMenu load + viewport, canonical New Game slot created in packaged session) | ledger row 09-03 02:32 |
| `wardrobe_presentation_swap` STATE TIER → PASS row, 13/13 checks (PIE: fail-closed grant → equip → mesh identity `SK_Melusina_V2_Skirt` → negative control → re-equip → identity re-verify) + `05_skirt_equipped.png` | ledger row 09-03 04:04 |
| `klein_veil_import.py` loud-fail (unknown scalars/vectors abort with reflection-derived known set; existing-MI re-apply; save readback) + 2 latent fatals fixed (`true` literals; TextureCoordinate filter) | eba92b76, 20ae100a |
| Dreamstate MapsToCook removal (owner-approved) + verdict doc | 90b7898e |
| Cook runbook (NeverCook two-domain rule, engine MeshPartition quarantine + revert) | eba92b76 |
| Harnesses committed (evidence-standard gap: the 09-01 harness was never tracked) | 15cb02c9 |

Harness: `Tools/run_wardrobe_skirt_swap_proof.py` (outer driver) +
`C:\Users\froma\AppData\Local\Temp\opencode\skirt_proof_pie.py` (in-PIE proof; copy next
to the harness if not yet copied — **owed**).

## Root causes found

1. `Cos_Skirt_MelusinaV2` equip failed fail-closed because Skirt cosmetics carry **no
   UnlockRewardId → never granted**. Grant is the required first step; Accessories worked
   historically because its record carries `reward.first_resonance_echo`.
2. `Cos_ShorewakeDress` is not runnable: manifest `in_development`,
   `SK_DressShorewake.uasset` absent. `SK_ShorewakeDress_Magical` FBX was auto-imported
   today (reimport loop terminated by moving the source to `Imports/GarmentIntake/`) but
   lands under `/Game/Melodia/Characters/Melusina/Textures/Clothes/` — **mis-path**; the
   interchange intake convention is `Imports/` → Blender prep → Outfits folder.
3. The master re-import churn re-saved a large swath of tracked `.uasset`s (audio/texture
   packages). **Working tree has hundreds of modified .uasset files — do NOT commit, do
   NOT `git checkout -- .` (forbidden).** Owner review required.

## NEXT SESSION #1 — material wiring (owner-approved order: after captures)

Reflection-verified truth: `M_Master_Toon_Universal` already exposes
`AudioBassGain / AudioBeatGain / AudioMidGain / AudioTrebleGain / AudioReactAmount` —
the audio-bus Collection×Scalar pattern partially exists.

Spec keys missing (10, verified live — NOT the 7 from the stale audit):
`BassIntensity, BeatPulse, CymaticAmplitude, GlobalEmissiveBoost, GlobalSparkleIntensity,
Grazing_Rim_Boost, IridescenceIntensity, POM_StepCount, Toksvig_AntiAliasing_Weight,
WPO_Resonance_Scale`.

Decision owed before adding anything (duplicate-vocabulary rule):
- **Remap** `BassIntensity→AudioBassGain`, `BeatPulse→AudioBeatGain` in klein_veil spec
  (recommended) vs add duplicates.
- Add the remaining 8 as ScalarParameters with Landscape-master pattern
  (CollectionParameter reads live bus × ScalarParameter gain, multiplied) wired into the
  relevant feature chains — inspect the master graph first
  (`material_query` / blueprint get_graph_data), especially WPO + emissive chains.
- After wiring: rerun klein_veil (must apply cleanly now), `verify_baseline` (expect
  exactly Universal drift), **owner sign-off** → baseline refresh → `static_gates` row.

## Queued after wiring

- Look/value tier of `wardrobe_presentation_swap`: MI identity + gain-scalar CDO diff,
  save → full process restart → load → restore (extends the 09-01 roundtrip row).
- Captures (owner approved BOTH): flat exploration frame (asserts reactive channels read
  zero — bus-leak check) + music-clock-driven frame (reactive look). Feeds
  `world_field_bus_pie` + `gaeA_live_pie` pending_capture rows — coordinate with those lanes.
- Faraway Mother populate (5 build scripts) — was Claude's step 3, untouched this session.
- `SM_Rock` reference check before next cook; allowlist reflection check for stale
  Dreamstate travel id (see DREAMSTATE verdict doc).
