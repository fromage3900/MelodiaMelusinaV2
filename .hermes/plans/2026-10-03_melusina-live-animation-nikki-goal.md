# Melusina Live Animation — Formal Bounded Goal (2026-10-03)

Owner: Brennan Shepherd. Executor: Hermes (CLI in Rider), live UE via Monolith `:9316`.
Recovered from: the rate-limited Codex marathon thread (objective: "converge Melusina's
existing runtime animation path without adding architecture").

## Goal (bounded, tonight)

By 11:30 p.m. America/Toronto, 2026-10-03, move Melusina's live runtime animation path
one more proven notch toward the Infinity-Nikki bar — inside existing owners, no new
architecture (no new pawn, ABP, Niagara, retarget or collision framework):

1. PROVE hair <- body shared collision in PIE (debug-draw capture + receipt + frames;
   owner eyes on the frames). This is the exact item Codex died mid-testing at 6:49 PM.
   Status: config restored + saved 7:31 PM; capture run scheduled.
2. PUT the staged candidate sets in front of owner eyes as contact sheets and get
   accept/reject marks: (a) shirt skinfit raised-arm fit, (b) hair-ornament swing,
   (c) the four idle candidates vs the `A_Melusina_Idle_Mocap_RootX` baseline,
   (d) the shared-collision debug captures.
3. ADOPT one Nikki-bar technique inside the existing KawaiiPhysics owner only:
   adaptive dynamic control for the hair/ornament chains — dynamic flutter while
   moving, shape-held while idle — via existing params (no new solver).
4. RECEIPT: Saved/Audit receipts + contact sheets + committed artifacts.

## Infinity Nikki bar — research digest (2026-10-03, sources below)

- Cloth: constraint-based solvers instead of collision-based; a soft-driven constraint
  pre-stage so garments never clip on first contact; silhouette preservation for
  structured garments (petticoats behave like fabric but keep their construction);
  inter-garment + multi-layer collision handling so free outfit combinations stay stable.
  [Apple Developer interview, Infold]
- Ribbons ("Tide of Tears"): hybrid cloth + bone physics with adaptive dynamic control —
  silky flutter while running; shape-locked "as if in water" when standing still.
  [Automaton interview]
- Materials: re-engineered fabric algorithm (4-layer UV blending, minimal params across
  cotton/silk/velvet) + a jewelry system (refraction, 3S transmission, sparkle response).
  [Apple Developer interview]
- Motion polish: feet must not stamp (light, elegant steps); slow micro-response jumps;
  idle/foot/reaction animations refined in live patches. [Apple; 1.6 patch notes]
- Pipeline: Marvelous Designer (patterns) -> Houdini (dynamics) -> UE5 (Lumen + materials).
  [foro3d]

## Non-goals (explicit)

- No new pawn/ABP/Niagara/retarget/collision framework; no battle-montage rework; no
  engine or Config changes; no p4 submit without explicit owner OK.
- The stable JRPG spine stays authoritative — this is convergence + acceptance.

## Definition of done

- PIE receipt with frames showing the hair against body collision (owner-verified).
- Contact sheets for the candidate sets; accept/reject captured in this file's addendum
  or the receipt.
- One adaptive-dynamic-control experiment receipt (params + before/after captures) or a
  written "not yet" with the measured reason.