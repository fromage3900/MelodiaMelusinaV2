# ♬ Melodia — Documentation Score Map

**Last updated:** 2026-09-02

> Front-facing docs tell the current truth. Dated handoffs keep the memory. Research is allowed to be weird. Runtime ownership is not. ♪

---

## 𝄞 Start here — in this order

| Order | Read this | Why |
|:---:|---|---|
| **♪ 1** | [`README.md`](README.md) | What Melodia is, in plain language. |
| **♫ 2** | [`Docs/Strategy/MELODIA_ENDLESS_JOURNEY_NORTH_STAR_2026-09-02.md`](Docs/Strategy/MELODIA_ENDLESS_JOURNEY_NORTH_STAR_2026-09-02.md) | The game-as-a-place / endless-journey north star. |
| **♬ 3** | [`Docs/Strategy/MELODIA_CHAPTER_TIER_AND_VOLUME_ARCHITECTURE_2026-09-02.md`](Docs/Strategy/MELODIA_CHAPTER_TIER_AND_VOLUME_ARCHITECTURE_2026-09-02.md) | Reveries, Episodes, Chapters, Movements, Monolith Events, Volumes. |
| **𝄞 4** | [`Docs/Strategy/MELODIA_EVERGREEN_CONTENT_AND_GIFT_MODEL_2026-09-02.md`](Docs/Strategy/MELODIA_EVERGREEN_CONTENT_AND_GIFT_MODEL_2026-09-02.md) | Gifts, mail, archives, Voyages, and the no-FOMO rule. |
| **♪ 5** | [`CURRENT_STATE.md`](CURRENT_STATE.md) | What exists and what can actually be claimed today. |
| **♫ 6** | [`TODO.md`](TODO.md) | The current production score. |
| **♬ 7** | [`SYSTEM_MAP.md`](SYSTEM_MAP.md) + [`DATA_FLOW.md`](DATA_FLOW.md) | Who owns what and how state moves. |
| **𝄞 8** | [`QUICKSTART.md`](QUICKSTART.md) | Setup, tests, editor, browser labs, package flow. |
| **♪ 8a** | [`Docs/Plans/LAPTOP_WORKSTATION_SETUP_AND_OFFLOAD_2026-09-02.md`](Docs/Plans/LAPTOP_WORKSTATION_SETUP_AND_OFFLOAD_2026-09-02.md) | Second-machine onboarding, measured hardware profile, offload lanes, and handoff gates. |
| **♫ 9** | [`_VERTICAL_SLICE_SCOPE.md`](_VERTICAL_SLICE_SCOPE.md) + [`TEST_READY.md`](TEST_READY.md) | P0 scope + bounded evidence. |

If you are an agent: **do not start by searching every old handoff.** Read the current front door first, then follow links into the system you are actually touching.

---

## ♪ Two truths that should never get mixed up

### The dream

Melodia is an evergreen single-player journey. A Volume can finish emotionally, then the game can later receive more Chapters, Reveries, Gifts, Voyages, creatures, outfits, impossible places, or whole new Volumes.

### The job today

Close the runtime.

P0 / First Dream + Sea Above is the current integration proof. Future scale does not excuse broken persistence, duplicate rewards, unclear ownership, or a package that cannot survive restart.

**Big world, boring contracts. Both matter.**

---

## ♫ Runtime authority map

| Truth | Owner |
|---|---|
| battle turns / targets / stock action results | Phoenix / TurnBased JRPG |
| narrative intents / flags / checkpoints / consequences | `UMelodiaNarrativeSubsystem` + QuillScript |
| rhythm timing / note-highway execution | Melodia rhythm / `MelodiaCore` |
| owned + equipped wardrobe state | `UMelodiaWardrobeSubsystem` |
| cross-system interpretation | Convergence |
| player-facing UI writes | `UMelodiaUIBridgeSubsystem` |
| durable Melodia memory | canonical save + narrative record |

Useful architecture records:

