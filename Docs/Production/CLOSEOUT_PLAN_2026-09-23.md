# Closeout plan (updated) — 2026-09-23

Supersedes the plan section of `MELODIA_STUDIO_CLOSEOUT_2026-09-21.md` (that
doc remains the audit record; this one is the task sequence to close out).

## Where the lane stands

Shipped and verified on this tree (see
`Saved/Audit/BRUTALIST_AND_STAGE_2026-09-23.md` for numbers):

- Track A builders **6 of 8**: EscherLadder, FountainLoop, DayNightFacade,
  Mansard, PenroseArch, MetamorphosisFrieze.
- BRUTALIST lane opened and shipped **2 of 2 planned for the first pass**:
  OfficeBlock, CubicleFarm.
- Shared family infrastructure: `paris_common.py` (helpers, `_sock`, `gn_line`).
- Staging deliverable: `Saved/Blend/MELODIA_GN_SHOWCASE_2026-09-23.blend` with
  organized collections and live modifier stacks; manifest + overview render.
- Gates green: preset audit exit 0 (157/492/0/0), sync 293/293, gate 6/6,
  census PASS (registry 601).

## Tasks to close out (in order)

1. **Finish Track A — MobiusBalcony + HyperbolicRose.** Each lands with 2-4
   presets, its own health script, preview renders, and a re-run of the full
   pipeline (audit -> sync -> baseline re-cut -> gate -> census). Discovery
   first: `MEL_mobius_strip` and `MEL_hyperbolic_window` already exist as
   decorative devices - the Track A builders must be architectural devices
   that do not duplicate them (balcony that returns to its own start at the
   wrong height; rose window with doubling tracery toward the rim).
2. **Refresh the stage** — add the two new builders to
   `deploy/_melodia_stage_gn_showcase.py` LAYOUT and re-stage, so the showcase
   file always reflects the full family.
3. **Brand-pack apply operator** — the one item that needs a LIVE Blender
   session (operator + hub row that applies a whole brand pack to a selected
   object). Validate end to end in the GUI, not headless.
4. **19 dropped-link trees** — fix-or-hide, then wire `LINK_STRICT` + gate
   check. (The `_sock` fix in paris_common removes the class for the new
   families; the 19 recorded trees are older modules.)
5. **C1 monolith-UI retire** — health 6/7; `plan_edit_floating` keep-vs-retire
   is an owner design call. Needs the owner, not an agent.
6. **Owner decision: commit/push.** Everything above is uncommitted by design
   (git pipeline law). The laptop line is `collab/laptop/longterm`; promoting
   is an explicit per-operation owner call with a written plan.

## Standing constraints

- One editor instance / one writer per surface (Blender here: headless runs
  serialise; no GUI session is open).
- `.uasset` writes: not this lane. `Saved/` outputs are the lane's artifacts.
- Health scripts are the evidence; a green build is not.
