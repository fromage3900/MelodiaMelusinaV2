# Mara Elletra Vell — Houdini Hero Asset + Garment + Cymatics Execution Plan

**Date:** 2026-08-31  
**Project:** Melodia Melusina / UE5.8 / Houdini 22  
**Status:** PC execution plan; buildable after local source-asset path cleanup  
**Scope:** Mara/Elletra hero instruments, Melusina instrument family, advanced garment construction, authoring-time cymatic geometry, and runtime cymatic presentation integration  
**Hard rule:** Houdini remains an authoring/compiler tool. Unreal remains gameplay/runtime/shipping authority. No runtime Houdini cook dependency.

---

## 0. Decision

Build the new concept-sheet assets as a **modular hero-asset compiler**, not twelve isolated hand models.

The common language is:

```text
CHARACTER / OUTFIT SOURCE
        |
        +--> Garment panel compiler ----> cloth / shells / scales / embroidery / morph states
        |
CONCEPT SILHOUETTE
        |
        +--> Instrument skeleton -------> frame / resonator / strings / chimes / ornament / grip
                                            |
                                            +--> shared cymatic pattern contract
                                                        |
                            +---------------------------+---------------------------+
                            |                                                       |
                    authoring geometry                                      runtime presentation
                    engravings / cutouts /                                  Niagara / materials /
                    emissive masks / ribs                                   local animation
                            |                                                       |
                            +------------------------> UE5.8 <----------------------+
```

The first useful goal is not "finish every weapon." It is to prove one full asset loop where **the same cymatic pattern that physically shapes the prop in Houdini also becomes readable when the player performs music in Unreal**.

Recommended first hero proof:

> **Mara/Elletra Resonance Astrolabe / Sonic Scepter** + one procedural garment resonance state + `OnLaneHitJudged` runtime pulse.

Once that works, the rest of the concept family becomes parameterized variation rather than reinvention.

---

# 1. Existing project reality we must build on

The current Shorewake dress work already proves a useful Blender -> Houdini -> Blender -> UE pattern:

```text
owner garment FBX
 -> Blender pose/inventory export
 -> Houdini procedural detail pass
 -> Blender rig/weight/morph assembly
 -> UE skeletal import
```

Existing Houdini work has already generated procedural ridges and thousands of scale plates, while the downstream Blender pass assembles the rigged magical dress and morph targets.

However, the current audit also identifies several problems that must be fixed before this becomes the template for Mara/Elletra production:

1. owner-machine source paths are hardcoded;
2. source files are not hash-pinned;
3. panel-driven morph logic incorrectly assumes uniform vertex counts;
4. the Houdini biharmonic weight lab has never been completed end-to-end;
5. a downstream `apply_houdini_weights.py` path does not exist;
6. current magical geometry is extremely dense for a runtime garment;
7. panel ordering differs between older script lanes;
8. output provenance is scattered.

Therefore this plan creates a **v2 character-prop pipeline** instead of extending those brittle assumptions.

---

# 2. Concept families to build

## 2.1 Mara / Elletra hero instrument family

Use the recent design sheets as the visual exploration set, but collapse them into common construction families.

### Family A — axial / survey instruments

- Resonance Astrolabe
- Sonic Scepter
- Cartographer's Rod
- Lattice Rod
- Monolith Tuner
- Monolith Caliper
- Field Compass

**Shared construction language:** central shaft, floating ring stack, pendulum/weight, survey head, cymatic resonator, calibration ornaments.

### Family B — string / frame instruments

- Ripple Lyre
- Wave Harp
- Measureless Lute
- Pearl Harp
- Choral Cage

**Shared language:** load-bearing outer frame, string bridge, resonator plate, tension nodes, hanging weights/chimes.

### Family C — resonant body / percussion instruments

- Phase Bell
- Veil Drum
- Tidal Disc
- Shell Drum
- Coral Conch
- Echo Orb

