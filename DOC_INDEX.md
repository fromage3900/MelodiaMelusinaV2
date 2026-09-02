# Melodia — Documentation Index & Authority Map

**Front door for project documentation**  
**Last Updated:** 2026-09-02

---

## 1. Read in this order

| Priority | Document | Authority |
|:---:|---|---|
| **1** | [`README.md`](README.md) | Public/product front door: what Melodia is now. |
| **2** | [`Docs/Strategy/MELODIA_ENDLESS_JOURNEY_NORTH_STAR_2026-09-02.md`](Docs/Strategy/MELODIA_ENDLESS_JOURNEY_NORTH_STAR_2026-09-02.md) | **Canonical product vision:** evergreen single-player RPG, Volumes/Voyages, permanent vs renewable game, long-term persistence philosophy. |
| **3** | [`Docs/Strategy/MELODIA_CHAPTER_TIER_AND_VOLUME_ARCHITECTURE_2026-09-02.md`](Docs/Strategy/MELODIA_CHAPTER_TIER_AND_VOLUME_ARCHITECTURE_2026-09-02.md) | **Canonical content structure:** Reveries/Episodes/Chapters/Movements/Monolith Events/Volumes; working 50+ Chapter Volume-I grid. |
| **4** | [`Docs/Strategy/MELODIA_EVERGREEN_CONTENT_AND_GIFT_MODEL_2026-09-02.md`](Docs/Strategy/MELODIA_EVERGREEN_CONTENT_AND_GIFT_MODEL_2026-09-02.md) | **Canonical long-term update model:** Gifts, Reveries, Voyages, no-FOMO default, optional online manifest later. |
| **5** | [`CURRENT_STATE.md`](CURRENT_STATE.md) | **Implementation truth now:** runtime ownership, proven baseline, active closure work. |
| **6** | [`TODO.md`](TODO.md) | **Production queue:** current closure work, reusable Chapter lane, Volume-I content roadmap. |
| **7** | [`SYSTEM_MAP.md`](SYSTEM_MAP.md) + [`DATA_FLOW.md`](DATA_FLOW.md) | Stable runtime architecture and state lifecycle. |
| **8** | [`QUICKSTART.md`](QUICKSTART.md) | Setup, tests, editor/package workflow. |
| **8a** | [Laptop workstation setup and offload plan](Docs/Plans/LAPTOP_WORKSTATION_SETUP_AND_OFFLOAD_2026-09-02.md) | Second-machine onboarding, RAM profile, offload lanes, and handoff gates. |
| **9** | [`_VERTICAL_SLICE_SCOPE.md`](_VERTICAL_SLICE_SCOPE.md) + [`TEST_READY.md`](TEST_READY.md) | P0 proof scope and bounded test evidence. |

---

## 2. Important paradigm distinction

The project has two different truths that must not be conflated:

### Product truth
Melodia is an **evergreen single-player journey** that may grow for years through complete Volumes, smaller Reveries, optional Gifts, and larger Voyages.

### Production truth
The immediate job is still **runtime closure**. The existing P0 / First Dream + Sea Above route is the current integration proof. Future scale is not permission to bypass persistence, packaged proof, stable authority, or chapter validation.

---

## 3. Historical docs vs current authority

Older documents remain valuable evidence and design history, but several old statements are no longer product-authoritative:

- the finite **~12h / four-movement** estimate in `Docs/FULL_GAME_LOOSE_SCOPE_2026-07-31.md` is a historical north-star snapshot;
- the **“every Chapter executes the exact same six-phase loop”** claim is superseded as content design;
- the six-phase loop remains a useful **P0 full-stack golden test**;
- P0 gate/test counts remain evidence for their captured baseline, not universal shipping certification for future Chapters.

Do not delete historical handoffs simply because the product framing evolved. Mark/interpret them through the current strategy docs.

---

## 4. Runtime architecture authorities

- TurnBased JRPG / Phoenix: combat skeleton, party/turn/target/damage/result/inventory stock ownership.
- `UMelodiaNarrativeSubsystem` + QuillScript: narrative progression, intents, flags, consequences, checkpoints.
- Melodia rhythm (`MelodiaCore`, rhythm integration): execution/performance layer over selected actions.
- `UMelodiaWardrobeSubsystem`: wardrobe/equipped ownership and gameplay relationship/capability state.
- Convergence: interpretation/glue; must not duplicate owner truth.
- `UMelodiaUIBridgeSubsystem`: single-writer UI ownership.
- Canonical save/narrative record: forward-compatible durable history.

Relevant architectural records include `Docs/ORCHESTRA_CONVERGENCE_2026-08-20.md`, `Docs/ORCHESTRA_CONTRACT_2026-08-20.md`, and the current runtime-persistence closure plan.

---

## 5. Chapter and progression docs

### Current/reusable contracts
- `specs/progression/`
- `Docs/Plans/REUSABLE_CHAPTER_VALIDATION_SYSTEM_2026-08-31.md`

### Current major content lanes
- First Dream / Sea Above P0 package
- Shorewake transition
- Mara / Faraway Mother
- God That Molts planning (needs formal progression package)
- Horizon Eater planning/spec (needs sequence reconciliation after God That Molts)
- Movement-IV frontier: House of Measures / Seam Oracle / Last Dress

The working 50+ Chapter grid is an **authoring scaffold**, not a requirement that every title or number survive production unchanged.

---

## 6. Testing and evidence

- `run_tests.ps1`
- `Tools/run_contract_tests.py`
- `Tools/verify_p0_offline.py`
- `Tools/test_melodia_mcp.py`
- `Tools/test_e2e_melusina_release.py`
- `Saved/gate_ledger.json` where available in the authoring/runtime evidence environment

A source file or asset existing is not proof of runtime completion. Preserve the distinction between source presence, offline contract proof, live proof, restart proof, and packaged proof.

---

## 7. Toolchain and research

Before proposing another emerging tool, read the existing toolchain discovery/master indexes. The production rule remains:

> **Adopt only when it produces visibly better Melodia per hour without creating a more expensive maintenance system.**

The Musical World Compiler is an offline-authoring lane; Unreal/MelodiaCore remains runtime gameplay authority.

---

## 8. Legal / provenance

- [`LICENSE`](LICENSE)
- [`Docs/CREDITS.md`](Docs/CREDITS.md)
- [`Docs/SOURCES_MATRIX.md`](Docs/SOURCES_MATRIX.md)
- [`SECURITY.md`](SECURITY.md)
- [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md)

---

**Documentation rule:** front-facing docs describe current product/production truth; dated handoffs preserve evidence and history.
