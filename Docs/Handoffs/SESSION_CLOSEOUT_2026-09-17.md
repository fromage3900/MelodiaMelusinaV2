# SESSION CLOSEOUT — 2026-09-17 → 18 (SHOREWAKE animatic + starskiff campaign)

**Lane:** Humber_FinalYear_Prep / ANMN301_Animatic — Blender-only (NO UE; school animatic)
**Tree:** `C:/EnvironmentPortfolio/BS_GodFile`, branch `cleanup/pbr-twin-landing-2026-09-10`
**Closes at:** 2026-09-17 ~23:15 EDT

---

## 1. What this session produced

### Animatic deliverables (school)
| File | State |
|---|---|
| `Humber_FinalYear_Prep/ANMN301_Animatic/ShepherdBrennan_AnimaticCreation_2026-10-09.mp4` | 1560f / 24fps / 65.0s / silent / 1080p — committed |
| `.../SHOREWAKE_VSE_animatic_v01.blend` | 19 strips (title 72f + 17 panels + end 72f) — committed this closeout |
| `.../SHOREWAKE_VSE_animatic_v02.blend` | revised cut — committed earlier |
| `.../proxy/panels_v2/panel_01..17.png` | 17 storyboard panels @1920x1080 — committed |

### Starskiff build lineage (each generation = a committed blend)
```
v02_storyboard -> v03_skiff (MK38 90 objs seat-aligned)
  -> v05_boat (fresh GN trees, 9-rib ribcage)
  -> v06_boat (GUI-crash recovery + star finial)
  -> v07_decor (star-pendant garlands, 12/side)
  -> v08_brightwork (128 objs: furled sail, pennant, bolts/rows/hex,
       crow's nest + bell + rope ladder + laundry line, mast bands,
       rope coils, lantern hoops->brass, keel caps, 42 waterline studs)
  -> v09_crest (131: stern name plate + medallion, bow crest rosette)
  -> v10_plates (133: strake-plate armor, kit MEL_skiff_plates, verified solid)
  -> v11_silhouette (134: swallowtail pennant, canvas-read furl + tie gaskets,
       star scaled 0.85; all three verified at 320px thumbnail)
  -> v12_rivets (rivet lattice tested + PARKED, removed; finding recorded)
  -> v12w_water (137: Ocean modifier + normal-driven emission shading,
       ripple rings keyed 07/08, wake trail keyed on from 13)
```
**Chain tip / next input: `proxy/SHOREWAKE_proxy_v12w_water.blend`**

### Plans & reviews written (all committed)
`SHOREWAKE_STORYBOARD_PLAN_v02.md` · `ADDON_USAGE_PLAN_v02.md` ·
`SHOREWAKE_OUTFIT_PLAN_v04.md` · `BOAT_POLISH_PLAN_v05.md` ·
`BOAT_TOPOLOGY_STUDY.md` · `BOAT_MOTION_PLAN_v08.md` · `BOAT_MASTER_PLAN_v09.md` ·
`SKIFF_GN_MASTER_PLAN_v10.md` (v12 + v12w notes appended) · `SKIFF_REVIEW_v11.md` ·
`VSE_RESEARCH.md` · `proxy/EXPERT_REVIEW.md` · `SHOREWAKE_BEAT_BOARD.md`

### Live-session (MCP) work performed during the session
Pennant wind sim · brightwork bolts/rows/hex iterations · crow's nest build ·
floating-bolts parenting bug found+fixed · furled sail + pennant reseat + warm fill ·
rope ladder / bell / laundry line · mast bands / rope coils / keel caps / bow ball ·
42 waterline strake rivets · waterline truth re-measured (z 0.62).

---

## 2. What I learned (hazards, in order of cost)

1. **GN modifier inputs are unreachable from Python in 5.2.** `m[key]` read/write both
   fail. Workarounds that DO work: fresh trees from builder code; **group interface
   defaults** via `node_group.interface.items_tree` (object sockets included — this is
   how a Guide object is driven headless); numeric rebend of baked meshes.
