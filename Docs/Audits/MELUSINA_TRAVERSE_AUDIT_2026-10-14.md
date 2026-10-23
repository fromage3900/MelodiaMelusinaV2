# Melusina Traverse Runtime + Editor-Workflow Audit — 2026-10-14

**Stamp:** 2026-10-14 ET (America/Toronto)
**Checkout tip:** `C:\EnvironmentPortfolio\BS_GodFile`
**Lens:** Triple-A locomotion/traversal standard for the canonical Melusina pawn, plus the editor import/retarget/bind workflow that feeds it.
**Rules:** read-only audit — no `.uasset`/`.umap` mutation, no recompile, no runtime change. Runtime improvement actions listed here are **proposals** requiring a live editor (Monolith/Claireon on 9316) and an Act-mode session.

**Method:** source-read of the traversal/anim C++ and the tracked Docs (KineFX convergence, Triple-A animation pipeline, retarget research, CURRENT_STATE). Chooser/MotionWarping/cloth presence confirmed by repo-wide grep of `Plugins/MelodiaCore/Source` and `Source/BS_GodFile` (excluding `Intermediate`).

---

## 0) Naming disambiguation — "Melodia Traverse"

**"Melodia Traverse" is NOT a Claireon/Monolith tool.** `ClaireonTool_ChooserTraverse.h/.cpp` is a generic Chooser-table graph walker in the Claireon editor plugin and is unrelated to character traversal.

The real system is the **Melusina traversal/locomotion stack** on the canonical pawn `BP_MelusinaJRPGCharacter`, split across two modules by a deliberate dependency inversion (MelodiaCore cannot depend on BS_GodFile; BS_GodFile already depends on MelodiaCore).

| Layer | Class / file | Module | Role |
|---|---|---|---|
| Traversal authority | `UMelodiaTraversalComponent` (`Source/BS_GodFile/MelodiaIntegration/MelodiaTraversalComponent.h/.cpp`) | game | Glide / dash / swim / dive / bubble-sprint, stamina + breath, variable-height jump (coyote-time + jump-buffer), rotation policy, roll montage (`AM_Melusina_Roll`), wing presentation, water Niagara/audio/post-process bridges |
| Capability gate | `UMelodiaTraversalCapabilityRegistry` + `IMelodiaTraversalCapabilityProvider` (`MelodiaTraversalCapabilityProvider.h`) | game | **Native** capability ids `capability.melodia.{glide,dash,swim,sail}`; single provider (MelodiaWardrobe); fail-closed `RequestTraversalMode` |
| Anim reader | `UMelodiaLocomotionAnimInstance` (`Plugins/MelodiaCore/Source/MelodiaCore/MelodiaLocomotionAnimInstance.cpp`) | MelodiaCore | Reads glide/sprint via the interface, drives blendspace/state machine |
| State contract | `IMelodiaTraversalStateProvider` (`MelodiaSharedAuthorityInterfaces.h:77-99`) | MelodiaCore | `IsGliding()` / `IsSprinting()` query surface |
| Secondary motion | `UMelodiaHairComponent` (KawaiiPhysics) | game | Runtime hair; **skirt cloth is baked offline** (Houdini Vellum→VAT), not runtime ChaosCloth |
| Clip integrity | `MonolithMelusinaClipGuard` (`Plugins/Monolith/Source/MonolithAnimation/Private/MonolithMelusinaClipGuard.cpp`) | Monolith | Enforces the rest-scale contract before any live bind |

**Structural verdict:** well-architected. Clean authority separation, interface-based cross-module access (no circular dependency), fail-closed capability gating, single-writer presentation handoff (`SetWingPresentationOwnedExternally` → `UMelodiaMagicalTransformComponent`). The gaps are in **finish, proof, and two missing runtime techniques** — not in structure.

---

## 1) Runtime stack — Triple-A-grade vs. missing

