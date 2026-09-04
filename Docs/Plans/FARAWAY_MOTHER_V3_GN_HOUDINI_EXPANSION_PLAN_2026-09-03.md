# Faraway Mother V3 — Geometry Nodes + Houdini Expansion Plan
**Author:** Geometry Nodes architect + Houdini proceduralist (one owner, single writer)
**Date:** 2026-09-03
**Status:** Plan (offline-ready where possible; editor-gated steps flagged)
**Prerequisites on disk:** 17 MEL_mother_* GN builders exported (`Exports/FarawayMother/SM_MEL_mother_*.fbx`), core.py extended with string params + P2 export pass + named attrs, VDM A/B/C + KleinVeil baked in `Saved/Audit/vdm_fabric/`, 8 Copernicus Faraway fabric sets already in `Saved/Audit/copernicus_cymatic/Faraway*/`.
**Constraint (non-negotiable):** No new landscapes without permission. All mountain-level geometry is MeshTerrain/Nanite/FBX-imported, with height-aware placement only. No floating pieces. No placeholder assets carried forward.

---

## 1. Executive summary

V2 ended with three truths:

1. **The GN library already works.** 17 builders export cleanly. The remaining work is depth (more builders, more systems, better LOD and audio coherence), not proof that GN can make a mountain.
2. **The Houdini bake pipeline is real where it touches proven assets and scaffolding where it points at files that don't exist on disk.** VDM A/B/C are baked. The Copernicus Faraway fabric sets are baked. The Copernicus fabric sheen script targets missing texture paths — so treat the sheen job as "fix paths or bake fresh", not "run the script and expect output".
3. **The editor is down for part of this.** Offline work (Blender 5.2, Houdini hython/apprentice, PIL/numpy) proceeds now. Editor-gated work (UE import, PCG assembly, Nanite collision ref, MPC wiring, baked-CoP texture ingest) waits.

V3 therefore is **not a rewrite**. It is an expansion: add builders until the monolith has a full body (head, hair, torso, valley, limbs, gate, trail, architecture, lighting, volumetric haze), add systems that make those builders behave as one mountain (spline assembly, height-aware scatter, LOD-aware selection, audio/Tension attributes), then bake a Houdini pass that turns the best GN shapes into baked Nanite-ready terrain and complementary VDM/curved detail.

---

## 2. V3 GN library architecture

Group builders by role, not by file. A builder can live in an existing module but belong to a role.

### 2.1 Terrain / body layer (the reclining silhouette)

Already present:
- `MEL_mother_head_silhouette` — sculpted ridge, moonlit face profile
- `MEL_mother_fabric_ridge` — fold terrain "skin"
- `MEL_mother_shoulder_fold` — shoulder/chest fold terrain
- `MEL_mother_valley_depression` — torso valley depression with fog attribute
- `MEL_mother_hair_cascade` — ribbon waterfall "hair"
- `MEL_mother_fog_volume` — volumetric haze box (no mesh, suggestion)

Missing for a complete body:
- torso valley floor (walkable, subtle folds + micro noise; this is a gameplay lane, not just "more terrain")
- limb haze anchors (three placement spars — no mesh, just fog volume origins)
- moon disc + halo ring (low horizon, silver-blue)
- hair anchor strand curves (so hair cascade follows head → valley deterministically)
- walkway supports under the existing walkway builders (fabric-wrapped pylons)

Keep: no Landscape. Terrain from imported MeshTerrain/Nanite FBX for the macro silhouette; GN builders for local folds/gates/depressions on top, all height-aware.

### 2.2 Garment / dress layer (the fabric that drapes the body)

Already present:
- `MEL_mother_tapestry_wall` — hanging seam (1 builder, not yet in manifest biome)
- walkway straight / curved (fabric walkway, tension sags)
- frill rock / frill arch (walk-through arch formations)
- lace tree / pearl bush / silk vine / brocade flower (forest-dress details)

V3 additions:
- veil seam at heart gate (open edge, pinned vertex group `PIN`; Chaos-ready, WPO until then) — this is the Hemkeeper test piece
- draped fabric curtain/portico that can be placed at the shoulder valley entrance
- brocade runner: a narrow long fabric strip that can trace a path (spline-driven)
- veil detail spray: small lace/frill instances around the heart gate veil seam