**Shared language:** membrane or shell body, radial cymatic plate, suspension system, apertures/ports, acoustic/cymatic response surface.

### Family D — transform / fan / anomalous forms

- Crescendo Fan
- Harmonic Seeder
- Current Flute
- Coral Siphon / shell variants

These are secondary after the common frame + cymatic pattern library works.

## 2.2 Garment targets

### Garment G0 — Shorewake v2 technical canary

Use the already-proven 48-panel dress as the **pipeline validation garment** because the source/rig/history is known.

Do not redesign it first. Fix the data contract, panel semantics, weight path, optimization and cymatic overlay on this known garment.

### Garment G1 — Mara/Elletra Surveyor Mantle

Build the long layered surveyor coat/mantle from the concept boards as the first new garment:

- wide layered sleeves;
- asymmetric mantle panels;
- hanging calibration tassels;
- structured collar/shoulder geometry;
- soft inner cloth + stiffer shell-like outer layers;
- instrument harness attachment points;
- cymatic embroidery/filigree paths;
- optional resonant floating ornaments.

### Garment G2 — Melusina resonance dress extension

After G0/G1, reuse the garment compiler to create:

- iridescent scale-panel zones;
- shell/pearl trim;
- cymatic node embroidery;
- resonance-state morphs;
- controlled fabric bloom / fan-out states.

---

# 3. New repository/source layout

Create this on the implementation branch when work begins:

```text
Tools/Houdini/mara_elletra/
  README.md
  config/
    mara_elletra_asset_manifest.v1.json
    cymatic_pattern_presets.v1.json
    material_slot_contract.v1.json
  instrument/
    build_instrument_family.py
    instrument_variant_table.json
    hda/
  garment/
    build_garment_panels.py
    build_garment_details.py
    build_garment_resonance_states.py
    garment_variant_table.json
  cymatics/
    build_cymatic_field.py
    build_cymatic_resonator.py
    export_cymatic_masks.py
  export/
    export_unreal_assets.py
  qa/
    validate_asset_contract.py
    validate_scale_pivots.py
    validate_panel_ids.py
    validate_runtime_budget.py
```

Authoring files should live under a predictable source tree outside `Saved/`, for example:

```text
ArtSource/MaraElletra/
  Character/
  Garments/
  Instruments/
  Cymatics/
  References/
```

Do not depend on `Downloads`, `Desktop`, or ad-hoc OneDrive locations.

Every source entry in `mara_elletra_asset_manifest.v1.json` should include:

```text
asset_id
source_path
source_sha256
source_tool
source_tool_version
units
up_axis
panel_or_part_count
rig_revision
material_contract_revision
cymatic_pattern_revision
output_paths
```

---

# 4. Houdini HDA architecture

Do not make one giant "Mara generator." Keep the HDAs composable.

## 4.1 Instrument HDAs

```text
HDA_MEL_Instrument_Frame_v001
HDA_MEL_Instrument_RingStack_v001
HDA_MEL_Instrument_StringArray_v001
HDA_MEL_Instrument_ChimeArray_v001
HDA_MEL_Instrument_Resonator_v001
HDA_MEL_Instrument_Ornament_v001
HDA_MEL_Instrument_GripMount_v001
HDA_MEL_Instrument_VariantCompiler_v001
```

### `Instrument_Frame`

Inputs:

- silhouette guide curve;
- centerline;
- optional symmetry plane;
- grip transform;
- resonator transform.

Responsibilities:

- resample guide curves;
- generate structural rails with Sweep;
- profile taper along normalized curve U;
- produce clean junctions with VDB/Boolean only where necessary;
- bevel and normal preparation;
- tag parts by semantic group.

Required groups/attributes:

```text
mel_part = frame|grip|resonator|ring|string|ornament|chime|blade
mel_variant_id
mel_material_family
mel_cymatic_receiver
mel_anim_channel
```

### `RingStack`

