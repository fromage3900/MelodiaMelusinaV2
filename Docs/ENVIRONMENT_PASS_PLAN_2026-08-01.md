# Environment / Set-Dressing Pass Plan — 2026-08-01

**Status: active plan for today's work. Supersedes the ad-hoc dressing done overnight (Decision 039)
as the process going forward — that work stands, this formalizes the sequencing from here.**

## Lane split (agreed with Kiro this morning)

- **Owner + Claude**: environment design, visual composition, dressing, lighting, materials, PCG,
  capture direction. Own every `.umap` and binary art asset — exclusive-write while claimed.
- **Kiro**: read-only systems support, documentation, evidence capture, and later validation of
  gameplay-facing consequences (route reachability, PlayerStart validity, no stale UI/input after
  travel, package/cook evidence) — without touching art assets. Kiro does not change a level to
  address a finding without owner approval.
- **Codex**: Niagara system authoring only (see `Docs/Handoffs/CODEX_NIAGARA_UPGRADE_2026-08-01.md`)
  — the graphs themselves, not where they're placed. Placement stays in this lane.

## Process, per level (Kiro's structure, adopted)

1. **Claim the level** before editing — state which `.umap` is being worked so no concurrent edit
   collides with Codex (who may be mid-edit on a Niagara system asset the level references) or Kiro.
2. **Define a one-line visual goal** before touching anything — what should this level communicate
   that it doesn't yet.
3. **Dress/light/compose.**
4. **Save.**
5. **Capture evidence** (screenshot or the actual render-archive capture) before moving to the next
   level — don't chain multiple levels' edits without a save+capture checkpoint between them.
6. **Avoid concurrent edits to the same `.umap`, material instance, PCG graph, or Niagara system** —
   if Codex is actively re-authoring a system that's placed in the level being dressed, don't also
   edit that placement in the same window; wait for Codex's "done" report on that specific system.

## Known blocker to work around today

3 of the effects placed overnight (`NS_Uni_DustShafts`, `NS_Uni_PollenSparkle` in
`L_MelusinaMorning`; `NS_Uni_Fireflies` in `ZenForestTest`) are empty Niagara shells — Codex is fixing
the systems themselves (P0 in their handoff). **Don't re-place or duplicate these effects while
they're empty** — the actor placements are already correct; only the system assets need Codex's
authoring. Capture evidence for those two levels should wait until Codex reports P0 done, or should
explicitly note "VFX pending Codex P0" if captured before then.

## Target order today

### 1. `L_KaleidoNave` — first, per Kiro's recommendation, and least blocked
**Visual goal**: the corridor should read as a continuous kaleidoscopic cathedral nave, not three
isolated set pieces (entry, midpoint, finale) with 20,000+ units of empty space between. Overnight's
arch-pair placements (Decision 039) are a first pass at this — today's work is confirming it actually
reads that way from the 4 placed cameras, not just that objects exist at the right coordinates.
- Walk all 4 cameras (`CAM_Kaleido_Hero`, `_Colonnade`, `_Axis`, `_KaleidoNave_Portfolio`), confirm
  framing against the new arch pairs and both petal-VFX instances.
- Not blocked by Codex — `NS_SakuraWaterPetals` (used here) is already a real, working system.
- Save, capture evidence, then move on.

### 2. `L_FallenMoon` — second, already near-complete, quick confirmation pass
**Visual goal**: confirm the existing 5-camera/3-VFX/PPV setup still reads correctly after last
night's PPV fix (Decision 038) — this level had the most going for it already, lowest-risk to verify.
- No new dressing anticipated unless the walk-through finds a gap.
- Save, capture evidence, move on.

### 3. `L_MelusinaMorning` — third, partially blocked on Codex P0
**Visual goal**: the bedroom should read as lived-in and warm (bed, lanterns, bookshelf already
present) with morning light motivating the new threshold dust-shaft placement once it's real.
- Confirm the new camera (`CAM_MelusinaMorning_Portfolio`) framing — this was a first-pass placement
  last night, not visually verified yet.
- Dust-shaft/pollen VFX capture waits on Codex; everything else (camera framing, existing set
  dressing) can be confirmed now.
- Save, capture evidence (note VFX-pending if captured before Codex's fix lands), move on.

### 4. `ZenForestTest` — last, partially blocked on Codex P0
**Visual goal**: confirm the existing camera and new sakura-petal/firefly placements read well
against the torii/tea-house cluster, avoiding the 3 `MelodiaNPCPlaceholder` cylinders (already
confirmed clear by distance, not yet visually confirmed in-frame).
- Sakura-petal VFX (`NS_SakuraPetals_v2`) is real and working — capture that now.
- Firefly capture waits on Codex.
- Save, capture evidence, move on.

## Verification

- Per level: save confirmed via Monolith `editor_query save_packages`, evidence captured before
  moving to the next level — no chaining multiple levels' worth of unsaved changes.
- Hand Kiro a go-ahead for their later gameplay-consequence validation pass only after all 4 levels
  are dressed and saved — not mid-pass, to avoid Kiro validating a route through a level still being
  actively edited.
- Codex's P0 completion (module/renderer counts > 0 on the 4 empty systems) is the gate for
  re-capturing `L_MelusinaMorning` and `ZenForestTest`'s VFX-dependent shots.
