# Dash & Magpie — Native Integration Plan 2026-08-31

**Status:** ACTIVE (owner task 2026-08-31: "start directly integrating actual dash and magpie")
**SSOT:** `Docs/Research/AGENT_TOOLCHAIN_DISCOVERY_INDEX_2026-08-30.md` · `Docs/Research/EMERGING_3D_RENDERING_TOOLCHAIN_RESEARCH_2026-08-30.md`

---

## 0. Ground truth (verified, not assumed)

| Claim | Verdict |
|---|---|
| Polygonflow "Dash" plugin present in `Plugins/` | **NO** — not vendored, not installed. It is a **paid third-party UE marketplace plugin**; we cannot download it and must not fabricate it. |
| Magpie implementation present anywhere | **NO** — research/watch concept only, no code, no vendor. |
| What the repo DOES have for dressing/procedural | `PCGExtendedToolkit`, `ProceduralDungeon`, `ProceduralModelingToolkit`, `HoudiniEngine`, `GaeaUnrealTools`, `PCG` + `MelodiaPCGNarrativeChallengeBridgeComponent`, `MelodiaPCGWaterGameplayBridgeComponent`. |

**Therefore "integrating Dash and Magpie" means integrating their *capabilities and architecture* natively — not installing commercial/experimental binaries we don't have.** This is the only honest path, and it is explicitly what the SSOT recommends (Dash = a native editor dressing pass; Magpie = a simulation/visual separation signal).

---

## 1. Dash → native environment-dressing subsystem (`UMelodiaDressingSubsystem`)

**Dash's SSOT role:** "fast final human composition pass" — hero prop placement, physically-dropped debris, cables/vines/roads, scene cleanup around camera-critical areas. Trial priority B, editor-only, no shipping dependency.

**Native build (what we can actually ship):**

- `UMelodiaDressingSubsystem` (`UGameInstanceSubsystem`) — the "Dash-capability" pass:
  - `DressHeroClutter(AActor* CameraFocus, int32 Count, const FGameplayTag& Family)` — place tagged hero props from the dressing catalog at camera-critical positions around a focus actor (PCG-family reuse, not a new procedural authority).
  - `PhysicallyDrop(const TArray<AActor*>& Actors, float Restitution)` — drop loose debris under gravity (logs/rocks/field gear).
  - `RunCompositionCleanup(AActor* CameraFocus, float Radius)` — report/reduce props occluding camera-critical framing (composition-only, never deletes foreign assets — flags for owner).
  - Catalog-backed: `DA_MelodiaDressingCatalog` (DataAsset) keyed by `FGameplayTag` family → hero prop set, avoiding a 5th authority (reuses existing SM_/MI_ library + PCG tags).
- **Convergence-safe:** dressing is a *manual human art-pass* (Dash's role), distinct from PCG (scalable authored distribution) and Houdini (procedural systems). It does NOT create a new master, a new combat authority, or a `Content/_PROJECT/` write. It tags/places existing assets.
- **Pass condition (from SSOT):** a 20-minute dressing pass makes a PCG-generated test scene visibly more authored with no fragile plugin-only runtime deps → we validate the same on `L_KaleidoNave` or `L_FallenMoon`.
- **Editor-only, no shipping dependency** — consistent with Dash's B priority.

**Out of scope:** installing/calling the actual Polygonflow plugin (commercial, absent). If the owner later buys/licenses it, this subsystem is the native fallback/complement.

## 2. Magpie → promoted to scaffold: the simulation↔visual seam

**Magpie's SSOT role:** research/watch — "conventional engine retains gameplay/simulation state while a generative renderer produces visual frames." Separation of **simulation truth** from **visual truth**.

**Promotion (this task):** from WATCH/RESEARCH to **architecture scaffold**, NOT to a shipping renderer. A generative frame renderer is explicitly not a production dependency (determinism/latency/QA/platform). We build the *seam* that makes a future Magpie-style renderer possible without a parallel combat/gameplay authority.

**Native build:**
- `Docs/Research/MAGPIE_SEAM_ARCHITECTURE_2026-08-31.md` — the contract: authoritative `UMelodiaSimulationTruth` (world state: positions, HP, quest flags, rhythm grade) vs presentation `UMelodiaVisualRepresentationSubsystem` (what frames show). MelodiaCore already carries this doctrine ("presentation-only this phase") — Magpie formalizes the read contract.
- `UMelodiaVisualRepresentationSubsystem` (scaffold, presentation-only): exposes stable read accessors onto simulation truth (via `UMelodiaNarrativeSubsystem`/`UMelodiaRhythmCombatSubsystem`), NOT a second writer. A future generative renderer would consume these readouts as "visual truth" inputs — the same seam the audio-reactivity `MPC_Melodia_Palette` already uses for BeatPulse.
- **Guardrail:** this is a *read* seam. No runtime frame generation, no new authority, no second HUD writer. It exists so a future Magpie-style renderer can be swapped under the presentation layer without touching simulation.

## 3. Why this is the right integration (not a fake one)

1. **We cannot install Polygonflow Dash or a Magpie renderer** — they are commercial/experimental and absent. Claiming to "integrate" them as binaries would be fabrication.
2. **The SSOT explicitly defines the correct native integration:** Dash = editor dressing pass; Magpie = simulation/visual separation signal.
3. **Convergence doctrine:** both scaffolds are narrow, reuse existing authorities (PCG, MelodiaCore presentation, existing catalogs), and add no parallel masters / combat / HUD writer.
4. **Evidence standard:** each scaffold gets an offline probe + a live PIE validation (like `CaptureRender`), with ledger rows — never prose.

## 4. Delivery order (this window)

| # | Deliverable | Buildable now? |
|---|---|---|
| 1 | This decision doc | ✅ |
| 2 | `UMelodiaDressingSubsystem` (header + cpp) | ✅ code, build next closed-editor window |
| 3 | `Docs/Research/MAGPIE_SEAM_ARCHITECTURE_2026-08-31.md` | ✅ doc |
| 4 | `UMelodiaVisualRepresentationSubsystem` (header + cpp) | ✅ code, build next window |
| 5 | Offline probes (`Tools/test_dressing.py`, `Tools/test_visual_seam.py`) | ✅ code |
| 6 | Live PIE validation (dressing pass + seam readout) on `L_KaleidoNave` | next editor window |
| 7 | Ledger rows | after live proof |

**Hard rules:** one editor, no `Content/_PROJECT/` writes, no parallel masters, spec precedes mutation, batch saves `unattended:true`, no `git clean`/`checkout -- .`.