### ✅ Already strong
- **Four-axis doctrine** (`Docs/TRIPLE_A_MELUSINA_ANIMATION_PIPELINE_2026-08-18.md`): Locomotion / Interaction / Presentation / Progression axes kept strictly separate; presentation can never move the character. Enforced in code comments and the capability registry. This is the correct AAA separation.
- **Locomotion feel is authored, not accidental:** `GlideGravityScale 0.11`, `GlideSinkEaseRate 5.0`, `GlideActivationLiftSpeed 130`, `GlideActivationForwardBoost 115`, coyote-time `0.12s`, jump-buffer `0.15s`, variable-height jump hold `0.25s`, dash impulse `900` + cooldown `0.7s` cadence, `NormalWalkSpeed 380` / `SprintSpeed 630`. Real game-feel knobs with clamps.
- **Retarget chain is correct and hardened:** `SK_Melusina_Skeleton → IK_Melusina_Body_Current → RTG_Mocap_FullBody_to_Melusina / RTG_BlenderARP_to_Melusina`, with the ClipGuard rest-scale contract (root scale 1, `spine_y ≈ −12.84`, arm segments `15.774 / 28.561 / 28.615`).
- **ClipGuard is a real regression gate** (465-track readback, endpoint residual, arm-segment measurement) — the single most valuable piece of the pipeline; it caught the live Glide root-scale-100 regression.
- **Capability vocabulary is single-sourced** (`MelodiaTraversalCapabilityProvider.h`), eliminating the prior raw-string-literal drift between `MelodiaTraversalComponent.cpp` and `MelodiaWardrobeSubsystem.cpp`.

### ⚠️ Gaps against Triple-A standard
1. **MotionWarping is enabled but completely unused** — repo-wide grep of the two C++ modules returns **zero** references to `MotionWarp*`, `WarpTarget`, or `AnimationWarp`. The owed **"boot contact"** gate (foot planting on stairs/slopes/ledges) is exactly what MotionWarping + foot-IK solves. `CURRENT_STATE.md` explicitly lists *"no running/ledge/slope/stair proof."* **Highest-value runtime addition.**
2. **No IK foot-placement / ground-alignment pass** in the locomotion chain. The blendspace + root motion carry everything today, which is why slope/stair contact is unproven.
3. **Chooser is not used in native traversal** — grep returns **zero** C++ references. Chooser lives only in AnimBP graphs and in the Monolith/Claireon editor tooling. For AAA, the Chooser/state tables inside `ABP_Melusina_Current` should be audited and fingerprinted (requires a live Monolith graph read; it is a binary `.uasset`).
4. **No runtime cloth** — the skirt is an offline Vellum/VAT bake. A legitimate AAA choice (deterministic, cheap), but it means **no reactive secondary motion during dash/glide**. Optional, not a defect.
5. **Traversal is not GAS-driven** (owner decision — ACFU is a trial harness only; canonical pawn stays `BP_MelusinaJRPGCharacter`). GAS/gameplay abilities are confined to the ACF trial harness. Traversal deliberately uses a native capability-provider interface instead. **Correct per canon — flag for the FLOW/SEQUENCE hybrid convergence, do not "fix" now.**

---

## 2) Editor workflow — current pipeline vs. Triple-A standard

### Current chain
```
Blender stage blend (NLA clip) → export_melusina_idle_v22.py (armature-only FBX, -Z/Y, baked)
 → remap_arp_fbx_to_ue.py (dots→underscores, ×100, sidecar contract "ue_import": false)
 → guarded import onto SOURCE skeleton (spine_y cm-probe ≈ −12.84)
 → IK-retarget (RTG_BlenderARP_to_Melusina) → ClipGuard validate
 → bind via scripts/bind_and_verify.py (set_state_animation → compile → attrib -R → save → mtime + re-read)
 → evidence: Saved/Audit/<topic>_<date>.json + capture frames + real-input PIE
```
KineFX side: `AnimationDoctor normalization → KineFX motion/transition polish → character finishing → Vellum/VAT → Copernicus → UE proof` (`Docs/Houdini/MELODIA_ANIMATION_OUTFIT_FINISHING_CONVERGENCE_2026-10-07.md`).

**Tooling surface:** Monolith (editor MCP — `animation_query`, `blueprint_query`, `chooser_query`, retarget, `capture_anim_frames`) + Claireon (editor automation — PIE, save, `uobject_inspect`), single listener on **9316**.

### ✅ Strong
- **Hard-won failure rules are codified** (skill `melusina-blender-handkeyed-import`): never bind direct-to-skeleton (explodes); one `capture_anim_frames` per editor session (Monolith `!IsRooted()` crash); LFS read-only `.uassets` → `attrib -R` before save; `save_asset` lies → verify via mtime + re-read; one editor / one MCP surface; **compile WIPES CDO overrides** → order is always `compile → set_cdo → save`.
- **Duplicate-only discipline:** fixes land on a `_Candidate` duplicate, never the original mocap clip (the Glide fix followed this exactly).
- **Evidence standard is rigorous** (skill `melodia-p0-closeout` §6): gate ledger rows, JSON assertion reports, committed verifiers, "probe-injected calls are not play evidence."