2. **Single-surface shells render as ghost "glass" in EEVEE** when the material carries a
   HASHED blend or texture alpha. Cure: plain opaque no-node material + Solidify (10-12 mm).
   Cost: three renders chasing "translucent armor" that was geometry, not material.
3. **Rivet lattices are sub-pixel on a 7.6 m hull at storyboard distance.** Three
   render/vision passes proved it; hand-placed stud rows carry the read. Parked + recorded.
4. **The water's emission hid every wave.** Emission 4.0 = constant color regardless of
   geometry. Cure that KEPT the look: drive Emission Strength from
   `Geometry.Normal.Z -> MapRange(0.982..1.0 -> 2.0..7.0)`. Waves band; glow survives.
5. **Ocean modifier `spatial_size` is an int** in 5.2 (float raises TypeError).
6. **Absolute-coordinate meshes double-offset when reparented** — always set
   `matrix_parent_inverse = anchor.matrix_world.inverted()` (the floating-bolts bug).
7. **MACHIN3tools + MESHmachine refuse to register under 5.2** (older releases).
   HardOps 26.1.5 works. FLIP Fluids broken (disabled). LiquiFeel hangs headless
   (`--factory-startup` required).
8. **GUI crash (19:20) after mid-session addon installs** (hardops/kushiro/cloth_next/
   pro_particles, UI panel-draw thread) — all in-memory edits lost; rebuilt from the
   19:52 save. Install addons at session start, not mid-flight.

---

## 3. In flight at close (delegated, background)

Five subagents were dispatched to write + self-verify build scripts. They write to
`Saved/Audit/` (gitignored — the files persist on disk only):

| Script | Piece | Chain step |
|---|---|---|
| `Saved/Audit/sa_tiers.py` | MEL_chime_carillon_tier + MEL_cn_tiered_pagoda (A/B) + MEL_balcony | v13 |
| `Saved/Audit/sa_drapery.py` | stern awning (MEL_mother_draped_curtain) + MEL_heraldic_banner | v14 |
| `Saved/Audit/sa_jewels.py` | bead string / star pendants / heart chain / filigree wreath / hair cascade | v15 |
| `Saved/Audit/sa_lissajous.py` | lissajous ribbon stays + arch + pearl variant | v16 |
| `Saved/Audit/tools_gn/` | raycast_place / seat_by_iteration / host_builder kit | tooling |

**To resume:** run each script against the chain file in order, editing its INPUT to the
previous step's OUTPUT (they open a blend and save the next generation). Input for v13 =
`proxy/SHOREWAKE_proxy_v12w_water.blend`. Verify each with a render + vision pass, then
re-render the affected panels.

## 4. Open items / blocked

- **Bow prop (`Melusina_Bow`, 1,144 verts)** — canonical arrives rotated 90° about Z;
  headless placement refused by the gate. Owner GUI handoff stands.
- **Wake trail** reads faint at wide scale and can dip under crests — raise or rework.
- **Promoted motion shots** (01 / 07 / 08 / 13 / 15) re-render AFTER the structure chain
  (v13–v16) so the wides show final geometry.
- **Pennant bake** (sim → keyed cloth) still pending.
- **cut_frames/ (3.4 GB) and panels/ (33 MB) intentionally NOT committed** — intermediates;
  `panels_v2/` is the committed panel set.
- Two school docs sit untracked and unclaimed by this session:
  `Humber_FinalYear_Prep/ANMN301_Animatic_Checklist_2026-09-14.md`,
  `Humber_FinalYear_Prep/WEEKLY_NEXT_3_MUSTS_2026-09-14.md`.

## 5. Final stats

| Metric | Value |
|---|---|
| Commits this session (boat/animatic lane) | 12 |
| Blend generations on disk | v02 → v12w (11 files) |
| Boat objects at tip (v12w) | 137 |
| Verts: hull / plates / ribcage / rivet lattice (parked) | 7.61 m / 306 / 216 / 3,276 |
| Live MCP edit passes | 12 |
| Render+vision verification passes | 21 |
| Subagent children dispatched | 5 (in flight at close) |

