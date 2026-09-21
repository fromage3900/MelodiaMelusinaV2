# Melusina + Choral Sheep + Sir Melodious — Composition, Cameras, Goo Physics & Outfit Decor Plan

> **For Hermes:** Execute task-by-task; every task gates on measured JSON, never prose. The owner's
> live Blender session is authoritative — never save it, mutate in-memory only on explicit GO.

**Goal:** A finished beauty composition — Melusina gazing into the distance, the Choral Sheep beside
her, Sir Melodious perched on her shoulder — with cameras that frame all three, Goo Physics-driven
dangle/feather life, and Melusina's outfit decorated with the same GN ornament language as the sheep.

**Architecture:** The live session (`Melusina_Harp_HERO01_ArcherPoseV09_ARP_R08_WIP_20260912.blend`,
dirty, 1149 objs) is the workbench. All heavy generation runs headless on copies in
`Saved/Audit/MelusinaPolish_20260920/`; live-session work is bounded in-memory edits with measured
re-reads. Ornament carrier pattern: zero-vert host + NODES modifier + bone parent
(`parent_type='BONE'`), dials via interface sockets by name.

**Tech:** Blender 5.2.1 EEVEE · surreal_arch GN builders (`deploy/surreal_arch/melodia_gn/`) ·
`Tools/gen_flower_brooch_v10.py` (en-tremblant authority) · Goo Physics v1.0.0 (installed, 4 modes,
METAL/JEWELRY + GOOFLAPPY presets) · house evidence standard (PNG + JSON pairs).

---

## Current context (audit 2026-09-21, full data: `Saved/Audit/staging_composition_audit_2026-09-21.json`)

- **Cameras:** Cam_Beauty 50mm f/4@5.29m (active) is the hero candidate but puts the sheep ~28°
  off-axis. Cam_Front 55mm f/1.8@2.31, Cam_Low 42mm, Cam_Turntable 52mm, Cam_Macro 90mm.
- **Lights:** key L_KeyWarm AREA e2.0 saturated pink [1,.01,.16]; rims L_RimPink e7.0 pink + e7.0
  blue; L_GoldKick POINT e4.0 gold. Harp-stage lights (650–800) sit at the character and can
  contaminate wides. 3 suns + 3 Starlight suns exist but hide_render'd. World = flat grey
  FadeDayNight. No neutral fill.
