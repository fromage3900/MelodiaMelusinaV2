# Melusina Master Work Plan v4 — Close-Out: Nikki Fabric Bar, Lissajous GN Suite, Higgsas Integration

> **For Hermes:** Supersedes execution order of v3 (`.hermes/plans/2026-09-22_001015-…v3…md`);
> v3's Wave G/F/H task detail and standing rules remain binding. Evidence standard: measured
> JSON + vision_analyze grading on cooked PNGs, never prose.

## Copernicus bake verdict (graded 2026-09-22 00:2x, vision_analyze on fresh cooks)

- **Cymatic loom (PearlWeave fresh 1024 cook): FAILS the Nikki bar.** BaseColor = blurred
  mush (no weave, no nacre banding, no flecks); Iridescence = functional grayscale mask but
  two sparse blobs, unstructured. 13 variant sets are imported to UE (9-10 channels each —
  structurally complete) but the visual bar is not met for fabric roles. They remain fine as
  cymatic NODE plates / hard-surface accents — just never as dress fabric.
- **Fabric lane (`pearl_painterly_aaa.py`, Moon set, fresh 4K cook): MIXED.** Iridescence
  PASSES (directional satin sheen, subtle-premium — the hue play comes from shader thin-film
  math, grayscale mask is correct). BaseColor near-correct for ivory (dot-grid reads pique,
  not satin). **Normal FAILS the house gate: single-direction lines, no warp/weft interlace,
  no crossings.** The recipe's warp component is not landing in the cook.
- **Conclusion: the Nikki dream is one recipe-fix away, and the animated flipbook generator
  must build on the FIXED fabric recipe, not raw chladni+fbm.**

## WAVE N — Nikki fabric bar (new)

- **N1 Weave-recipe fix** in `Tools/Houdini/pearl_painterly_aaa.py`: true two-direction
  interlace — warp×weft crossing with over-under phase modulation (sin phase per thread
  family), crest highlight only on the "over" thread; verify by vision_analyze on the cooked
  Normal (individual threads resolvable at 1024 preview) + BaseColor (reads satin, not pique).
  Keep the passing Iridescence branch untouched.
- **N2 Flipbook upgrade** (steer sa-2 / fold into `animated_materials_20260922.py`): fabric
  base = N1 recipe animated (phase-drifting interlace); chladni nodes = EMBELLISHMENT layer
  (vein glow / shimmer accents) over the base — never the base itself. Same for glob nacre
  flow (PearlWeave family rebuilt on N1 math).
- **N3 Nikki QA gate:** every fabric/material asset passes a 5-criteria vision grade
  (weave structure / nacre banding / flecks / painterly wash / expensive-vs-placeholder)
  recorded in `Saved/Audit/melusina_vfx_20260921/nikki_grades.json`.
- **N4 Chladni harp re-render** (missing `t_me_chladni_*`) rides the same solver — owner-gated.

## WAVE L — Lissajous GN builder suite (the dream, with Higgsas)

- **L1 Higgsas inventory first:** run `Tools/higgsas_gate.py`; list usable node groups
  (curve tools, bead strings, frames) from `RawArt/BlenderLibraries/Higgsas/Blender 5.0
  Higgsas Geo Node Groups v13.blend`. Verified list only — no assumed nodes.
- **L2 Core engine:** `MEL_lissajous_curve_3d` — sockets: Ratio A (X/Y), Ratio B, Delta
  Phase, Radius, Turns, Theta Range, Resample, Twist; curve → tube with round profile
  (quad-dominant), shade-smooth; resample count tied to Turns so thread density stays even.
  House pattern: per-object groups with baked dial defaults (5.x `properties.inputs` API,
  `update_tag()` after writes, NEVER rebuild wrapper trees).
- **L3 Builders (register via `register_builder` in AppData package first, repo deploy
  sync after):**
  - `MEL_lissajous_charm_chain` — knot-path charm chain around the collar
  - `MEL_lissajous_ring_dangler` — beads/charms swinging off the 3 clockwork rings
    (Scene Time counter-phase per ring — integrates with tonight's regalia)
  - `MEL_lissajous_wing_feather_lattice` — feather ordering along Lissajous arcs
    (upgrades the wing rows without rebuilding their trees)
  - `MEL_lissajous_shawl_drape_guide` — drape guide curves feeding the wide-panel
    XPBD shawl task (folds the shawl queue item)
- **L4 Topology imperative (owner demand):** per-builder audit JSON — tri/ngon counts,
  pole counts, sharp-edge inventory (reuse sa-0's audit harness); quads for tubes,
  GN Bevel only on designed hard edges, shade-smooth-by-angle everywhere else;
  MESHmachine/MACHIN3tools = host-mesh cleanup only, never a reason to bake GN output.
- **L5 One-writer rule:** new builders join the existing package taxonomy
  (`Docs/Production/GN_TAXONOMY_2026-08-29.md` resync after the batch).

## Close-out order

1. Wave G fixes (await sa-0 audit) — then bank.
2. F smoke verdict (await sa-1) → emitter rig → full overnight bake → import/material.
3. N1 recipe fix → N2 flipbook upgrade (steer sa-2) → N3 grades.
4. L suite: gate → core engine → 4 builders → audits → taxonomy resync → repo sync.
5. H3 wiring (flipbooks into materials, loop-rate = Scene Time).
6. B beauty pass — owner eyes gate; S skills (`melodia-animated-flipbook-materials`,
   `melodia-lissajous-gn-suite`) staged only after their workflows verify.