### 2.3 Trail / architecture layer (paths through the mother)

Already present:
- walkway straight / curved
- frill arch

V3 additions:
- swooping fabric ramp (short arc, low rise, high width) — for traversal gain
- woven fabric "bridge" segment — thin curved ribbon with rail bolsters
- cradle / cradle arch (already exists in Copernicus HDA list; add GN builder that matches its profile, not reimports the whole HDA unless needed)

### 2.4 Volumetrics / lighting layer (readability at distance)

Already present:
- fog volume box
- moonlight rig (lighting rig, currently fails export due to missing MeshPlane — fixed via Grid card substitution in this session)

V3 additions:
- volumetric haze volume instances keyed to limb anchors
- moon rim halo (a thin curved ribbon at horizon, low opacity, silver-blue)
- a faint "breathing" volumetric haze that pulses with BeatPulse (attribute-driven density, same source as MPC)

### 2.5 Hero mechanics layer (rhythm gate family)

Already present:
- heart gate (arch + pillar family, glow attribute)

V3 additions:
- rhythm gate "finial veil" (the veil seam above — the gameplay-significant piece)
- gate "moon key" orb: a small artifact that can be placed at the heart gate center, with a glow attribute and a named `p2_builder` tag for later MPC/beatpulse wiring

### 2.6 Shared attributes (V3 GN hygiene)

Every MEL_mother builder that shipped in V2 now gets (via apply_p2_export_pass):
- `BuilderName` (string)
- `Biome` (string)
- `Tension` (float, 0–1, mults fold depth downstream)
- `RealizeForExport` (bool)
- named attrs on output geometry: `p2_builder`, `p2_tension`, `p2_chladni_uv`

V3 extends this to all new builders too, plus:
- `AudioTension` (float) — drives fold depth mult
- `BeatPulse` (float) — drives micro noise mult
- `LOD` (int, 0/1/2) — switches grid res for export/distance variants where sensible

This makes downstream UE, PCG, and MPC able to read intent without parsing node names.

---

## 3. New GN builders to author (V3 additions)

Write these as pure GN. Reuse existing masters. No new materials unless a hero mechanic genuinely needs it (likely not for V3).

### 3.1 Terrain/body

- `MEL_mother_torso_floor` — wide shallow bowl/flat floor, gentle dish + micro pleats; primary walk lane.
  Inputs: Width, Depth, Fold Depth, Fold Count, Micro Noise, Floor Flatness
- `MEL_mother_limb_haze_anchor` — three named placement points (no mesh): origin + two spars for volumetric haze volumes.
  Outputs: named points (store point count + index), set a string attribute `limb_anchor`
- `MEL_mother_moon_disc` — low horizon disc, halo ring, silver-blue tint attribute.
  Inputs: Radius, Halo Width, Halo Segments, Tint
- `MEL_mother_hair_anchor` — curve from head to valley that hair cascade can follow.
  Outputs: curve as "hair_path"; store `p2_builder` = "MEL_mother_hair_anchor"
- `MEL_mother_walkway_pylon` — fabric-wrapped support under walkways.
  Inputs: Height, Base Radius, Wrap Taper, Wrap Count, Fabric Tension

### 3.2 garment/dress

- `MEL_mother_veil_seam` — open-edge veil at heart gate; pinned vertex group `PIN`; Chaos-ready.
  Inputs: Span, Height, Opening Width, Veil Length, Edge Frill, Tension, Pin Offset
- `MEL_mother_draped_curtain` — archway drape with gather and fall.
  Inputs: Span, Height, Gather, Fall Depth, Fold Count, Fold Sharpness, Tension
- `MEL_mother_brocade_runner` — narrow long fabric strip, spline-traceable.
  Inputs: Length, Width, Fold Depth, Fold Frequency, Tension, Profile Resolution
- `MEL_mother_veil_detail_spray` — lace/frill instances near veil seam.
  Inputs: Spray Radius, Density, Instance Scale, Tension

### 3.3 trail/architecture

- `MEL_mother_swooping_ramp` — low-rise fabric ramp.
  Inputs: Length, Width, Rise, Fold Depth, Fold Frequency, Tension
