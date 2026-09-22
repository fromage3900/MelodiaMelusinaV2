# Melusina AAA Lookdev Grandmaster Plan v7 — the Gating List (2026-09-22)

> **For Hermes:** This plan supersedes v6's W1/W2 ordering and folds the accessory
> convergence redirect (PR #292, owner-amended). Authority chain: owner's final
> gating notes (2026-09-22, verbatim in §1), showcase-day lock (`5e06b981f`),
> redirect commit (`054fc126e`), and the 2026-09-14 lookdev closeout docs
> (`Docs/Plans/MELUSINA_LOOKDEV_CLOSEOUT_2026-09-14.md`,
> `Docs/Handoffs/SESSION_CLOSEOUT_2026-09-14.md`,
> `Docs/Plans/KAWAII_GAP_STUDY_2026-09-14.md`).
> The Choral Sheep lane belongs to the owner tonight (showcase lock item 1); this
> plan is the Melusina lane only.

## 0. Staging decision (owner delegated the choice)

**Headless Blender first, live MCP second.**
- Deterministic rig/bake/export work runs **headless on COPIES**
  (`blender -b <copy> --factory-startup`, evidence JSON per run) — it does not
  contend with the owner's GUI Blender session, and every step is reproducible.
- Editor-resident truth (ABP nodes, physics assets, PIE reads, captures) runs
  **live via Monolith** (:9316, health chain first, single writer, duplicate maps
  before staging). Monolith refused connections at 23:0x on 09-22 — re-run the
  health chain (`netstat :9316` → PID reconcile → `curl /health`) before W0; a
  refused port with the process alive = wedged game thread, diagnose via
  `MODAL_OPEN` grep, never kill on a modal.
- No C++ change is required by any wave below. Closed-editor builds stay reserved
  for the deferred Jump lane.

## 1. The gating list (owner, 2026-09-22 — verbatim order preserved)

1. **Multi-segment hair re-rig** — 3–5 joints per strand, weights redistributed,
   still on `SK_Melusina_Hair_Skeleton`. THE beauty blocker in the render-readiness
   note. NOT "merge hair onto the body skeleton" (Decision 010's long-term line).
   **Pattern B stays.**
2. **Root-motion re-export** of the locomotion clips, then a measured re-place of
   `BS_Melusina_Locomotion_Hybrid`. First unblock in that note. Blender, then UE.
3. **Cornea re-weight onto `DEF_eye.L/R`**, and the finger-controller decision once
   the owner picks re-weight or export config.
4. **Jump-on-press / JumpMaxHoldTime / glide-from-held-fall** — scheduled for a
   closed editor. NOT part of the hair proof unless the owner adds it to the same
   build.
5. **Sleeve and hem dangle bones on `SK_Melusina_Skeleton`**, then ONE Kawaii node
   on `ABP_Melusina_Current`. Pattern A. The shirt follow is already correct.
6. **Enemy visibility, then an environment under the beauty camera.** Last mile for
   portfolio frames. Do NOT retune hair or skirt while dressing the set.
7. **Head collision** — the 2026-09-14 gap stays open unless the PIE read shows
   otherwise: hair skeleton has no head bone, `SK_Melusina_FIXED_Hair_PhysicsAsset`
   is not the sim mesh, and a single Outer sphere on `hair_root` was the old helmet
   suspect. Inner sphere per the vendor if that sphere is still jailing the scalp.
   Not a damping change.
8. **`a.AnimNode.KawaiiPhysics.Debug` weight-versus-eval verdict was never
   recorded.** Record it.
9. **`SequencePlayer_0` in the hair ABP had no pose output on 2026-09-14.**
   Re-read only. Do NOT rewire it in this pass.
10. **FLIP fluid_surface, geometry cache, Copernicus maps, and PearlWeave.**
    Separate lanes. UVs and the Nikki fabric bar already failed assignment.
11. **Cook, the other five levels, and Niagara bytecode** — last.
12. **Skirt stays the standalone `Portfolio_R2_Skirt` actor.** Its skeleton is not
    the wardrobe skeleton.

## 2. Hard boundaries (violation = stop)

- Hair stays on `SK_Melusina_Hair_Skeleton` (Pattern B). No Decision-010 merge.
- Sleeves/hem are Pattern A: bones on `SK_Melusina_Skeleton` + one Kawaii node on
  `ABP_Melusina_Current`. The shirt follow is correct — untouched.
- `Portfolio_R2_Skirt` is a standalone actor, never a wardrobe slot.
- `SequencePlayer_0`: read-only in this pass.
- No hair or skirt tuning during W6 set dressing.
- FLIP / Copernicus / PearlWeave are separate passes with their own evidence; the
  failed UV assignment is their ENTRY GATE, not a mid-stream patch.
- Duplicate-before-change on every asset; guarded FBX lane; Recipe 15 (fingerprint
  → mutate → compile → assert → save; never compile between CDO set and save);
  WaterHair MI stays HANDS OFF (19 overrides, other lane — 09-14 verdict).

## 3. Waves

### W0 — Truth passes (live MCP, ~30 min, do first)
1. Record the missing verdict: `a.AnimNode.KawaiiPhysics.Debug` weight-versus-eval
   on the hair ABP → `Saved/Audit/melusina_hair_rerig_20260922/kawaii_weight_vs_eval.json`.
2. Re-read `SequencePlayer_0` pose output (expected: still none; record, no rewire).
3. Head-collision PIE read: enumerate the hair skeleton's bones (expect no head
   bone), confirm which physics asset the sim actually uses, probe the `hair_root`
   Outer sphere extent vs scalp. Verdict JSON decides W1's collision config
   (Inner sphere per vendor iff the scalp is jailed).

### W1 — Multi-segment hair re-rig (THE beauty blocker; headless → UE, M/L)
1. Headless, on a copy: add 3–5 joints per strand to `SK_Melusina_Hair_Skeleton`
   (length-tiered: long strands 5, mid 4, short 3), redistribute weights by curve
   proximity with falloff; keep `hair_root` the sole root.
2. Rebuild the hair physics asset for the new chain; apply W0.3's verdict on the
   collision spheres (Inner per vendor iff jailed; never a damping change).
3. Export via the guarded FBX lane → UE import → re-run the W0.1 verdict read
   (post-re-rig numbers, properly recorded this time) → 30 s PIE film vs the
   2026-09-14 baseline (`Saved/PIE/melusina_hair_20260914`) → owner names the
   symptom delta. No physics tuning without a named symptom (standing rule).

### W2 — Root-motion re-export → measured blendspace re-place (first unblock; Blender → UE, M)
1. Headless re-export of the locomotion clips WITH root motion via the
   `Tools/mocap/` lane; record measured speeds per take.
2. Re-place `BS_Melusina_Locomotion_Hybrid`: dedupe samples; `rate_scale =
   controller_speed / measured_speed` per state (GlideForward measured 217 cm/s);
   leave the in-place axes untouched.

### W3 — Cornea + finger (S–M, gate inside)
1. Cornea re-weight onto `DEF_eye.L/R` (headless copy; blink drives must still win).
2. Finger controller: **owner gate** — re-weight vs export config. Execute only the
   picked branch.

### W4 — Sleeve/hem dangle, Pattern A (Blender → UE, M)
1. Dangle bones on `SK_Melusina_Skeleton` (headless copy; sleeves + hem only).
2. ONE Kawaii node on `ABP_Melusina_Current` (live MCP; Recipe 15). Shirt follow
   untouched.

### W5 — Set dressing for the portfolio frames (live MCP, after W1 + W2 land)
- Enemy visibility fix, then environment under the beauty camera. Height-aware,
  raycast-snapped placement, CanonicalLandscape only. **No hair/skirt retune while
  dressing.**

### W6 — Hero-look convergence capture (the R0 fold-in; live MCP; tonight if W1–W2 land)
1. Regalia: v5 U1–U3 import → `/Game/Melusina/FX/Regalia20260922/` (Nanite wings ON,
   rings OFF, collision NONE, bounds gate ~230 UU) → sockets `FX_WingRoot` /
   `FX_RingStack` on the skeleton asset → attach to the live actor and tag
   `MelodiaWings` / `MelodiaAccessory` (existing `UMelodiaMagicalTransformComponent`
   seam; `SnapToPhase(Revealed)` for a steady pose; rings' counter-rotation via the
   narrowest proven seam — check `MelodiaResonantPassageComponent` BEFORE any adapter).
2. Skirt stays the standalone `Portfolio_R2_Skirt` actor — bound as itself, never a
   slot. Lash pair re-verify/respawn (bounds eye midpoint (−0.43, 31.4, 155.2),
   scale 6) — carried from L1.
3. Duplicate the capture map first (`..._MFX_20260922`); original never saved.
4. Evidence: PIE `HighResShot` + JSON (socket transforms, slot states, reveal phase)
   = the cohesive hero render state.

### W7 — Separate fabric lanes (headless; sequenced AFTER W1–W4; not tonight)
- FLIP `fluid_surface` + geometry cache; Copernicus maps; PearlWeave — three
  separate passes, each with its own evidence. **Entry gate for all three: the UV
  re-assignment work (the Nikki fabric bar already failed assignment — fix UVs
  first or nothing downstream reads correctly).**

### W8 — Deferred (owner-gated / last)
- Jump-on-press / JumpMaxHoldTime / glide-from-held-fall (closed editor; owner adds
  explicitly). Cook + the other five levels + Niagara bytecode. World-Compiler
  garment domain (R3) and Universe Foundry merge (parked by the showcase lock).

## 4. Owner gates

| Gate | Question | Default if silent |
|---|---|---|
| G-1 | Finger controller: re-weight or export config? | wait |
| G-2 | Hair re-rig joint counts per length tier (3/4/5 as proposed)? | 3/4/5 by strand length |
| G-3 | Add the Jump lane to this build? | no |
| G-4 | Hero capture go/no-go after the W1 film | owner eyes on the film |

## 5. Carried, not gating (do not let rot)
- Vein fix + plans + convergence plan: merged (PRs #290–292). CURRENT_STATE rewrite
  landing: still uncommitted (W0.3 of v6, owner word pending).
- A3 bow/arrow defects ×3, L2 T-pose/anim-class fix: after W2 (same editor session
  family, separate evidence).
- `CURRENT_STATE.md` remains the only status authority; wave completion is recorded
  there in the same commit as the work.