---

## ADDENDUM — delegation batch complete; chain consolidated (23:35 EDT)

All five delegated tasks delivered and self-verified. The scripts were then run
for real down the chain, each on the previous generation:

```
v12w_water -> v13_tiers -> v14_drapery -> v15_jewels -> v16_lissajous  (chain tip)
```

| Step | Script (Saved/Audit/, gitignored — persists on disk) | Result |
|---|---|---|
| v13 | `sa_tiers.py` (SA_INPUT/SA_OUTPUT env) | Tier2_Carillon visible + Tier2_Pagoda hidden (A/B) + Tier2_Balcony; gates PASS on v12w |
| v14 | `sa_drapery.py` (`-- --out`) | stern awning (draped curtain, hem z 1.271, slope 13.2 deg) + masthead banner; SA_DRAPERY_OK |
| v15 | `sa_jewels.py` (`-- --src/--scratch/--out`) | 12 pieces: rim bead string, 2 star-pendant strands, heart chain, mast wreath collar, 7 cascade ribbons; gates PASS |
| v16 | `sa_lissajous.py` (patched OUTPUT) | 2 ribbon stays + nest arch + pearl seaward strand; re-open verified, GATE_STATUS PASS |

Workspace kit: `Saved/Audit/tools_gn/{raycast_place,seat_by_iteration,host_builder}.py`
+ `self_test.py` (log `self_test.out.txt`) — per-object raycast proven vs the scene
BVH trap; seat converges 1 pass rigid; host_builder sets object sockets pre-attach.

### Renders (Saved/Audit/): v16_mast.png, v16_stern.png, v16_wide.png
- Mast: "coherent as a whimsical second story" — carillon crown, banner, filigree
  wreath, pendants, lissajous arch all read.
- Stern: awning "roofs the stern deck and slopes from the mast side down to the
  transom" — verified read.

### Owner calls / polish list (from the v16 art-director pass)
1. LISSAJOUS near-miss (flagged by the lissajous agent, stands): the bow stay and
   pearl strand graze the LIVE furled-sail mesh (0.0-1.0 mm, 4+97 sample points)
   because the brief's sail box (z 2.31..2.46) is 7 cm below the live roll
   (z 2.529..2.729). Fix = either drop the sail back to the stated z, re-route
   the stays, or accept the kiss.
2. Blue lissajous disc crowds the chime tubes at the mast — pull apart.
3. Boom/strap/banner silhouette ambiguous in the mast view; "detached left-hand
   cylinders" (rope coils?) want anchoring or cutting.
4. Heart chain barely reads from stern views (Stern_Crest silhouettes it); fine
   from quarters.
5. Pagoda (option B) sits at a 2.7 cm gap from the authored MastLantern and its
   spire lands inside the star finial — if B is chosen, revisit the lantern scale.

### Kit quirks carried (fixes applied on fresh trees only; kit sources untouched)
- chimes: Tube Count dial unwired (now wired, 14 chimes); semitone FIELD link
  collapses tube depth in 5.2 (dropped — chimes hang uniform 0.64 m).
- pagoda/balcony bake from module param defaults (dials cosmetic).
- draped curtain: gather vector mis-wired into SetPosition.Position (collapsed
  strip; relinked to Offset); literals relinked to the interface dials.
- hair cascade: profile curve reseated (zero-area sheet measured); needs a
  Set Material node on the fresh tree.
- heart chain needs a `Heart_Template_L` scene object (script builds + hides one).

### Status of this lane at close
Chain tip committed: `SHOREWAKE_proxy_v16_lissajous.blend` (all structure, drapery,
jewels, rigging, water). Next session: owner picks the A/Bs (carillon vs pagoda;
ribbon vs pearl), then the polish list, then re-render the promoted shots and the
panels, then the pennant bake.

