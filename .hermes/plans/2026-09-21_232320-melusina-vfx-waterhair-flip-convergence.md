# Melusina VFX Polish + Water-Hair FLIP Convergence Plan

> **For Hermes:** Execute task-by-task; every gate is measured JSON/PNG+JSON pairs, never prose.
> The live GUI session on :9876 (PID 30268, WIP file dirty) is authoritative — never save it,
> mutate in-memory only on explicit owner GO. Heavy generation runs on copies.

**Goal:** Extend tonight's VFX wins (GN wings + clockwork regalia rings, both verified in-memory)
into a full polish pass, and integrate the staged FLIPFluids water-hair bake into her hair meshes
for globulating magical-girl effects — building on every existing system, creating nothing parallel.

**Architecture:** One water sim authority (FLIP bake on a copy) feeding one hair-water material
writer (`Water (Advance).002` family), one motion-life authority (Goo Physics bakes), existing GN
ornament carrier pattern for glob accents. UE port rides the existing
`Content/Cinematics/MelusinaWaterHair` + `ABP_Melusina_WaterHair` lane; KawaiiPhysics stays the
runtime dangle authority (no second runtime writer).

**Tech:** Blender 5.2.1 · FLIPFluids addon (domain staged, NOT yet baked) · LiquiFeel v1.3
(GUI-only — zombie headless) · Goo Physics v1.0.0 (installed) · surreal_arch 599 builders
(AppData is live, ahead of repo) · Higgsas (gate: `Tools/higgsas_gate.py`) · house GN water library.

---

## Current context — verified today (sources)

**Live file** `harp_bow_pipeline/Melusina_Harp_HERO01_ArcherPoseV09_ARP_R08_WIP_20260912.blend`
(1141 objs, dirty, nothing saved since 21:36):

- Done tonight (in-memory): wings dials restored (span x ±1.16, verified depsgraph); 3 clockwork
  arc rings built + motion-verified (`MEL_clockwork_arc_ring_outer/mid/inner`,
  `FX_ClockworkRing_*` in `FX_Hero`, Scene Time driven, counter-rotating).
- **Existing water systems (probed 23:00):**
  - `FLIPFluids` coll: `FF_MelusinaHair_Domain` (8-vert bbox shell), `FF_MelusinaHair_Drip`
    (482-vert emitter), `FF_MelusinaHair_Sheet`, child coll `FLIPMeshes`.
    **Zero FLUID modifiers exist in this file** — domain is staged, sim not wired/baked.
    Cache target per handoff: `G:\...\KitbashExport\flip_cache_melusina_waterhair` — does not exist.
  - `Melusina_HairDrip` coll: 3 × `LF_TipDrip_Hair_Strand.*` (42 verts) with
    `LF_LiquiFeel_Select Outer` + `LF_LiquiFeelv1.3` NODES modifiers. Setup tool exists:
    `Tools/setup_melusina_liquifeel_hair_drip.py`.
  - `MEL_Hair_Water_Render` coll: `Hair Strand.004/.007/.010` (3.1k/26.4k/7.6k verts,
    Armature-deformed, **hidden in viewport AND render**, sole users of `Water (Advance).002`).
  - `Melusina_WaterHair_Ref`: `NOTE_WaterHair` empty (notes).
  - House GN water library live in-file: `MEL_water_foam`, `MEL_water_ripples`,
    `MEL_water_gerstner`, 12 × `MEL_water_them_*`.