### ⚠️ Gaps
1. **AnimationDoctor is local-first / not on Git main** — no tracked `HDA_Melodia_AnimationDoctor*.hda`, HIP, or PASS receipt. The normalization step that feeds the whole chain is not version-controlled. **Triple-A requires the Doctor to be a tracked, reproducible artifact** (the convergence doc already flags this as a recovery risk).
2. **No automated slope/stair/ledge contact harness.** Automation currently **fails on PCG invalid-bounds errors**, and only flat simulated-input PIE is proven; the physical-input G1–G5 gates are owed.
3. **Chooser/state tables in `ABP_Melusina_Current` are unaudited** — no committed fingerprint of the anim-graph Chooser/transition content (the `bp_fingerprints.json` baseline covers BP regression, not anim-graph Chooser data).
4. **Shoulder-silhouette proof is owed** — the ClipGuard proves per-key arm lengths, not the blended visual result; discrete keys "do not prove blended shoulder silhouette" (per the 2026-10-09 review note).

---

## 3) Prioritized recommendations

Respecting canon (canonical pawn `BP_MelusinaJRPGCharacter`, no reparent) and the hard-won rules above.

### P0 — close the owed gates (highest value, lowest risk)
1. **Add a MotionWarping + foot-IK pass** to the locomotion chain for boot contact on slopes/stairs/ledges. Author warp targets per transition; IK planting in the AnimBP post-process. Directly closes the owed **boot-contact** + **ledge/slope/stair** gates and uses an already-enabled-but-unused plugin. *Requires live editor (Monolith/Claireon) + Act mode.*
2. **Track AnimationDoctor on Git main** (HDA/HIP + PASS receipt) so the normalization step is reproducible, not local-only.
3. **Build a physical-input G1–G5 harness** that survives PCG invalid-bounds (fix the PCG bounds first, then run real-key PIE), producing ledger rows + JSON assertion reports.

### P1 — finish + proof
4. **Audit + fingerprint the Chooser/state graph** in `ABP_Melusina_Current` via a live Monolith `animation_query`/`chooser_query` read; commit the fingerprint as a regression baseline.
5. **Shoulder-silhouette proof:** capture blended-pose frames (not just per-key lengths) and add a visual assertion to the ClipGuard evidence.

### P2 — optional polish (do not expand scope without an owner pivot)
6. Reactive skirt secondary motion during dash/glide — only if the owner wants runtime cloth; the current offline Vellum/VAT bake is a valid AAA choice.
7. Consolidate traversal capability vocabulary with the future GAS/ACFU convergence — **deferred** (ACFU is harness-only per canon).

---

## 4) Hard constraints every change must honor
- Canonical pawn stays `BP_MelusinaJRPGCharacter` — **no reparent** to an ACF child.
- **Duplicate-only** clip edits — never mutate the original mocap clip.
- **ClipGuard rest-scale contract** must pass (root scale 1, `spine_y ≈ −12.84`, arms `15.774 / 28.561 / 28.615`).
- **Single-authority writers** — no second Magical-Transform writer, no second HUD writer, no direct OSC → `MPC_Cymatics_Driver`.
- **One editor, one MCP surface** (9316); never run two graph-mutation surfaces in one session.
- **Evidence = ledger rows + JSON assertion reports**, never prose; probe-injected calls are not play evidence.
- Commit with an **explicit pathspec** (`git add <exact file>` + `git commit -- <exact file>`) — this repo's index routinely holds other lanes' work.

---

## 5) Key source references
- `Source/BS_GodFile/MelodiaIntegration/MelodiaTraversalComponent.h/.cpp`
- `Source/BS_GodFile/MelodiaIntegration/MelodiaTraversalCapabilityProvider.h`
- `Plugins/MelodiaCore/Source/MelodiaCore/MelodiaSharedAuthorityInterfaces.h` (`IMelodiaTraversalStateProvider:77-99`)
- `Plugins/MelodiaCore/Source/MelodiaCore/MelodiaLocomotionAnimInstance.cpp`
- `Plugins/Monolith/Source/MonolithAnimation/Private/MonolithMelusinaClipGuard.cpp`
- `Docs/TRIPLE_A_MELUSINA_ANIMATION_PIPELINE_2026-08-18.md`
- `Docs/Research/UE_RETARGET_PIPELINES_LONG_TERM_2026-08-15.md`
- `Docs/Houdini/MELODIA_ANIMATION_OUTFIT_FINISHING_CONVERGENCE_2026-10-07.md`
- `Docs/Production/BLENDER_HANDKEYED_ANIM_IMPORT_PIPELINE_2026-08-22.md`
- Skills: `.agents/skills/melusina-blender-handkeyed-import`, `melodia-p0-closeout`, `melodia-p0-loop`
- `CURRENT_STATE.md` (Glide regression fix; simulated-input PIE; owed shoulder/boot/G1–G5)