- `MEL_mother_fabric_bridge` — curved ribbon with rail bolsters.
  Inputs: Span, Width, Rail Height, Rail Count, Fold Depth, Tension

### 3.4 volumetrics/lighting

- `MEL_mother_limb_haze_volume` — placed at limb anchors; attribute-driven density; optional BeatPulse mult.
  Inputs: Size X/Y/Z, Base Density, BeatPulse, Tint
- `MEL_mother_moon_halo` — thin horizon ribbon.
  Inputs: Radius, Ribbon Width, Segments, Tint Strength, Curl

### 3.5 hero mechanics

- `MEL_mother_heart_gate_orb` — small artifact at gate center; glow attribute; `p2_builder` tag.
  Inputs: Radius, Glow Intensity, Pulse Frequency

---

## 4. V3 systems beyond individual builders

Single builders aren't enough. V3 needs systems that assemble and place them coherently.

### 4.1 Spline-driven fabric placement system

A GN "kit" that places fabric builders along a user curve:
- curve input (or generated path)
- builder selector (dropdown/string): `MEL_mother_walkway_straight`, `MEL_mother_brocade_runner`, `MEL_mother_draped_curtain`, etc.
- per-point transform (position + rotation + scale), driven by curve tangent
- stores `p2_builder` + `biome` per placed instance
Use case: trail corridor, gorge path, brocade runner tracing a ridge seam.

### 4.2 Height-aware scatter system (terrain-aware instances)

Build a GN scatter that:
- takes a terrain mesh (imported Nanite terrain or local builder geometry)
- raycasts each candidate point down to terrain (never float)
- filters by slope + height + biome attribute
- spawns builders / detail props / foliage with the existing 17 + V3 new builders
This is the "no floating pieces" guarantee in code. It is the rule for every scatter, not a custom per-level hack.

### 4.3 LOD-aware builder selection

A GN "LOD layer" wrapper that picks builder variants by LOD int:
- LOD0: high-poly folds + micro detail
- LOD1: medium
- LOD2: low + rely on material/macro
This is most useful for export variants and for runtime selection where UE-side LOD switching exists. For V3, implement the GN-side LOD input param on the leaders (terrain ridge, valley floor, hair cascade); simpler builders keep one resolution.

### 4.4 Audio/Tension coherence system

A small GN helper that:
- takes `Tension`, `AudioTension`, `BeatPulse`
- multiplies fold depth, micro noise, and (for volumetric builders) density
- propagates a named attribute `p2_audio` so downstream material/PCG can read it
This makes the mountain "breathe" in GN even before MPC wiring. Keep it additive; don't make GN replace MPC.

### 4.5 Body-map attribute consistency

Define the body-map intent as a table of builder roles + expected XZ relationship, so placement isn't ad hoc:
- head silhouette at one end of the XZ composition
- hair cascade flows from head downward
- shoulder fold beside head
- torso valley below shoulder
- valley floor under torso
- limb haze anchors at the implied limb extents
- heart gate at "heart"
- moon disc on horizon
This is the same spirit as the production sheet body map; V3 makes it enforceable via attributes + placement order.

---

## 5. Houdini + Copernicus expansion

### 5.1 What is real now

- VDM A/B/C + KleinVeil baked to `Saved/Audit/vdm_fabric/` (2048² RGBA32F npy + png). These are real and usable.
- 8 Copernicus Faraway fabric sets exist in `Saved/Audit/copernicus_cymatic/Faraway*/` (10 maps each incl. Sheen). These are real and usable.

### 5.2 What is scaffolding / path-broken