- **Geometry expansion blockers (today's handoff §6 — must clear first):**
  all 8 SHP curve systems generate ZERO geometry; water-hair render meshes hidden;
  `Melusina.001` (18.8k-vert duplicate body) render-visible 8.34 cm below base → double body;
  `Retopo_Melusina_002` 0-vert shell; six strand systems carry the −8.34 cm offset;
  30 degenerate polys on `.007`.
- **Docs reviewed today:** `Docs/Handoffs/MELUSINA_LIVE_SESSION_HANDOFF_2026-09-21.md` (geometry +
  addon method notes — incl. 5.x GN input API `mod.properties.inputs[id]["value"]` +
  `ob.update_tag()`), `Humber_FinalYear_Prep/ANMN301_Animatic/ADDON_USAGE_PLAN_v02.md`
  (addon roster: LiquiFeel zombie-headless GUI-only; mid-session addon install = crash window;
  FLIP "HOLD" ruling is scoped to the SCHOOL animatic, not this hero lane),
  `.hermes/plans/2026-09-21_composition-melusina-sheep-cameras-goo-decor.md`
  (Phases 1–7 already planned: hygiene, sheep, Sir Melodious, cameras, Goo, decor, beauty),
  `.hermes/plans/2026-09-21_melusina-root-motion-reexport-KIMI.md` (parallel UE motion lane).
- **UE-side precedent:** `ABP_Melusina_WaterHair` (148-bone skeleton), water-hair flip cache in
  `Content/Cinematics/MelusinaWaterHair`, tuned WaterHair mesh confirmed in V13 portfolio captures.

---

## Phase A — Geometry expansion gate (clears the blockers; owner GO per item)

### Task A1: Hair existence first
The 8 SHP curve systems generate zero geometry; without them there is nothing to glob.
Fix on a COPY first (`Saved/Audit/MelusinaPolish_20260920/` generation roll), diagnose via
 evaluated-depsgraph probe: guide curves present? GN modifier on each? `object.update_tag()`
after dial writes (5.x trap, handoff §7).
**Gate:** per-system evaluated vert count > 0 in `<stage>_integrity.json`.

### Task A2: Unhide + de-offset the water-hair render meshes
`Hair Strand.004/.007/.010`: restore viewport/render visibility per owner; remove the −8.34 cm
offset class on six strand systems; kill the 30 degenerate polys on `.007`.
**Gate:** evaluated bbox of all three strands overlaps the head/hair zone; degenerate count 0.

### Task A3: Single body
Owner decides Task 1.1 of the composition plan (Melusina.001 vs Retopo body) — the double body
poisons every beauty render AND every FLIP collision surface.
**Gate:** exactly one render-visible body from Cam_Beauty.

## Phase B — FLIP bake (the one sim authority)

### Task B1: Bake file = generational copy, never the live GUI file
Copy the post-Phase-A generation to
`Saved/Audit/MelusinaPolish_20260920/waterhair_flip_v01.blend`. Open GUI (owner) or headless with
`--factory-startup` and **LiquiFeel DISABLED** (zombie rule). One Blender instance; port 9876 free.

### Task B2: Wire + bake the sim
On the copy: `FF_MelusinaHair_Domain` → FLUID domain (res 72 start; cache frames 1–240; VDB/bobj
per FLIP addon default); `FF_MelusinaHair_Drip` → flow object, **parented/bone-parented to the
hair deform bones** so the emitter rides the strand motion (verify per-frame emitter bbox moves);
inflow rate authored low at tips (globbing, not gushing). Cache to the staged
`G:\...\KitbashExport\flip_cache_melusina_waterhair` dir (create it first).
**Gate:** cache dir populated with per-frame data; mesh-sequence frames count == 240; PNG frame
sample + JSON (domain res, cache format, emitter path length).

### Task B3: Mesh sequence in
FLIP mesh surfaces into `FLIPMeshes` (child coll, render-visible on this copy only), then
**import into the LIVE session as an animated mesh sequence / vertex-cache** via append —
in-memory, owner eyeballs before any save.
**Gate:** live-session frame scrub shows water riding the hair armature (evaluated bbox per frame).

## Phase C — Globulating magical-girl accents (existing carriers only)

### Task C1: GN glob beads on strands
New `MEL_hair_water_glob` builder (house pattern: zero-vert host + NODES modifier + bone parent,
dials via interface sockets): instance small ico-spheres/bead arcs along strand curves with
noise-scattered density, Scale-by-Curvature so globs cluster at tips/edges. Register pattern per
`melodia-gn-builder-workflow`; land in AppData package only while Blender is closed, deploy to
repo after gate (`Tools/higgsas_gate.py` analog check).
**Gate:** evaluated glob bbox hugs strand surfaces within 2 cm; count dials work; no intersection
with face/skirt at rest (intersect check JSON).

### Task C2: LiquiFeel — GUI-only enhancer
Keep LiquiFeel on the 3 `LF_TipDrip` hosts as the tip-drip read, GUI session only, NEVER headless.
If a headless pass needs that scene: `--factory-startup` with the addon off.
**Gate:** before/after PNG pair of a drip strand, JSON of modifier dial values.

### Task C3: Material convergence — one writer
`Water (Advance).002` remains the only hair-water material; extend IT (transmission, iridescence
dial, foam mask reading `MEL_water_foam`) rather than adding a second water shader.
Rings/wings get iridescence as a Material Variant of existing slots — no new material families.
**Gate:** material user census: hair-water = 1 family; PNG+JSON of the beauty frame.

## Phase D — Motion life (Goo bake, not a second sim)

### Task D1: Glob wobble
Goo Physics GOOFLAPPY preset on glob cluster proxies (scratch duplicates first); bake
(`goophys.bake_physics`); FLIP handles the fluid, Goo handles residual jiggle — one authority each.
**Gate:** >1 cm max displacement over 30 frames; bake cache exists; no explosion.

## Phase E — UE handoff (rides the existing lane)

### Task E1: Export contract
Alembic/geo-cache of baked water + globs into `Content/Cinematics/MelusinaWaterHair` conventions;
skeleton untouched; `use_armature_deform_only`; runtime dangle authority stays KawaiiPhysics
(Pattern A). No new UE writer.
**Gate:** import verified in an exclusive UE editor window; zero compile errors; owner eye pass.

## Phase F — VFX polish backlog (post-convergence)

- Star pendants + bead strings on shawl/skirt (composition plan Task 6.2 — registry ready).
- Brooch hero + sparkles (Task 6.1), audio-reactive dials deferred (6.3).
- Clockwork rings: material pass (iridescence), optional second ring axis; floating-regalia
  variant (Harmonic Orb staging) still queued from last night.
- FX_Hero existing carriers (KawaiiSparkles, RibbonJiggle, SanctusJewelryHero, InkformFlourish):
  audit render visibility for the beauty pass; quiet what must be quiet (FX_Hero = dressing-only).

## Files likely to change / create
- Live session (in-memory, owner saves): the WIP blend.
- `Saved/Audit/MelusinaPolish_20260920/`: `waterhair_flip_v01.blend`, `comp_*.py`, `*_integrity.json`.
- Cache: `G:\...\KitbashExport\flip_cache_melusina_waterhair\` (created by Task B2).
- AppData `surreal_arch/melodia_gn/`: `MEL_hair_water_glob` builder (Task C1, closed-Blender only).
- Plan artifacts: every render ships PNG + JSON.

## Risks / open questions
1. Owner GO gates: A1 unhide set, A3 body choice, B2 bake cost (res 72 × 240 frames ≈ GBs on G:),
   C1 builder landing — none run without it.
2. LiquiFeel zombie: any headless run with it enabled hangs — enforced by --factory-startup + off.
3. Port 9876 double-bind: only the WIP file answers; RESTAGE_STARTER session is dark.
4. G: free space before bake (check before B2; window skill exists if low).
5. FLIP addon ruling in ADDON_USAGE_PLAN_v02 is school-lane-scoped; hero lane here is owner-
   directed ("go" 2026-09-21). Do not carry the school HOLD into this lane silently.
6. The 21:36 on-disk save predates tonight's wings/rings — a crash before the owner saves loses
   them again. Save/bank first is the standing recommendation.
