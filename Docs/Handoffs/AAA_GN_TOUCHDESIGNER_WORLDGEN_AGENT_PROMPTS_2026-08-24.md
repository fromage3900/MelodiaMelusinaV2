# AAA Geometry Nodes, TouchDesigner, and Worldgen Agent Prompts

These are three independent copy-paste lanes. Infinity Nikki is a quality lens for readable silhouettes, luminous softness, strong landmarks, outfit/world readability, and welcoming traversal—not a source of copied assets, layouts, motifs, palettes, names, or trade dress.

Official grounding: Blender recommends instancing to avoid duplicated geometry and warns that realizing instances costs memory; Repeat Zones are for bounded iteration and Simulation Zones for frame-to-frame state. TouchDesigner officially supports MIDI/OSC through CHOP/DAT operators and recommends reducing SOP and render batches for performance.

---

## Prompt 1 — Blender 5.2 Geometry Nodes fantasy-architecture lane

BEGIN COPY-PASTE PROMPT

You are the isolated Blender 5.2 Geometry Nodes architecture owner for C:\EnvironmentPortfolio\BS_GodFile.

MISSION

Build one original, production-oriented Geometry Nodes architecture grammar for soft, readable AAA fantasy environments. Use Infinity Nikki only as an abstract quality lens: clear silhouettes, welcoming scale, layered softness, restrained ornament, graceful verticality, strong landmarks, readable routes, and coherent material regions. Do not copy buildings, layouts, motifs, textures, logos, names, or assets. Do not create another monolithic generator or a renamed clone of an existing MEL_* group.

READ FIRST

- AGENTS.md and _AGENT_WORKING_AGREEMENT.md
- deploy/surreal_arch/README.md
- deploy/surreal_arch/Docs/GN_EXPANSION_PLAN_2026-08-17.md
- deploy/surreal_arch/melodia_gn/core.py, aaa_quality.py, structures.py, castle.py, ornament.py, filigree.py, set_dressing.py, nikki_quarter.py, profiles.py, presets.py
- deploy/surreal_greybox/shells.py, facades.py, towers.py
- Tools/BlenderAddons/blender_kawaii_gn and blender_brutalist_gn as read-only references
- Docs/WorldGen/MESH_TERRAIN_GAEA_DEM_P0.md
- PetalCantata_3900 world.json, pcg_plan.json, score.json, and current_midi_environment.manifest.json

PREFLIGHT

Record HEAD, scoped Git status, and hashes of every target file. Inventory GROUP_BUILDERS and prove all proposed identifiers are unused. Treat dirty files as owner-authored. If a target exists or changes during work, stop with PATH_COLLISION_HOLD. If HEAD or a hashed input moves once, refresh and rerun; twice means MOVING_BASELINE_HOLD.

EXCLUSIVE WRITES