Produces:

- astrolabe rings;
- nested orbitals;
- tuning halos;
- dial/gimbal pieces;
- pendant attachment points.

Expose:

```text
ring_count
ring_radii[]
ring_thickness
ring_tilt[]
ring_gap
ornament_density
open_angle
```

### `StringArray`

Builds lyres/harps/cages with deterministic string indexing.

Output:

```text
mel_string_id
mel_string_frequency_ratio
mel_string_tension_norm
mel_string_rest_length_cm
```

These values can later map to UE material/VFX animation without claiming to be an audio simulation.

### `Resonator`

This is the key shared component. It creates:

- engraved cymatic channels;
- embossed nodal ridges;
- perforated apertures;
- emissive inlay masks;
- optional thin glass/pearl membrane;
- UVs aligned to the pattern domain.

The same pattern preset must be exportable as a texture/mask and as geometry.

---

# 5. Cymatic pattern authoring contract

Create a project-owned authoring contract:

```text
melodia.cymatic-pattern.v1
```

Minimum fields:

```json
{
  "pattern_id": "MEL_CYM_001",
  "seed": 20260831,
  "domain": "disc",
  "mode_family": "interference",
  "frequency_ratios": [1.0, 1.25, 1.5, 2.0],
  "amplitudes": [1.0, 0.82, 0.58, 0.18],
  "phases": [0.0, 0.0, 0.0, 0.0],
  "node_threshold": 0.08,
  "crest_threshold": 0.72,
  "rotation_deg": 0.0,
  "symmetry": 6,
  "revision": 1
}
```

## 5.1 Authoring field

The first pattern does not need a physically exact Chladni plate solver.

Use the same readable interference idea already planned in Unreal:

```text
W(P) = sum_i A_i * sin(k_i * distance(P, Origin_i) + Phase_i)
```

Then derive:

```text
Node = abs(W) < node_threshold
Crest = abs(W) > crest_threshold
```

In Houdini:

1. create a 2D sampling domain on the resonator plate;
2. compute `W` in VEX or Python;
3. store `mel_cymatic_value` and `mel_cymatic_node`;
4. convert node bands into curves/masks;
5. resample/smooth curves;
6. Sweep them into shallow engraved/inlaid channels;
7. export the exact scalar field or mask for Copernicus/UE comparison.

Later pattern families can include radial/rose modes, circular membrane approximations, authored vector fields and Monolith-distorted modes.

## 5.2 One pattern, four uses

Every accepted pattern should be able to generate:

```text
A. hero-prop physical engraving
B. emissive/iridescent mask
C. garment embroidery / scale orientation guide
D. UE runtime cymatic presentation preset
```

This is the main architectural win: the art asset and the runtime effect are visibly related because they share a data definition.

---

# 6. Advanced instrument geometry pipeline

## Stage I0 — blockout compiler

For each concept variant, author only:

```text
centerline curve
outer silhouette curve(s)
resonator location/diameter
hand/grip location
major hanging masses
string/chime region
```

Do not sculpt ornament before proportions pass in the character hand.

Generate rough meshes with:

- Sweep;
- Copy to Points;
- Transform Pieces;
- PolyExtrude;
- PolyBevel;
- Curve Boolean / Boolean where justified;
- VDB only for junction cleanup, then remesh/retopo as needed.

**Gate:** silhouette must read at gameplay camera distance before detail.

## Stage I1 — structural parametric pass

Add:

- ring stacks;
- frame rails;
- ribs;
- string bridges;
- chime rails;
- mechanical pivots;
- grip guards;
- hanging ornaments.

All repeated pieces must be instanced/copied procedurally rather than hand duplicated.

## Stage I2 — cymatic resonator pass

Feed the selected `cymatic_pattern_presets.v1.json` entry into `HDA_MEL_Instrument_Resonator_v001`.

Generate:

- 0.5–2.0 mm engraved channels for close hero shots;
- broader 2–8 mm raised/inlaid bands where silhouette matters;
- simplified emissive-only pattern for gameplay LODs;
- optional perforation only if it survives import and does not cause excessive microgeometry.

## Stage I3 — ornament compiler

Create a small ornament grammar instead of unique decoration everywhere:

```text
pearl bead
shell petal
teardrop crystal
calibration weight
spiral filigree
crescent blade
star/compass point
ring clasp
```

Expose attachment points on the frame with `mel_socket_*` attributes.

The variant compiler can then redistribute this language across all twelve instruments while preserving family identity.

## Stage I4 — game mesh split

Do not export the Houdini hero model as one monolithic mesh.

Recommended split:

```text
Rigid hero shell        -> static mesh / optional Nanite where appropriate
Moving rings/dials      -> skeletal or separate static components
Strings/chimes          -> low-cost geometry + material/secondary animation
Resonator glass/pearl   -> separate transparent/translucent surface
Emissive inlay          -> mask/material, not dense geometry at runtime
Tiny filigree           -> bake or simplify where it does not affect silhouette
```

Create high/medium/game representations from the same HDA parameters.

---

# 7. Advanced garment pipeline

## Stage G0 — repair the known Shorewake data contract

Before new garment generation:

- replace hardcoded source paths with manifest-relative paths;
- hash the owner FBX/USDZ;
- use real panel IDs/ranges, never `vertex_index / average_panel_size`;
- standardize numeric panel sort;
- add manifest to every Blender/Houdini geometry lane;
- either complete the Houdini weight handoff or remove the dead-end path;
- archive/provenance-tag orphan outputs instead of treating them as production sources.

This lets Shorewake become a reliable canary for the new garment framework.

## Stage G1 — panel semantics

Every panel entering Houdini must carry stable metadata:

```text
mel_panel_id
mel_panel_name
mel_panel_region = bodice|sleeve|mantle|hem|collar|inner|outer
mel_panel_layer
mel_panel_stiffness
mel_panel_detail_family
mel_panel_cymatic_weight
mel_panel_runtime_material
```

This becomes the equivalent of the environment semantic-field doctrine, but for garments.

## Stage G2 — Vellum construction / drape

For new Mara/Elletra garments:

1. start from clean pattern panels or derive planarized source panels;
2. establish seam pairs explicitly;
3. assign per-region cloth properties;
4. pin/attach only required body regions;
5. drape on a proxy character body;
6. resolve self-collision and sleeve/torso penetration;
7. cache the approved rest/posed state;
8. never require the runtime game to execute the Vellum solve.

Suggested cloth families:

```text
inner silk       -> soft / high drape
outer mantle     -> medium stiffness
structured collar-> high bend stiffness
translucent veil -> light / soft, simulation-safe thickness
shell trim       -> rigid geometry, not cloth
hanging tassels  -> separate curves/secondary pieces
```

## Stage G3 — procedural garment detail

### Shell/scales

Replace brute-force dense plate growth with a controllable density hierarchy:

```text
Hero plates       -> real geometry near silhouette / focal areas
Mid plates        -> simplified instanced geometry
Micro scales      -> normal/height/emissive material treatment
```

Drive plate orientation from surface frame + optional cymatic gradient.

### Embroidery / resonance lines

Project cymatic node curves onto garment panels.

Create:

- stitched curves;
- pearl chains;
- emissive piping;
- cut lace bands;
- material masks.

The same pattern should be recognizable on the resonator and the garment without literal duplication.

### Ruffles / fins / veil elements

Use guide curves + Sweep / Copy to Points for stable repeated edge language. Keep these modular so silhouette can be tuned without rebuilding the base garment.

## Stage G4 — resonance morph/state generation

Use Houdini to generate authored transform states rather than runtime cloth chaos.

Target states:

```text
Neutral
Measure
Harmonize
ResonanceBloom
Crescendo
MissDisruption (presentation-safe, subtle)
```