- `Docs/ORCHESTRA_CONVERGENCE_2026-08-20.md`
- `Docs/ORCHESTRA_CONTRACT_2026-08-20.md`
- current runtime-persistence closure plan

---

## ♬ Chapter / journey documents

### Reusable contracts

- `specs/progression/`
- `Docs/Plans/REUSABLE_CHAPTER_VALIDATION_SYSTEM_2026-08-31.md`

### Current major lanes

- First Dream / Sea Above;
- Shorewake + Starskiff departure;
- Mara / Faraway Mother;
- God That Molts — still needs a formal progression package;
- Horizon Eater — needs ordering reconciliation after God That Molts;
- House of Measures / Seam Oracle / Last Dress of the Sea.

The 50+ Chapter Volume-I grid is an **arrangement scaffold**. It is not proof that every current title or number must survive production.

---

## 𝄞 Browser + tool laboratories

These are part of the repository on purpose. They let ideas become interactive quickly without inventing another Unreal authority.

### ♪ Cymatic Sanctuary

`Docs/Tools/puzzle-sandbox/index.html`

12-instrument Three.js Music-as-Key sandbox with phrase gates, watercolor/toon presentation, bloom, particles, and prototype JSON export.

### ♫ MusicKey3D

`Prototypes/Web/MusicKey3D/`

World-interaction lab for music nodes, phrase readability, barrier feedback, and Melodia's illustrative browser style.

### ♬ Traveling Folio

`Prototypes/Web/MelodiaFolio3D/`

3D UI / Starskiff post / Thread navigation / repository-model turntable.

`mara.html` is the more stylized Mara-art-direction variant.

**Browser prototype rule:** emit ideas, view models, proposed schemas, and UI intents. Never quietly become gameplay authority.

---

## ♪ Testing / evidence

Useful roots:

- `run_tests.ps1`
- `deploy/test_laptop_workstation.ps1` — staged laptop Smoke/Fast/Contracts/Build/UE acceptance runner.
- `deploy/inspect_workstation.ps1` — local hardware/toolchain profile report.

- `Tools/run_contract_tests.py`
- `Tools/verify_p0_offline.py`
- `Tools/test_melodia_mcp.py`
- `Tools/test_e2e_melusina_release.py`
- `Saved/gate_ledger.json` where it exists in the evidence environment

Remember the ladder:

```text
source exists
   ≠
offline contract passes
   ≠
live runtime proven
   ≠
restart proven
   ≠
packaged build proven
```

Say which one you have.

---

## ♫ Git-health interpretation

As of the 2026-09-02 health pass:

- persistence PR #54 contains useful work but is too stale to merge wholesale; reapply it from current `main`;
- site / Three.js PR #61 is cleanly based but broad; review it as a large Wix snapshot and reconcile Three.js versions before promotion;
- very large older research PRs increasingly function as **archives to extract from**, not automatic merge candidates.

Do not let “open PR” become synonymous with “current authority.”

---

## ♬ Historical documents

Older docs are allowed to disagree with current strategy because they preserve how the project got here.

Superseded examples include:

- the old finite `~12h` loose-scope estimate;
- the idea that every Chapter must run the same six-phase P0 loop.

Keep the history. Read it through the current north-star docs.

---

## ♪ Toolchain / research

Before adding another tool, check the current research/discovery indexes.

The rule remains:

> **Adopt a tool only when it makes visibly better Melodia per hour without creating a more expensive maintenance system.**

Music may author geometry offline. Houdini may author impossible evidence. Browser toys may test interaction. Unreal remains the game.

---

## 𝄞 Legal / provenance

- [`LICENSE`](LICENSE)
- [`Docs/CREDITS.md`](Docs/CREDITS.md)
- [`Docs/SOURCES_MATRIX.md`](Docs/SOURCES_MATRIX.md)
- [`SECURITY.md`](SECURITY.md)
- [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md)

---

> **Front door = current truth. Handoff = memory. Research = possibility. Runtime = authority.** ♫