- deploy/surreal_arch/melodia_gn/fantasy_architecture.py
- deploy/_gn_fantasy_architecture_smoke.py
- deploy/surreal_arch/Docs/FANTASY_ARCHITECTURE_GN_CONTRACT_2026-08-24.md
- Saved/Audit/gn_fantasy_architecture_20260824/**
- One minimal import-only edit to deploy/surreal_arch/melodia_gn/__init__.py after its hash remains stable

Implement exactly five public builders. Reuse existing primitives/helpers; do not add a sixth group.

1. MEL_fantasy_building_shell

Purpose: metric massing from an input footprint or default rectangle; softened shell, floors, bays, openings, roof outline, facade/socket points, and cheap collision proxy.

Inputs: Geometry, Use Default Footprint, Width, Depth, Floors, Floor Height, Wall Thickness, Corner Softness, Door Bay, Door Width, Door Height, Window Bay Count, Window Width, Window Height, Window Sill, Symmetry, Variation, Seed, LOD, Realize for Export.

Outputs: Geometry, Collision Proxy, Facade Points, Roof Outline, Socket Points.

Use fields, Mesh Line, curves, and instances. Do not use a zone where ordinary fields solve the problem.

2. MEL_fantasy_facade_rhythm

Purpose: turn facade points/curves into deterministic doors, windows, bays, cornices, balconies, arches, material regions, and sockets. Reuse MEL_arch, column, baluster, ornament, and filigree vocabulary.

Inputs: Facade Points, Building Width, Floor Height, Bay Count, Door Bay, Window Collection, Balcony Collection, Arch Amount, Balcony Amount, Cornice Amount, Ornament Density, Softness, Variation, Seed, LOD, Realize for Export.

Outputs: Geometry, Hero Detail, Material Regions, Socket Points.

Bay/floor indices drive stable selection. Curvature/normal fields may affect trim depth. Reducing ornament density must not reshuffle unrelated windows.

3. MEL_fantasy_roof_canopy

Purpose: gable, hipped, pavilion, and soft-canopy silhouettes with eaves and at most four tiers.

Inputs: Roof Outline, Roof Mode, Pitch, Eave Overhang, Tier Count, Tier Scale, Tier Rise, Ridge Softness, Tile Collection, Ornament Collection, Variation, Seed, LOD, Realize for Export.

Outputs: Geometry, Collision Proxy, Ridge Curves, Ornament Points.

Use one Repeat Zone only to accumulate tier outline/scale/height. Tiles use points/curves/instances. LOD1 removes individual ornaments; LOD2 emits roof mass only.

4. MEL_fantasy_district

Purpose: compose shell/facade/roof variants over parcel points or a guide curve while preserving routes and one dominant landmark per cell.

Inputs: Parcel Points, Guide Curve, Building Collection, Landmark Collection, Parcel Spacing, Route Clearance, Slope Limit, Density, Landmark Index, Height Range, Variation, Seed, LOD, Realize for Export.

Outputs: Geometry, Collision Proxies, Landmark Geometry, Route Exclusion, PCG Socket Points.

Distance to Guide Curve controls exclusion and density falloff. Stable semantic point IDs drive variation. Keep instances unrealized until export. Accept evaluated terrain positions; do not invent a placeholder terrain plane.

5. MEL_fantasy_bloom_preview

Purpose: Blender-only presentation preview for vines, petals, banners, or emissive accents awakening over time. It is not gameplay or world state.

Inputs: Geometry, Accent Points, Enabled, Reset, Growth Rate, Growth Duration, Beat Pulse, Seed, Final Static State.

Outputs: Geometry, Growth Mask.

Use one Simulation Zone carrying only required age/growth state. Final Static State must bypass temporal state and deterministically evaluate at 1.0. Export proof must show the static path has no simulation dependency.

NAMED ATTRIBUTES

- mel_piece_id: INT stable piece ID
- mel_material_slot: INT material region
- mel_lod_class: INT 0 hero, 1 mid, 2 silhouette
- mel_collision_class: INT 0 none, 1 walkable, 2 blocking
- mel_walkable: BOOLEAN
- mel_route_clearance: FLOAT metres
- mel_softness_mask: FLOAT 0–1
- mel_ornament_mask: FLOAT 0–1
- mel_seed_channel: INT

DETERMINISM

Default seed 3900. Never use time, scene frame, object name, Python random, unordered iteration, or global RNG. Derive independent channels from base seed + stable piece ID + constants: massing 11, facade 23, roof 37, ornament 53, growth 71, district 89. Two factory-startup runs must match topology, bounds, interface schema, attributes, and geometry fingerprints. A second seed may alter variants but not route clearance, collision, schema, or budgets.

QUALITY AND PERFORMANCE

- Large/medium/small detail distribution approximately 70/20/10.
- At least 1.2 m clear walkable width; hero routes target 2.0 m.
- Ornament visible-area ceiling: 15% LOD0, 5% LOD1, 0% LOD2.
- Per building: LOD0 <=100k triangles; LOD1 <=35k; LOD2 <=8k; collision <=5k.
- Per district: <=1.2M realized triangles, <=5k unrealized instances, <=12 named attributes, <=250 MB evaluated geometry target.
- No NaN/Inf, zero-area faces, negative export scale, or increasing triangle counts across LODs.
- Preserve silhouette and route readability before secondary detail.

VERIFY

- Probe exact Blender 5.2 node idnames and zone APIs before implementation; unavailable required nodes are HOLD, never silent fallback.
- Python syntax and static interface tests.
- Blender 5.2 --background --factory-startup smoke run building all five groups.
- Evaluate LOD0/1/2, seed 3900 and one alternate seed, route clearance, collision separation, static bloom path, naming audit, and budgets.
- Run the identical factory-startup test twice into separate directories and compare deterministic fingerprints byte-for-byte.
- Produce node_availability.json, catalog_before_after.json, interface_contract.json, two geometry metrics files, determinism_diff.json, lod_budget.json, collision_report.json, an isolated preview_factory.blend, and a labeled contact sheet.

FORBIDDEN

No Content, Source, Plugins, Config, specs, Tools/BlenderAddons, PetalCantata, existing generator edits, UE, Monolith, MCP, AppData sync, portfolio .blend resave, network/downloads, proprietary references, clone suffixes, silent node fallbacks, Python-built final meshes, staging, commits, pushes, or destructive Git.

Handoff exact files, commands/results, builder-count delta, node probe, budgets, deterministic hashes, image/contact-sheet paths, holds, and confirmation that UE and Git history were untouched. Do the work, verify it, stop.

END COPY-PASTE PROMPT

---

## Prompt 2 — TouchDesigner music-key sanctuary lane

BEGIN COPY-PASTE PROMPT

You are the TouchDesigner look-development owner for one bounded Melodia lane in C:\EnvironmentPortfolio\BS_GodFile.

MISSION

Create one original AAA-fantasy audiovisual sanctuary where an authored musical phrase visibly awakens an architectural passage. Use Infinity Nikki only as a mood/readability lens: luminous optimism, graceful silhouettes, restrained magical detail, strong landmarks, and clear interactable emphasis. Do not copy assets, compositions, motifs, palettes, shaders, logos, UI, or names. This is presentation/lookdev only and owns no gameplay, narrative, progression, save, traversal, or combat state.

READ FIRST

- AGENTS.md and _AGENT_WORKING_AGREEMENT.md
- _TouchDesigner/README.md
- _TouchDesigner/grandmaster_melodia/networks/audio.tdn, osc.tdn, postfx.tdn
- _TouchDesigner/grandmaster_melodia/scripts/wire_render_pipeline.py and wire_battle_fixed.py
- deploy/osc_routing.json and Content/Python/osc_server.py
- Docs/HARMONIX_MIDI_RHYTHM_CONTRACT_2026-07-29.md
- Docs/T3D_Baseline/materials/MPC_Melodia_Palette.t3d

Preserve current facts: TD listens on 9000; only one OSC In CHOP may own it; TD-to-UE destination is 8000; existing analysis uses five bands around 80/250/1000/4000/8000 Hz, RMS, asymmetric lag, pitch/chord features; authored MIDI is presentation timing only.

EXCLUSIVE WRITES

- _TouchDesigner/lookdev/melodia_music_key_sanctuary/**
- _TouchDesigner/components/melodia_music_key_sanctuary/**
- _TouchDesigner/networks/melodia_music_key_sanctuary/**
- _TouchDesigner/exports/melodia_music_key_sanctuary/**
- Saved/Audit/touchdesigner_music_key_sanctuary/**
- Docs/Handoffs/TOUCHDESIGNER_MUSIC_KEY_SANCTUARY_HANDOFF_2026-08-24.md

Build exactly this root network:

/project1/melodia_music_key_sanctuary
- /control
- /source_replay
- /audio_analysis
- /midi_motif
- /architecture
- /palette_materials
- /particles
- /postfx
- /render
- /ui_debug
- /record
- /audit

Expose only TakeSeed, TakeFrame, ReplayMode, MotifIndex, PaletteIndex, AudioInfluence, MotifProgress, GateResolved, WorkingResolution, CaptureResolution, DebugView, RecordArm. Every child COMP publishes named inputs/outputs and one OUT_* operator; no expressions reaching into arbitrary internals.

NETWORK CONTRACT

1. control: Table DAT + Constant CHOP for seed, palette, motif, quality, frame, A/B switches, and one reset pulse. No hidden UI state.

2. source_replay: deterministic frame-indexed DAT/CSV -> DAT to CHOP -> Trim/Lookup -> Null. Publish beat_phase, beat_pulse, measure, bpm, sub, low, mid, high, air, pitch_note, chord_root, chord_quality, and motif events. Switch between replay and disabled live input. Open no sockets.

3. audio_analysis: Audio File In -> five Audio Filter CHOPs -> RMS Analyze -> asymmetric Lag -> Rename -> Merge -> OUT_AUDIO_FEATURES. Clamp outputs; silence is stable zero/default, never NaN.

4. midi_motif: read Content/MelodiaIntegration/MIDI/128BPMarpeggiomelody_beatgrid.mid. Select one real complete bar/phrase and record exact track, tick range, bar, BPM, notes/pitch classes, and tolerance in motifs.json. MIDI/replay -> Select/Rename -> Logic note edges -> Count/Pattern -> comparison DAT -> progress/complete -> OUT_MOTIF_STATE. Velocity-zero note-on is note-off. Publish motif_index, motif_progress, correct_streak, motif_error, one-frame complete pulse, phrase_tension, and stable resolved state.

5. architecture: original SOP geometry only. Include one sanctuary silhouette, central readable path, closed passage, petal/lyre-inspired original portal, foreground frame, midground landmark, background crown, and negative space around the gate. Suggested SOP chain: Curve/Line/Grid -> Resample -> Transform/Copy to Points -> Sweep ribs/arches -> procedural tracery -> Merge -> Normal -> Null. Use instancing. Step 1 wakes path inlay; step 2 side ribs; step 3 crown/rose; completion unfurls portal once and holds open. Provide clay view.

6. palette_materials: semantic roles SkyBackground, ArchitectureBody, CoolShadow, PathGuide, MusicKeyGlow, InteractableAccent, CompletionGold, ErrorMuted. Author 3–4 original palettes with linear and sRGB JSON. BeatPulse is restrained emissive breathing; band values affect separate scales; PaletteShift is quantized; motif progress owns path/gate readability.

7. particles: only ambient petal motes, note-path guides, and one completion burst. Audio controls secondary motion; motif owns sequence.

8. postfx: threshold -> three-scale bloom -> composite -> optional restrained DOF -> subtle chroma/grain -> vignette -> palette grade. Drive capture from TakeFrame/FPS, never absTime or wall clock. Bypasses for bloom, DOF, particles, grain, grade; clay bypasses all beauty effects.

9. render: camera/light/geometry -> Render TOP -> postfx/particles -> Switch TOP for beauty, clay, wireframe, audio-debug, motif-debug -> Out TOP. One hero camera and optional diagnostic camera.

10. record: deterministic PNG/EXR sequence at 60 FPS, 1920x1080, 120-frame preroll, 720 captured frames, diagnostic frames 0/120/240/480/719, beauty/clay/motif/audio outputs, and a second identical take for hash comparison.

OSC/MIDI

Do not edit canonical routing. Export osc_schema_delta.json. Recognize existing rhythm/audio routes, but keep all OSC operators inactive. Propose only namespaced lookdev routes: /td/lookdev/motif/index, /progress, /complete, /palette/index, /take/frame, /take/seed with type/range/cadence/owner/default. Never transmit them during this task.

DETERMINISM AND BUDGETS

Use 60 FPS, integer root seed, explicit reset, frame-indexed replay, and no absTime, current time, unseeded Noise, live devices, network, ambiguous feedback, or startup-order dependence. Hash the .toe, TDN/TOX, MIDI, replay, palettes, motifs, manifests, and diagnostic frames. Identical takes must have identical event and fixed-frame image hashes.

Interactive: 1280x720 at 60 FPS, <=16.67 ms frame, <=12 ms GPU target, <=4 ms aggregate CPU cook, no drops. Final: 1080p/60 for 720 frames, <=100k visible particles/instances, <=250k SOP points, <=150 draw calls, <=3 bloom scales, <=2 full-resolution GLSL beauty passes, <=1.5 GB TOP memory, zero red operators/NaNs/errors. Reduce particles, then DOF, bloom resolution, and secondary geometry if needed—never sacrifice route/gate readability first.

DELIVER AND VERIFY

New isolated .toe, reusable root .tox and clean child .tox files, TDN exports, README network map, palettes.json, motifs.json, osc_schema_delta.json, replay data, all captures, two take manifests/hash comparison, performance samples, validation_report.json, and handoff doc. Reopen from disk, pulse reset, run twice, compare hashes, prove closed/open states, prove audio-off preserves readability, validate schemas without sockets, record performance, and confirm no forbidden path changed.

FORBIDDEN

No UE/Blender execution, MCP, canonical OSC/MIDI edits, shared active .toe resave, live sockets, NDI/Spout, network/downloads/packages, multiple unrelated experiments, commits/staging/destructive Git, or copied game material. If the phrase lacks traceable MIDI provenance or deterministic takes differ without an isolated cause, HOLD.

Return status, exact files, component paths, three-sentence visual thesis, palette/motif provenance, take hashes, performance table, schema result, verification, limits, and confirmation that UE, Blender, network, canonical assets, and Git history were untouched.

END COPY-PASTE PROMPT

---

## Prompt 3 — Offline deterministic fantasy worldgen and architectural-research lane

BEGIN COPY-PASTE PROMPT

You are the OFFLINE MELODIA ARCHITECTURE + DETERMINISTIC WORLDGEN owner in C:\EnvironmentPortfolio\BS_GodFile.

MISSION

Produce an original AAA-oriented fantasy architectural research packet and deterministic world-generation prototype. Use Infinity Nikki only as a lens for navigable silhouettes, landmark readability, graceful verticality, path telegraphing, material separation, and long/medium/near hierarchy. Do not copy layouts, assets, motifs, terminology, or trade dress. Grow the result from Melodia’s music-as-key identity, PetalCantata data, checked-in architectural kits, and gameplay routes.

This lane is offline: schemas, standard-library Python, deterministic JSON, tests, evidence, and research documents only. It does not execute Blender or integrate UE.

READ FIRST

- AGENTS.md, _AGENT_WORKING_AGREEMENT.md, Orchestra contract/convergence
- Content/Python/resonant_world_generator.py, score.py, phrase_bridge.py, pcg_adapter.py, asset_atlas.py, asset_constellation.py, chronicle.py, magic_passage.py, proof_handoff.py and their tests
- specs/resonant_world*, resonant_phrase*, score, pcg_plan, constellation, magic_passage, proof_handoff
- PetalCantata_3900 world.json, phrase.json, score.json, pcg_plan.json, bundle.json, current_midi_environment.manifest.json, proof_handoff.json, ue_import_plan.json
- Docs/WorldGen/MESH_TERRAIN_GAEA_DEM_P0.md and MIDI contract
- deploy/surreal_arch README, GN plan, melodia_gn_route.py, core, structures, castle, recursive_castle, sky_observatory, music modules, nikki_quarter, pcg_integration, set_dressing, profiles/presets, and architectural kits

Treat .blend/.fbx/.obj/.uasset as opaque references.

EXCLUSIVE WRITES

- Tools/resonant_architecture_lab/**
- specs/worldgen_architecture/**
- Docs/WorldGen/AAA_MELODIA_ARCHITECTURE_RESEARCH_2026-08-24.md
- Docs/WorldGen/MELODIA_NAVIGABLE_ARCHITECTURE_GRAMMAR_2026-08-24.md
- Saved/WorldGen/ArchitectureLab/**

PREFLIGHT

Record HEAD/status, hash every material read-only input, and stop on path collision. One changed baseline triggers one full refresh/rerun; a second triggers MOVING_BASELINE_HOLD. Never clean, reset, checkout, stash, stage, commit, or touch unrelated dirt.

RESEARCH CORPUS

Create research_corpus.v1.json containing normalized source path, SHA-256, role, extracted rule, confidence (canonical/implemented/proposed/unknown), affected seam, contradictions, and exact line evidence. Minimum 12 concrete rules across eight sources. Separate repo facts from design synthesis. Add an originality ledger stating retained abstract principles and forbidden derivative expression.

ARCHITECTURAL GRAMMAR

Create architecture_grammar.v1.json and a readable companion document covering:

- Hierarchy: world -> district -> neighborhood/room sequence -> landmark -> route -> encounter/reward pocket.
- Landmark roles: primary, secondary, local; ingress, climax, return, optional-loop, vista anchor.
- Silhouette: primary mass, secondary masses, crown/accent, near trim; long/medium/near readability; skyline separation; landmark reacquisition; foreground framing; compression/release; district identity not dependent on color.
- Language: bay rhythm, openings/arches, roof/crown families, support logic, base/body/crown ratios, ornament density by distance/traversal importance, original musical structural motifs, material/value grouping, permissible kit hybrids, and forbidden illegible combinations.
- Topology: guaranteed start-to-goal route, authored main route, optional loop, explicit reward dead ends, readable junctions, return logic, encounter pockets, route widths/clearance/slopes/stairs/landings/turning/vista cadence. Unknown player metrics are PROPOSED_NEEDS_RUNTIME_VALIDATION.
- Music-as-key: stable phrase/MIDI IDs map tempo bands, sections, pitch classes, accents, and cadences to authored variant selection, density, landmark accent, and route dressing. Music never makes collision-critical topology nondeterministic.

GENERATOR

Implement a pure standard-library package under Tools/resonant_architecture_lab. No Unreal, bpy, Monolith, NumPy, pytest, network, or third-party imports. Use explicit integer seed, SHA-256 named sub-seeds, stable IDs, sorted iteration/JSON, UTF-8 + final newline, bounded rounded floats, and no timestamps/absolute paths/machine names/random UUIDs. Same corpus+seed is byte-identical; another seed changes optional layout/dressing while all hard route gates remain.

Generate seed 3900 outputs:

- Saved/WorldGen/ArchitectureLab/PetalCantata_3900/world_architecture.json
- gn_handoff.json
- route_gate_report.json
- determinism_proof.json

VALIDATION GATES

Fail closed on duplicate/unstable IDs, disconnected districts, missing start/goal/primary landmark, no start-to-goal route, unreachable required landmark, unjustified dead ends, district lacking loop/terminal role, insufficient route clearance, excessive untreated slope, overlapping traversal envelopes, landmark hierarchy collisions, missing ingress/reacquisition samples, undeclared GN sockets/modules, unsorted output, unknown phrase/MIDI references, and exceeded budgets. Visibility is STATIC_APPROXIMATION, never camera/NavMesh/runtime proof.

GN HANDOFF SCHEMA

Create gn_handoff.schema.v1.json with schema/generator versions, input hashes, seed/sub-seeds, units/axes/space, districts, landmarks, routes, splines, sockets, modules, instances, stable relationships, transforms, symbolic kit IDs, typed GN parameters with ranges/units, material and ornament tags, traversal/no-build envelopes, LOD/culling/collision intent, instancing group, phrase provenance, required/optional downstream capabilities, findings, and unresolved assumptions. Unproven modules are capability_status: proposed.

LOD/PERFORMANCE CONTRACT

Define LOD0–LOD3 purposes/distance bands, module triangle ceilings, unique material/slot ceilings, maximum generators/realized meshes/spline points/instances, instancing policy, collision proxies, ornament falloff, and district/world aggregates. These are static constraints, not measured Blender/UE performance.

TEST

Use unittest for corpus/hash reconciliation, schemas, sub-seeds/IDs, two-process byte equality, alternate-seed variation, graph connectivity/reachability/loops/dead ends, width/clearance/slope/envelopes, landmark/vista gates, phrase references, GN handoff ordering/completeness, budgets, and malformed-input fail-closed behavior.

Run:

- python -B -m unittest discover -s Tools/resonant_architecture_lab/tests -p test_*.py -v
- python -B -m Tools.resonant_architecture_lab.generate --seed 3900 --output-root Saved/WorldGen/ArchitectureLab/PetalCantata_3900
- python -B -m Tools.resonant_architecture_lab.verify --seed 3900 --output-root Saved/WorldGen/ArchitectureLab/PetalCantata_3900

PROOF TIERS

T0 research/originality; T1 schemas/tests; T2 deterministic JSON/route proof; T3 Blender/GN materialization HOLD_DOWNSTREAM; T4 UE/NavMesh/runtime HOLD_DOWNSTREAM; T5 packaged/art-direction acceptance HOLD_DOWNSTREAM. Never promote static evidence.

FORBIDDEN

No UE, Monolith, PIE, builds, packaging, Blender/bpy/.blend save/export/render, network/downloads, Content/deploy/Source/Plugins edits, canonical ResonantWorld/PetalCantata/MIDI/Echo/website edits, new gameplay authority, fabricated citations/performance/geometry claims, commits/staging/destructive Git.

HANDOFF

Return status, starting/ending HEAD, files, input hashes, seed/output hashes, district/landmark/route counts, gates, exact tests/results, deterministic comparison, T0–T5 table, runtime assumptions, downstream routes, scoped status, and confirmation that UE, Blender, network, dependencies, staging, and commits were untouched. Route the handoff to the existing GN owner and ResonantWorld/PCG owner; do not integrate it yourself.

END COPY-PASTE PROMPT