Possible deformations:

- panel fan-out;
- sleeve/veil lift;
- scale orientation change;
- local inflation;
- resonant ripple along hem;
- selected ornamental ring/chime motion.

These can become morph targets, bones or controlled material/WPO channels depending on the deformation.

## Stage G5 — skinning path decision

Resolve the current dead-end before production.

### Preferred canary A — Houdini/KineFX owns capture

- import skeleton;
- use biharmonic/joint capture;
- clamp influences to project limit;
- deform-test in Houdini;
- export FBX with skin;
- reopen in Blender and UE;
- compare bind pose and animation.

### Fallback B — Blender owns final skin

- Houdini exports deterministic panel/detail meshes with stable names;
- Blender transfers or reconstructs weights;
- a real committed `apply_houdini_weights.py` is created if JSON weight transfer remains necessary;
- QA fails if zero-weight vertices or >allowed influences exist.

Do not maintain a half-Houdini / half-Blender weight workflow with no executable bridge.

---

# 8. Material / Copernicus integration

Use Copernicus as the geometry-aware mask generator around the Houdini outputs.

For each hero prop/garment, generate a compact material family:

```text
BaseColor
Normal
ORM or project equivalent
CymaticMask
IridescenceMask
EdgeWear / cavity mask
Optional EmissionMask
```

Do **not** ship the 48 authoring material slots as 48 runtime draw calls.

The 48-slot Shorewake lane remains useful for Substance authoring/selection, but runtime assets should collapse to a small material set such as:

```text
MEL_Cloth
MEL_PearlShell
MEL_Metal
MEL_Glass
MEL_Emission
```

with packed masks/IDs controlling local variation.

---

# 9. Unreal cymatics integration

## 9.1 Authority boundary

Use the existing presentation seam:

```text
UMelodiaRhythmCombatSubsystem::OnLaneHitJudged
```

The hero asset may react to:

```text
LaneIndex
Grade
TimingErrorMs
```

but it must not recalculate judgement, timing or damage.

## 9.2 Runtime prop response

Create a reusable presentation component/Blueprint, for example:

```text
BP_MelodiaCymaticHeroInstrument
```

Responsibilities:

- bind once to `OnLaneHitJudged`;
- map lane -> instrument frequency/pattern channel;
- map grade -> amplitude/coherence;
- map timing error -> phase offset;
- set material instance parameters;
- write `NDC_MelodiaRhythmPulse` for surrounding Niagara;
- drive optional cosmetic ring/chime animation;
- decay to idle state.

Suggested prop material parameters:

```text
CymaticAmplitude
CymaticPhase
CymaticPatternIndex
CymaticNodeSharpness
CymaticEmission
ResonanceAge
```

## 9.3 Shared pattern identity

For v1, do not attempt to reconstruct the full Houdini authoring mesh at runtime.

Instead export a lightweight runtime representation of the accepted pattern:

```text
pattern id
mask texture or compact analytic preset
frequency ratios
phase family
symmetry
```

This is enough for the physical engraving, emissive material and Niagara particles to visibly agree.

## 9.4 Instrument -> world bridge

The instrument can become a local source for the existing Cymatic Ecology system:

```text
player hits note
 -> instrument resonator lights / rings react
 -> same pulse enters NDC_MelodiaRhythmPulse
 -> local dust/water/filigree field reacts
 -> ecological memory may briefly persist
```

This should read as **the instrument revealing the same hidden field that already exists in the world**, not spawning a disconnected VFX package.

---

# 10. PC execution sequence

## Session 0 — repository/source hygiene — 30–60 min

- [ ] Create implementation branch separate from the docs-only research PR.
- [ ] Create `ArtSource/MaraElletra/` and `Tools/Houdini/mara_elletra/`.
- [ ] Copy/relocate canonical source meshes out of Downloads/Desktop.
- [ ] Generate SHA256 manifest entries.
- [ ] Record Houdini, Blender and UE exact versions.
- [ ] Pin one character body/rig revision for the canary.