- `Tools/Houdini/copernicus/copernicus_fabric_sheen.py` builds a COP that reads BaseColor + Sheen from `Content/Textures/FarawayMother_Suites/...`. Those texture files do not exist on disk in that layout. So either fix the paths to point at the real `copernicus_cymatic/Faraway*` sets, or bake a fresh sheen from existing sets, or use PIL compositing (the script's own fallback mention).

### 5.3 Houdini expansion targets

1. **Heightfield bake pass for the macro silhouette.** Goal: one cooked heightfield that becomes the Nanite-ready terrain backing the body silhouette.
   - Source: the body silhouette intent (head/shoulder/hip/body humps + valley) — can be authored offline as a 2k/4k numpy heightmap in the same style as `Tools/_gen_faraway_heightmap.py`, then cooked by hython `copernicus_terrain_height_to_nanite.py` into an OBJ/Nanite-ready FBX for import.
   - This is the offline route when Apprentice 1080p blocks larger COP renders. Prefer the offline heightmap + OBJ/Nanite import path unless we confirm hython can cook a larger result.
2. **VDM expansion.** Add variants for new fabric roles if we author new sets:
   - Ridge (deep folds)
   - Valley (gentler)
   - Haze drape (very low freq)
   - Veil seam (high micro, lower lateral)
   Recycle the same `build_vdm()` recipe from `Tools/cook_faraway_fabric_vdm.py`. This is offline-safe.
3. **Copernicus fabric catalog consolidation.** The 8 real sets are the catalog. V3 should map each set to a role/terrain/drape variant and bake only what's missing (e.g. a fresh base/sheen if we want a new role). Do not pretend the sheen script can run as-is against missing textures.
4. **HDA bake (targeted, not blanket).** The Copernicus HDA list includes faraway_p2_corset/cradle/gown/mantle/ornament/veil hips. For V3, only bake a HDA if it produces geometry we can't get cheaper from GN + Nanite. Prefer GN + baked terrain for the body; reserve HDA for a few hero details (cradle, gown silhouette accent) where Houdini gives a better silhouette.

### 5.4 Offline Houdini priority list

1. Confirm hython works headless for the VDM/terrain path (`hython Tools/Houdini/copernicus/copernicus_terrain_height_to_nanite.py ...` or the vdm recipe).
2. Bake a fresh macro silhouette heightmap (numpy) and cook it to OBJ/Nanite-ready FBX.
3. Bake any new VDM variants needed by new fabric sets.
4. If we want fresh sheen, bake from the 8 existing sets (PIL compositing or corrected COP paths), not from the broken script paths.

---

## 6. Bake chapter

### 6.1 Heightmap / terrain bake (offline)

Inputs: body silhouette intent → numpy heightmap (2k/4k).
Outputs:
- `T_FarawayMother_MacroSilhouette_Height.png` (16-bit, fabric folds: body humps + 2–3 pleat octaves + torso valley)
- `SM_FarawayMother_MacroSilhouette.obj` (Nanite-ready interchange fallback) in `Saved/Audit/faraway_mother/`

This is the backing terrain for the body. GN builders sit on top.

### 6.2 VDM bake (offline)

Inputs: fabric role params (foldFreq, depth, Chladni modes, mask thresholds).
Outputs: `T_FarawayMother_Fabric_VDM_<role>.{npy,png}` in `Saved/Audit/vdm_fabric/`.
Existing: A/B/C/KleinVeil.
Add: veil seam, haze drape if needed for new fabric variations.

### 6.3 Copernicus fabric bake (offline, using existing sets)

Inputs: existing 8 Faraway sets in `Saved/Audit/copernicus_cymatic/Faraway*/`.
Outputs: either (a) confirm the 8 sets are sufficient as the fabric catalog, or (b) bake a small number of new base/sheen maps for new roles, from the existing sets or from corrected COP paths.
Decision: for V3, treat the 8 sets as the catalog. Only bake new maps if a new role needs a distinct look that the 8 can't cover.

### 6.4 Material instance plan (offline spec → editor execution)

Offline spec is the `faraway_fabric_variation_manifest.json` already written:
- 8 sets, each with WPO layer params, LOD tier, MPC channel intent, instance name, parameter overrides, cloth tier note.
Offline: the manifest is the SSOT for which builder / set / instance goes where.
Editor: build the material instances over `M_Master_Nikki_Landscape`, assign to imported terrain + GN builder placements.

---

## 7. Stage + export chapter

### 7.1 Stage A — Blender export (offline, done / repeatable)

Already proven: `Tools/export_mother_builders.py` exports all 17 to `Exports/FarawayMother/SM_MEL_mother_*.fbx` with manifest + audit.
V3: rerun after new builders added, plus new builders' FBX. Keep manifest updated.

### 7.2 Stage B — Blender-to-UE FBX prep (offline, mostly done)

Every exported FBX should be:
- axis-correct for UE (FBX export with -Z forward, Y up, or the project's known convention)
- scale-uniform
- named cleanly (`SM_MEL_mother_<name>.fbx`)
- accompanied by the manifest entry (verts/polys/sha)

### 7.3 Stage C — UE import + Nanite + collision (editor-gated)

For each FBX:
- import to `/Game/EnvSandbox/Meshes/FarawayMother/SM_MEL_mother_<name>`
- Nanite ON
- complex collision for raycast (height-aware rule)
- custom props carried over if possible: `p2_builder`, `p2_biome`, `p2_tension`
This is editor-gated.

### 7.4 Stage D — material instances + placement + PCG (editor-gated)

From `faraway_fabric_variation_manifest.json`:
- build 8 MI over `M_Master_Nikki_Landscape`
- place GN builders in the level per the body-map + P2 layout
- set cloth tiers (A rigid / B Chaos pending / C WPO / D VAT) per the cloth-tiers doc
- register PCG graphs if doing scatter (height-aware)

### 7.5 Export manifest (V3 final)

A V3 export manifest should list, per builder:
- name
- role
- source FBX
- UE path
- placement kind (hero / scatter / terrain / volumetric / lighting / trail)
- LOD interest
- material instance / override
- audio attribute intent (Tension/BeatPulse)
This manifest is the bridge between GN/Houdini and the stage script.

---

## 8. Editor-gated vs offline split

### 8.1 Offline now (editor down)

- Write V3 new GN builders in Blender 5.2 (mother.py additions or new module).
- Extend core if needed (already has string param + export pass).
- Re-export with `export_mother_builders.py`.
- Bake heightmap/VDM/fabric from Houdini/PIL/numpy.
- Write/update V3 export manifest + fabric variation manifest.

### 8.2 Editor-gated

- UE import of FBX + Nanite + collision.
- Material instance creation.
- Level placement of GN builders + PCG assembly.
- MPC wiring (MPC_Melodia_Palette single writer; no second MPC).
- LOD + WPO parameter verification.

---

## 9. Success criteria (V3)

- All new builders build + export cleanly (no build-time GN node errors).
- Export manifest covers 17+ new builders with role/placement/material/audio intent.
- One baked macro silhouette heightmap + Nanite-ready OBJ/Nanite-ready fallback exists.
- VDM variants exist for the fabric roles we need.
- Copernicus fabric catalog is 8 real sets, mapped to roles, not broken script paths.
- Editor-gated stage produces a level where:
  - terrain is MeshTerrain/Nanite (no Landscape without permission)
  - no pieces float (height-aware raycast)
  - cloth tiers per cloth-tiers doc
  - MPC single writer
  - LOD continuum is visible from valley to horizon

---

## 10. Risky corners

- Copernicus fabric sheen script pointing at missing texture paths — fix paths or bake fresh, don't pretend it works.
- Apprentice 1080p cap if we try a larger COP render — prefer offline numpy heightmap + OBJ/Nanite import.
- Don't create a Landscape for the mountain without explicit owner permission — body silhouette is Nanite terrain / imported mesh.
- Don't introduce a second MPC or second audio-reactive master for Faraway Mother — single writer rule.
- Don't carry placeholder assets; if a builder is meant to suggest mass without mesh (fog/haze), tag it clearly and don't ship an empty mesh by accident.

---

## 11. Suggested order (today)

1. Offline: author the V3 new builders that matter most for a complete body — torso floor, limb haze anchors, moon disc/halo, hair anchor, walkway pylons. (Pure GN.)
2. Offline: add veil seam + draped curtain + brocade runner to garment layer.
3. Offline: re-export all (existing + new) with `export_mother_builders.py`; refresh manifest.
4. Offline: bake macro silhouette heightmap + any new VDM variants; confirm Copernicus catalog is the 8 real sets.
5. Editor-gated (when :9316 up): import + Nanite + collision + material instances + placement + PCG + MPC wiring.

If you want, I can start the offline GN builder authoring now (torso floor, limb haze anchors, moon disc/halo, hair anchor, walkway pylons) and re-export, while the editor stays down. That's the highest-leverage offline pass for a more complete mountain before any UE import.