## ADDENDUM 2 — v17 SNAP + SOFTEN (2026-09-18 00:05)

`SHOREWAKE_proxy_v17_soft.blend` (chain tip) — BVH nearest-surface audit +
selective snapping + soft-edge pass (`Saved/Audit/sa_snap_soft_v17b.py`,
`soft_cloth_v17c.py`).

Audit (gap to nearest big surface, world space): 14 pieces snug (0-10 mm) —
mast bands, lantern hoops, rope ladder, laundry line, nest bell, garlands
(2 mm), jewel beads/wreath/stars (0-8 mm), plates + stern plate (0 mm).
Snapped loose fittings: KeelCaps 0.136->0.006, Keel_BrassShoe 0.166->0.006,
MastLantern 0.035->0.006. Standoffs classified as BY DESIGN and left:
Tier2_Carillon (0.080 above the sail), StarFinialHost (0.410 over the lantern),
BalljointsHost (0.085 on rib tips), Stern_Crest (0.133, reads attached in
render). Tier2_Balcony's designed 0.167 m nest gap BRIDGED with a new
`BalconyBracket` (brass, beveled) instead of slamming the balcony inward.

Soft edges: Bevel 4 mm/2 seg/40 deg + smooth-by-angle on 9 hard-surface pieces
(plates, tiers, star, keel caps/shoe, mast bands, hoops, bell, nest, lantern);
`shade_smooth()` on the cloth family (awning, banner, swallowtail, 7 cascades).

Verification (vision): "keel trim caps and brass shoe flush, no floating gaps;
hull edges and armor plates read soft/beveled"; awning "reads softer, smooth
cloth shading rather than faceted hard creases". Note: the FIRST snap pass used
a blanket gap>30mm rule and damaged 5 standoff pieces — caught, reclassified,
rebuilt from v16; the wrong-rule lesson is now law in the new skill
`melodia-blender-snap-soft`.

New skills created this session: `melodia-blender-snap-soft`,
`melodia-skiff-chain`.

## ADDENDUM 3 — v18 REFINE + BIRD-SAFE TRAVERSAL (2026-09-18 00:45)

`SHOREWAKE_proxy_v18_refine.blend` (chain tip, 185 objects). Scripts:
`Saved/Audit/sa_refine_v18.py` + `fix_v18_arms.py` / `fix_v18c_soft.py` /
`fix_v18d.py` (iterative corrections, each render-verified).

Delivered:
- 3 soft ribbon swags (aft, fore, deck run) — Bezier + flat-object profile,
  rebuilt with a SAGGING cross-section after the first pass read as "rigid
  folded planes"; verdict after: "sagging, curved, soft cloth".
- 3 dangling heart chains: boom end (drop 0.26), bow rail, nest rail (0.22) —
  oriented to world-down by measured local axis (first attempt lay them flat).
- 1 more pearl lissajous strand (aft, scale 0.62).
- PROPER PADDLES: 4 leaf-blade oars in brass rowlock forks (port+starboard,
  midship), 1 spare stowed along the deck; M_Oar_Wood, smooth-shaded.
- BIRD-SAFE KIT for Sir Melodious: 9-tread spiral mast stair (0.165 m rise,
  hop-friendly) + 9 strut arms + helical handrail + 3 posts; 2 shroud cables +
  6 thick ratline rungs (mirror-interpolation bug fixed — first pass floated);
  4 brass T-bar perches (bow, stern, 2 on the nest rail); 2 gunwale guard-rope
  runs with 6 posts each. Route: deck -> guard ropes -> spiral stair (or
  ratlines) -> nest rim perches.

Owner notes: chains read "tonally twee" to the AD pass (kept — requested);
the swags may want a twist pass later; everything else verified at render.
New lessons written into `melodia-skiff-chain` (chain orientation, sagging
ribbon profile, strut+rail for stairs, shroud-parameter direction trap).