**Stop if:** source authority is ambiguous.

## Session 1 — Resonance Astrolabe/Sonic Scepter blockout — 60–90 min

- [ ] Draw/import centerline + silhouette curves from the concept sheet.
- [ ] Build frame with Sweep.
- [ ] Add 3–5 ring stack.
- [ ] Add resonator disc.
- [ ] Add grip/socket position.
- [ ] Export rough FBX.
- [ ] Put in Mara/Elletra hand in UE.
- [ ] Capture gameplay-distance silhouette.

**Pass:** recognizable, balanced and readable without ornament.

## Session 2 — first cymatic resonator — 60–90 min

- [ ] Create `cymatic_pattern_presets.v1.json` with one pattern.
- [ ] Sample field in Houdini.
- [ ] generate node mask;
- [ ] convert nodes to curves;
- [ ] engrave or inlay resonator;
- [ ] export 2D mask from the same field;
- [ ] import mask into UE material canary.

**Pass:** Houdini geometry and UE emissive visibly match the same pattern.

## Session 3 — hero instrument detail compiler — 90–150 min

- [ ] Add ring pivots, rails, string/chime attachment points.
- [ ] Build ornament grammar.
- [ ] Generate high and game variants.
- [ ] pack material IDs;
- [ ] validate scale/pivot/orientation;
- [ ] export Unreal asset.

**Pass:** under target triangle/material budget and easy to regenerate after parameter changes.

## Session 4 — runtime instrument reaction — 60–90 min

- [ ] Build `BP_MelodiaCymaticHeroInstrument`.
- [ ] bind to `OnLaneHitJudged` once;
- [ ] drive MID amplitude/phase;
- [ ] write the existing rhythm pulse Data Channel;
- [ ] test Perfect / Great / Good / Miss;
- [ ] verify exactly one visual response per judged press;
- [ ] capture fixed-camera sequence.

**Pass:** instrument response is immediate and presentation-only.

## Session 5 — Shorewake v2 garment canary — 90–180 min

- [ ] replace hardcoded paths;
- [ ] add source hashes;
- [ ] fix numeric panel ordering;
- [ ] drive all transforms from true panel IDs/ranges;
- [ ] rerun current magic detail pass;
- [ ] generate before/after manifests;
- [ ] decide KineFX vs Blender-final skin path.

**Pass:** deterministic regenerate/reopen with no panel misalignment.

## Session 6 — cymatic garment overlay — 60–120 min

- [ ] project resonator node curves onto selected garment panels;
- [ ] create embroidery/inlay geometry only in hero zones;
- [ ] export packed mask for microdetail elsewhere;
- [ ] create one `Harmonize` deformation state;
- [ ] bind a material/morph response to the same runtime pulse.

**Pass:** garment and instrument feel designed from the same physical language.

## Session 7 — Mara Surveyor Mantle — 2–4 h blockout + drape

- [ ] author/prepare panel patterns;
- [ ] assign semantic panel regions;
- [ ] Vellum drape against proxy body;
- [ ] tune sleeves/mantle silhouette;
- [ ] add structured collar and shell trim as separate rigid pieces;
- [ ] cache approved state;
- [ ] export to rig pipeline.

**Pass:** garment silhouette works in engine before procedural surface detail.

## Session 8 — instrument family expansion

Only after the core compiler works:

1. Ripple Lyre;
2. Phase Bell;
3. Choral Cage / Monolith Tuner;
4. Tidal Disc / Veil Drum;
5. Melusina Pearl Harp;
6. Current Flute / Coral Conch;
7. remaining experimental forms.

Each new variant should be mostly parameter/guide-curve work.

---

# 11. Proposed batch commands

Exact local executable paths vary, but preserve this shape:

