# Magpie Seam Architecture — simulation truth ↔ visual truth

**Status:** PROMOTED from WATCH/RESEARCH to architecture scaffold by owner task
2026-08-31. NOT a shipping renderer. Read-only seam only.
**Owner:** `Docs/Research/DASH_MAGPIE_NATIVE_INTEGRATION_2026-08-31.md`
**Contract:** `Source/BS_GodFile/MelodiaIntegration/MelodiaVisualRepresentationSubsystem.*

---

## 1. The concept (from SSOT)

> "Conventional engine retains gameplay/simulation state while a generative renderer
> produces visual frames." — `Docs/Research/EMERGING_3D_RENDERING_TOOLCHAIN_RESEARCH_2026-08-30.md`

Magpie separates **simulation truth** (what the game IS) from **visual truth** (what
frames SHOW). It was WATCH-only because a generative frame renderer is not a production
dependency (determinism / latency / consistency / art-direction / temporal stability / QA / platform).

**Promotion scope:** we build the **seam** (the stable read contract), NOT the renderer.
A future Magpie-style renderer can be swapped under the presentation layer without
touching simulation. This is already the MelodiaCore doctrine — "presentation-only this
phase" — formalized as an interface.

## 2. Authority map (what is truth, what reads it)

| Layer | System | Role |
|---|---|---|
| **Simulation truth** | JRPG template, `UMelodiaNarrativeSubsystem`, `UMelodiaRhythmCombatSubsystem`, `UMelodiaWaterGameplaySubsystem` | authoritative world state (HP, quest flags, rhythm grade, positions) |
| **Visual truth seam** | **`UMelodiaVisualRepresentationSubsystem`** (NEW) | READ-ONLY accessors onto simulation truth; the contract a renderer consumes |
| **Presentation** | `MPC_Melodia_Palette` (BeatPulse/BeatPhase), existing HUD widgets, `CaptureRender` | what frames actually show |
| **Future Magpie renderer** | none exists | would read the seam and produce frames — **not built here** |

## 3. The seam contract (all READ-ONLY)

```
GetCurrentRhythmGradeKey()     -> FName  (Perfect/Great/Good/Miss)
GetBeatPhaseNormalized()       -> float  (0..1, mirrors MPC BeatPhase)
IsBattleActive()               -> bool
GetActiveNarrativeVisualFlags()-> TArray<FName>
IsReadOnlyByContract()         -> true   (determinism assertion)
```

- The subsystem holds **no mutable simulation state** — every accessor forwards to the
  owning authority at call time.
- It performs **zero writes** to simulation, MPC, or any HUD. It is not a second writer.
- A future generative renderer consumes these reads as "visual truth" inputs — the same
  pattern `UMelodiaAudioReactivePresentationSubsystem` already uses to drive `MPC_Melodia_Palette`.

## 4. Guardrails (binding)

1. **No frame generation** in this scaffold — Magpie remains a seam, not a renderer.
2. **No second writer** — the seam never mutates simulation or presentation state.
3. **No new authority** — rhythm/narrative/water stay OWNER; this subsystem only reads them.
4. **No `Content/_PROJECT/` writes**; no parallel material masters.
5. **Determinism:** `IsReadOnlyByContract()` is an assertable invariant — a probe checks it.
6. **Promotion is by-task only** (owner granted 2026-08-31); no auto-promotion.

## 5. Validation (evidence standard)

- `Tools/test_visual_seam.py` — offline: header exists, read-only API present,
  `IsReadOnlyByContract` present, no simulation-state comment. → `Saved/Audit/visual_seam_probe_*.json`
- Live PIE (next editor window): assert `IsReadOnlyByContract()==true`, read grade/beat/
  flags during a battle and confirm they match the owning authorities (no drift).
- Ledger row only from the live run — never from the offline probe.