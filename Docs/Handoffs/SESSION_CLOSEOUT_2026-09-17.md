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