```powershell
# Houdini authoring build
hython Tools/Houdini/mara_elletra/instrument/build_instrument_family.py --variant resonance_astrolabe --config Tools/Houdini/mara_elletra/config/mara_elletra_asset_manifest.v1.json

# Cymatic authoring pattern
hython Tools/Houdini/mara_elletra/cymatics/build_cymatic_resonator.py --preset MEL_CYM_001 --variant resonance_astrolabe

# Garment detail build
hython Tools/Houdini/mara_elletra/garment/build_garment_details.py --garment shorewake_v2 --pattern MEL_CYM_001

# Contract validation
python Tools/Houdini/mara_elletra/qa/validate_asset_contract.py
```

Do not finalize commands until local Houdini/Blender executable locations and licenses are recorded in the manifest.

---

# 12. Runtime budgets / quality gates

These are project R&D targets, not universal engine limits.

## Hero instrument

Track:

```text
triangles high/game
material slots
transparent surfaces
skeletal/moving part count
shader complexity
draw calls
texture memory
Nanite eligibility if used
LOD generation/regeneration time
```

A new procedural detail only survives if it is visible in the intended camera or materially improves the silhouette/read.

## Garment

Track:

```text
base garment verts
hero detail verts
plate/ruffle instance count
skin influence count
material slots
morph target count
cloth/runtime simulation use
GPU skin cost
shader complexity
```

The current ~268k-vertex magical dress is a useful quality reference but should **not** silently become the default budget.

## Cymatics

Track:

```text
judged event -> visible response latency
material update cost
Niagara GPU ms
particle count
mask texture cost
temporal stability under TSR/DLAA/DLSS
Perfect vs Miss readability
```

---

# 13. Evidence bundle

For every hero asset spike:

```text
Docs/Research/Evidence/HeroAssets/<asset-id>/
  README.md
  manifest.json
  source_hashes.json
  houdini_params.json
  cymatic_pattern.json
  silhouette_before.png
  silhouette_after.png
  wireframe.md
  ue_import_notes.md
  perf_summary.csv
  regeneration_notes.md
  decision.md
```

Large HIP/FBX/cache files stay in the appropriate source-control/LFS/Perforce lane, not ordinary Git text history unless explicitly approved.

---

# 14. ADOPT / PARK / REJECT gates

## ADOPT the modular instrument compiler if

- at least three concept variants reuse the same HDAs;
- silhouette revision is fast;
- regenerate/export is deterministic;
- physical cymatic detail matches the runtime pattern language;
- UE import does not require manual repair each time;
- hero detail can be simplified without destroying identity.

## PARK if

- every concept needs a unique hand-built network;
- Boolean/VDB cleanup dominates iteration;
- generated ornament looks generic;
- cymatic engraving is invisible in actual game framing.

## REJECT a technique if

- it requires runtime Houdini;
- it changes rhythm authority;
- it explodes draw calls/material slots;
- it produces untraceable source drift;
- garment regeneration loses panel/rig correspondence;
- hero microgeometry costs more than a mask/normal solution with no visible gain.

---

# 15. Exact first build recommendation

When sitting down at the PC, build **only this vertical slice first**:

```text
Mara/Elletra Resonance Astrolabe
  + 1 procedural ring stack
  + 1 cymatic resonator disc
  + 1 pearl/glass material
  + 1 emissive cymatic mask
  + BP_MelodiaCymaticHeroInstrument
  + OnLaneHitJudged response
  + NDC_MelodiaRhythmPulse world echo
```

Then add one garment connection:

```text
Shorewake v2 or Surveyor Mantle panel
  + projected MEL_CYM_001 embroidery
  + Harmonize material/morph response
```

If that works, the project has proven the full thesis:

> **Houdini does not merely generate ornate props. It compiles a visual/acoustic design language that survives into gameplay presentation.**

At that point, expanding the instrument family and garment variants is production work rather than speculative R&D.
