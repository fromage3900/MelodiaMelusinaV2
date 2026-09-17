# Boat Polish Plan v05 — GN hull cure + ribcage build + brightwork (2026-09-17)

Scope: the MK38 starskiff only. Melusina is the owner's. School Blender 5.2.
Nothing below touches source canon (MK36/MK38) — all proof ran on a scratch copy.

## 1. GN hull research: VERDICT (proven in scratch, 2026-09-17)

Symptom: Hull_Shell evals 11.42 x 6.36 x 3.94 m in MK38 (authored hull is 7.55 m).
Isolation: form tree ON = bloat, form OFF = base, audio = neutral.
Root cause: MK38's filed trees predate the code fix — their interface defaults sit
at 1.0 (Beam/Length/Taper measured). Current builder code (`starskiff_hull.py`)
is already zero-neutral (Beam/Length/Rocker/Tumble/Taper default 0.0).
Cure proven on scratch copy of MK36: delete old groups, rebuild trees from current
code, attach FRESH modifiers (fresh mods take group defaults; Blender 5.2 exposes
no Python path to per-modifier GN inputs, so never try to dial the old mods —
replace them). Fresh eval with form LIVE: 7.61 x 2.54 x 1.01, 1537 verts.
Audio tree untouched and live throughout (clip-less = silent-neutral for stills).

Rollout (stage-local, reversible):
1. In the next stage file (v05): remove HullForm/HullAudio mods, delete the two
   filed groups, rebuild from current builders, attach fresh mods in order
   (form first, audio second, both before bevel/weighted-normal).
2. Eval-gate: hull must read 7.6 x 2.5 x 1.0 or the rollout stops.
3. UNMUTE form (mute was the v03 field dressing, not the cure).
4. Dials stay GUI-only forever: headless cannot set GN inputs in 5.2.

## 2. Ribcage build: FOUND, BUILT, MEASURED (was preview-only)

The builder existed all along: `build_skiff_ribcage` (`starskiff_biomech.py`) —
MEL_skiff_ribcage, 28 nodes, knuckled bone-rib arcs keel->gunwale, NaN-guarded
ellipse math, measured station table for the 7.615 m hull. Only
`mk38_ribcage_preview.png` ever reached the blend; no rib geometry shipped.
Scratch instantiation: single-vertex host + Ribcage modifier → 9 ribs spanning
7.61 x 0.81 x 1.00, 216 verts. First real blend ribcage of this hull.
Sister builders inventoried and ready: MEL_skiff_balljoints (keel collars),
MEL_skiff_plates (strake armor over the bones), MEL_skiff_rivet_lattice.

Merge plan (v05 stage):
1. Ribcage host + modifier, defaults (Rib Count 9, Span 0.806, Thickness 0.035).
2. Eval-gate: span must read ~7.6 x 0.8 x 1.0 and sit INSIDE the hull shell
   (ribs are bones under armor, never poking through — eye-check broadside).
3. Then, in order: balljoints, strake plates, rivet lattice — one per commit,
   each with its own eval-gate. Bones before armor is the builder's own rule.

## 3. Brightwork polish list (ranked)

1. Nail material .001 duplicates (32 of the 62 mats) — caused by the v03 append;
   remap to originals in the GUI, purge orphans. My mess, flagged for cleanup.
2. Lantern crystal + gunwale glow emissive pass for wake shots (13-16): raise in
   a COPY of M_Lantern_Crystal / gunwale mats, never the shared originals.
3. Mast pennant + oar wood check against close-ups (03/13); weathering only if
   the panels ask for it.
4. FX_Wake_L/R empties: foam/burst placement for shot 13 (the wake lift) — pair
   with the anchor's +0.3 Z key.
5. Cushion velvet + floor grating close-up check (boarding shot 14).
6. Optional atmosphere: starlight dome (physical-starlight) for 01/16, projection
   matte far shore for 16. Only if the wides feel empty after ribs land.

## 4. Order of work

v05 stage: fresh-tree rollout + ribcage merge (gates above) → re-render the 6
boat panels + boat beauty set → commit. Then brightwork 1-2, then 3-5 as the
panels demand. Bones before armor, proof before polish.

## 5. v06 — rib orientation fix + finial + crash recovery (2026-09-17 evening)

The GUI session crashed at 19:20 (UI panel-draw thread, right after hardops /
kushiro_tools / cloth_next / pro_particles were installed mid-session; the
reopened session sits clean on the v05 disk state). Live-only edits were lost and
have been REBUILT on disk as SHOREWAKE_proxy_v06_boat.blend (headless —
Saved/Audit/roll_v06_recovery.py):

- Material dedupe: 15 identical .001 dupes verified, remapped, purged (57 mats).
- RIBCAGE ORIENTATION FIX (the big one): measured cross-sections (ASCII, mid +
  bow) show the builder's arc arrives as an upside-down dome spanning one side
  (y 0..beam, high center). Correct form for this hull = U: tips at the gunwales,
  dip at the keel. Fix = rotate host 180 about X + re-seat: ribs now y ±0.403,
  z 0.620..1.618 — tips spring 0.32 above the deck line, which is exactly the
  Arc Rise dial's own language ("how far the arc springs above the deck line").
- BalljointsHost: MEL_skiff_balljoints built + same transform (1,692 verts at the
  rib tips, gunwale collars). Flag: bow-most pair reaches ~0.35 m past the rail.
- Star finial: kit builder MEL_star_finial, M_Brass, seated 0.03 above the
  masthead lantern (x 0.21..0.48, z 3.54..3.84).
- The owner's mid-session HullForm Beam 0.53 dial died in the crash — not baked
  (panels so far all rendered at neutral); re-dial in the modifier panel or ask.

RULES from tonight: (1) after installing addons mid-session, restart Blender;
(2) structural edits persist to disk headless — never live-only;
(3) the open session is for looking; the roll scripts are for keeping.