- **Placement:** character_rig at origin; **Melusina.001 (18.8k body) linked to NO collection —
  cannot render**; the render body is the Retopo_Melusina_002/Characters set. Sheep appended
  (MrSheepFinal on armature 'rig' at (2.54,0,0.64), body back 1.31m vs her 2.07m — correct companion
  read). **Four GN ornaments stranded at x≈7.6** (horns/halo/music beads/pearl danglers — world-baked
  guides don't ride host or armature transforms). **Sir Melodious IS in-scene** at her right
  shoulder: `SirMelodiousBody` (3.9k verts, ~0.5m span, render-visible) + `sirmelodious_Retopo_PM3D_*`
  feather/retopo family (densest 226.8k verts) in `Characters`, around (-0.94,0.09,1.23). Also live:
  `FF_MelusinaHair_Domain/Drip` (FLIPFluids water-hair sim, `Melusina_WaterFX` collection).
- **Session traps:** render res parked at 20% (384×216); port 9876 double-bind (a second Blender,
  RESTAGE_STARTER, binds via SO_REUSEADDR but never answers — if that file is meant to be the
  target it needs its own port); sheep appended into collection `ChoralSheep_Appended` (in-memory).

---

## Phase 1 — Session hygiene (live, in-memory, owner GO per item)

### Task 1.1: Render-body decision
Melusina.001 is unlinked and cannot render. **Ask the owner:** link `Melusina.001` into the render
collection, or is Retopo_Melusina_002 the intended beauty body? Do not guess — the wrong body in a
hero frame wastes the whole pass.
**Gate:** exactly one body is render-visible from Cam_Beauty.

### Task 1.2: Resolution + frame range
Set `scene.render.resolution_percentage = 100` (1920×1080), frame range per owner's anim intent.
**Gate:** re-read shows 100%.

### Task 1.3: Light isolation
Move the 3 harp-stage lights (e650/260/800 at (0.5,-0.26,0.26)) to a `Harp_QA_Lights` collection,
hide_render=True. Keep character trio + gold kick.
**Gate:** light census shows only the intended four render-visible.

## Phase 2 — Sheep ornament rebuild (cures the four strays)

### Task 2.1: Fresh hosts at the seat, bone-parented
Per the carrier pattern, for each of `SheepHorns`, `SheepLissajous_Halo`, `SheepMusicBeads`,
`SheepPearlDanglers`: delete the stranded host, create a zero-vert host AT the sheep's head/neck
world position, add NODES modifier on the existing S5 group (`MEL_S5_horns`, `MEL_S5_lissajous`,
`MEL_S5_music_beads`, `MEL_S5_pearl_string`), parent to the sheep rig (`rig`) with
`parent_type='BONE'` on the neck/head deform bone. Purge `surreal_arch*` from sys.modules before
re-import if builders are re-run.
**Gate:** evaluated bbox of each piece within 0.25m of its body anchor; zero missing node groups;
parent recorded in the integrity JSON.

### Task 2.2: Dial verification
Read each modifier's `properties.inputs[identifier]["value"]` for its dials (Scallop/Crack dials are
already proven); confirm horn curl variant + halo A:B:Δ per v3 accent rules (D3: 1 hero + ≤2
supporting — the sheep's hero accent is the collar; halo only if owner wants G-state).
**Gate:** dial table in `<stage>_integrity.json`.

## Phase 3 — Sir Melodious

### Task 3.1: Melodious contact + parenting audit (bird already in-scene)
Sir Melodious exists: `SirMelodiousBody` + `sirmelodious_Retopo_PM3D_*` family in `Characters`.
Audit, don't import: confirm every piece is parented (directly or via the armature) to
`SirMelodious_rig`; measure feet-to-perch contact at her shoulder (<2cm gap); flag any
render-visible rig-control spheres (cs_sphere.001/.003 are render-visible — they should be
hide_render or moved to a controls collection).
**Gate:** per-piece parent map in the integrity JSON; control spheres render-invisible;
contact distance recorded.

## Phase 4 — Cameras & gaze

### Task 4.1: Hero reframe
Pull Cam_Beauty back to ~7.5m (or 35mm at current distance) so Melusina centres at ~5.4m and the
sheep lands frame-right inside a 50mm FOV; keep yaw ≈37°. Verify with a 20% proxy render + lit-bbox
check (sheep fully inside frame).
**Gate:** proxy render shows her + sheep + shoulder perch all inside the crop; JSON stats saved.

### Task 4.2: Gaze pose
On `character_rig`, base+delta FK keying (skill procedure): head/eyes turn toward frame-left into
the distance (small deltas, 5–10° head, shoulders relaxed). Key on a single frame; record base
eulers first. Sheep head may turn toward her (2–3 bone deltas on `rig`).
**Gate:** head world-rotation delta measured; no wardrobe clip (evaluated mesh intersect check
skirt↔thigh stays under current tolerance).

### Task 4.3: Second angles
Cam_Low (42mm) re-aimed for the low hero; Cam_Turntable for the 3/4 pair.
**Gate:** two proxies, both JSON'd.

## Phase 5 — Goo Physics (bird sway + dangle life)

### Task 5.1: Bird body/feather sway
On SirMelodious 2–3 bone chains (head/crest, tail, wing-tips): `goophys.add_jiggle_physics_to_selected`
mode GOOFLAPPY preset; Root Ref empty CHILD_OF the shoulder perch bone; bake
(`goophys.bake_physics`) once the owner likes the read.
**Gate:** sim mesh max displacement >1cm across 30 sequential frames (alive, not exploded);
bake cache exists.

### Task 5.2: Outfit dangle dynamics
On new brooch dangle chains (Phase 6) + existing earring/charm chains if any:
`goophys.add_geonodes_physics_to_selected` with **METAL/JEWELRY** preset ("earrings and necklaces"),
colliders = convex-hull combined (reuse the sheep's `GooPhysics_CombineObjects` pattern).
**Gate:** dangle tips move >5mm on a head-turn scrub; no intersection with shawl at rest.

### Task 5.3: Runtime authority note
Goo is authoring/bake only. In-game dangle authority remains KawaiiPhysics (Pattern A,
`Docs/MELUSINA_WARDROBE_PHYSICS_PIPELINE_2026-09-15.md`). Any UE export uses
`use_armature_deform_only` + baked caches; no second runtime writer.

## Phase 6 — Outfit GN decoration (the sheep's language on Melusina)

### Task 6.1: Brooch hero piece
Build `GN_FlowerBrooch_v10` (genome per `Saved/Accessories/brooch_lab/genome/` — recommend
gala_tide or nova) via `Tools/gen_flower_brooch_v10.py` on a shawl clasp anchor
(bone-parent to the shawl's clavicle-area deform bone). En-tremblant dangles: Sway=0 for the beauty
still; `Dangle Sway/Rate` dialed for a motion pass. Add `GN_Brooch_Sparkles_v7` second modifier
(Twinkle Speed low for stills).
**Gate:** evaluated bbox at the clasp <0.35m; degenerate faces = 0; dials + sway formula recorded.

### Task 6.2: Dangle family accents (≤2 supporting, D3 rule)
From the addon registry: `MEL_nikki_star_pendant` (guide-driven, Hang .075/Droop .08/Cord .0026)
draped from the shawl back-edge; `MEL_nikki_bead_string` (catenary, Droop .1) as a skirt-side
accent — guides drawn in WORLD coords, unparented, hosts zero-vert (the skill's guide recipe).
Optional `gold_light_strip` seam on the shawl edge (emissive, restrained).
**Gate:** per-piece world coords + anchor printed; total added objects ≤6; no clipping at rest pose
(evaluated intersect check).

### Task 6.3: Audio-reactive dials (optional, deferred)
The dangl family reads Sound/Time/Low/High Hz + Audio Gain (Scene Time → Sample Sound → SetPosition
Z). For today's stills keep them static (Sway=0, no Sound datablock); wire a Sound datablock only in
a later motion pass if the owner wants it.

## Phase 7 — Beauty pass & evidence

### Task 7.1: Light balance for the frame
Add one neutral fill (AREA, low e, camera-left) to balance the saturated pink key; optionally raise
`Set_Diorama` backdrop from hide_render if the owner wants an environment behind the gaze.
**Gate:** proxy render mean-luma inside 0.18–0.32 band; no blown highlights on the shawl.

### Task 7.2: Panel renders
Cam_Beauty + Cam_Low + Cam_Turntable at 100%, PIL number burn-in, near-black-fraction stats each.
**Gate:** every PNG ships with its JSON (house standard); owner eye pass is the final gate.

---

## Files likely to change / create
- Live session (in-memory, owner saves): `Melusina_Harp_HERO01_ArcherPoseV09_ARP_R08_WIP_20260912.blend`
- Staging copies + integrity JSONs: `Saved/Audit/MelusinaPolish_20260920/` (new `*_comp_*` stages)
- Audit artifacts: `Saved/Audit/staging_composition_audit_2026-09-21.json` (exists)
- New scripts: `Saved/Audit/MelusinaPolish_20260920/comp_<task>.py` (one per headless pass)

## Risks / open questions
1. **Melusina.001 vs Retopo body** — owner decision (Task 1.1) blocks all framing.
2. Sir Melodious is in-scene; only audit work remains there (contact/parenting/control-sphere
   hygiene).
3. Port 9876 double-bind: any socket automation can only reach the WIP file; the RESTAGE_STARTER
   session is dark. If the owner wants THAT file staged, it must move to another port first.
4. The sheep's four GN ornaments: fresh-host rebuild must re-check world-baked guide internals per
   group — the S5 trees were authored in the sheep file's frame; verify evaluated bbox immediately
   after build (the 0.6m-offset class of bug).
5. Goo Physics is new to this file: run it on scratch duplicates first (skill: never sim the source
   mesh), keep bakes reversible, presets before hand-rolled dials.
6. Queued lanes not in this plan: UE Agent A A/B capture (needs an exclusive editor window), sheep
   S7 presentation renders, TD field pipeline (TD down, `comp_final_wool` broken).
