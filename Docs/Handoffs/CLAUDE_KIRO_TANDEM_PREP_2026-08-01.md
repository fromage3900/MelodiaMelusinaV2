# Claude ↔ Kiro tandem prep — core gameplay systems

**Date:** 2026-08-01, end of the PPV/lookdev session.
**Purpose:** hand the presentation layer over in a state Kiro can build gameplay against, and name
exactly what is ready, what is blocked, and what is unverified.

## The presentation layer is done and waiting on gameplay

Everything below is **live and runtime-verified** — no build gates, no config gates:

- `r.CustomDepth=3` is persisted in `Config/DefaultEngine.ini` (owner-approved).
- `UMelodiaRhythmReactivitySubsystem::SetReactiveStencil` is compiled and linked — verified by
  artifact, not by claim (`MelodiaRhythmReactivitySubsystem.cpp.obj` 11:55:45,
  `UnrealEditor-MelodiaCore.dll` 11:56:25, both after the 11:13:01 source edit).
- The live outline material reads `CustomStencil` and switches ink colour on values 1/2/3, with 4
  reserved as a "no ink" escape hatch.

**Nothing calls it.** That is the single gap between "a stencil system exists" and "the game has
reactive visual feedback". This is Kiro's move, not a Claude one — the mapping from gameplay state to
stencil value is a design decision.

### The contract

```cpp
RhythmReactivity->SetReactiveStencil(MeshComponent, StencilValue);   // presentation only, no return
```

| Value | Renders as | Suggested meaning (owner decides) |
|---|---|---|
| `0` | normal ink; also disables the CustomDepth pass on that component | idle / cleared |
| `1` | `Style1Color` (warm) | interactable in range |
| `2` | `Style2Color` (cool) | quest / objective target |
| `3` | `Style3Color` (gold) | selected / focused |
| `4` | no ink at all | deliberate opt-out |

### Four rules that will bite

1. **Per `UPrimitiveComponent`, not per actor.** A character with a skeletal mesh plus weapon/prop
   static meshes needs the call on each component, or you get a half-outlined actor.
2. **Always clear to `0`** — on exit *and* on death, teleport, level unload, encounter end and actor
   pooling. A stale `3` reappears on whatever reuses that pooled actor.
3. **Only 1–4 do anything.** Values 5–255 are legal to write and render as normal ink. Don't encode
   gameplay data in the stencil byte expecting it to be visible.
4. **Never read it back.** Nothing may branch on stencil state or treat it as truth. Gameplay writes;
   the material reads. One-way, per the standing FX rule.

**Cheapest convincing first wire:** interactable-in-range → `1`. One call, immediately legible,
proves the whole chain end to end.

## What Claude should NOT be asked to do next

- Touch `MI_StorybookOutline_Premium_Hero` or the live grade. The look is owner-approved and locked.
- Save `ZenForestTest`. Owner art work is dirty there; every session has left it deliberately unsaved.
- Own gameplay, quest, save, input or encounter authority. That stays with the JRPG template per
  Decision 009, and MelodiaCore remains quarantined as runtime-unstable for authority purposes —
  note the stencil helper lives *in* MelodiaCore but is presentation-only, which is legal but was a
  deliberate choice worth revisiting.

## Gameplay state Kiro is walking into

From `_TASK_QUEUE.md` — several P0s are marked **"Fixed (unverified in PIE)"**, which is the highest-risk
category in the project right now:

- Dreamstate portal destination corrected (`MelodiaOpeningPortal_0` → `L_KaleidoNave`) — not yet
  PIE-walked.
- Death route to `WBP_MainMenu` fixed via `BP_BattleController` CDO — not yet PIE-walked
  (party wipe → confirm → arrival).
- Ollama QuillScript validation built — PIE smoke test still owed.

Test baseline is **46 pass / 3 fail**, and the 3 failures are known-stale assertions, not regressions.
Use `Automation RunTests Melodia` — **not** `Melodia.Integration`, which only runs 5 of them.

**Recommendation for the tandem session: spend the first block PIE-walking the three unverified P0s
before adding anything.** Three separate "fixed but unseen" items on the critical path is how a
vertical slice ends up failing on the day it matters.

## Open decisions that need the owner, not an agent

1. **Two palette authorities.** `MPC_Melodia_Palette` and `MPC_Portfolio_Palette` carry an identical
   vector set (`Melusina_*`, `R1999_*`, `Melu*`). The universal master reads one, the grade reads the
   other. This blocks real unification.
2. **Stencil interaction mapping** — which meshes, which states, which of 1/2/3.
3. **Stacked quarantined PPVs** in `L_SakuraPath` and `L_Template` (Decision 037a) — an unlabeled
   priority-0 volume still carries the quarantined outline pair, so `L_SakuraPath` renders two
   outline passes. Do not judge that level's look until resolved.

## Constraint worth knowing before any further material work

**A material may reference at most 2 MaterialParameterCollections.** Exceeding it fails compilation
outright with no graceful degrade. The sky already spends both slots
(`UltraDynamicWeather_Parameters` + `MPC_Melodia_Palette`). Plan the two slots deliberately per
material — this is the binding constraint on unifying outline, grade and sky.
