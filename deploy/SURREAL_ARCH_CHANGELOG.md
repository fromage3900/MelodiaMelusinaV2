# Surreal Architecture — Changelog

## v2.131.0 — Art Deco lobby architecture set

- **`art_deco_lobby_v1`** genome + **`ART_DECO`** grammar chain (6 modules)
- **`ART_DECO`** compose style + library bake for **`TESSELLATION_TOWER`**
- Research preset `art_deco_lobby_graph` + curated playable preset; `vertical_stretch` transform
- World manifest embed verify; genome catalog **30**

## v2.130.0 — Asian city recursive compose polish

- **`ASIAN_CITY_RECURSIVE`** grammar — offset alley lanes, kura bays, bend, moon gate terminus
- **`ASIAN_CITY_RECURSIVE`** compose style — kura medium / pavilion small role inversion vs street grid
- **`asian_city_recursive_v1`** retargeted to dedicated grammar + compose; manifest embed verify

## v2.129.0 — Brutalist + Western compose retarget

- **`BRUTALIST_PLAZA`** compose style + library bake for **`GB_BRUTALIST_PANEL_WALL`**
- **`brutalist_plaza_v1`** retargeted to native `BRUTALIST_PLAZA` compose (was WESTERN_CASTLE bleed)
- **`western_castle_v1`** — `recursive_interior` + CLOISTER gate/corridor compose role overrides
- World manifest embed verify for brutalist plaza + western castle compose exports

## v2.128.0 — Romanesque compose polish

- **`ROMANESQUE_CLOISTER`** + **`ROMANESQUE_APSE`** compose styles in `compose_roles.json`
- Library bake for **`GB_ROMANESQUE_APSE`**; arcade-medium + apse-sacred role maps
- **`romanesque_cloister_v1`** + **`romanesque_apse_v1`** compose_style fixed (was WESTERN_CASTLE bleed)
- World manifest embed verify for Romanesque cloister + apse compose exports

## v2.127.0 — Gothic nave crossing variant

- **`gothic_nave_crossing_v1`** genome + **`GOTHIC_NAVE_CROSSING`** grammar (T-crossing junction, transept arm, rose clerestory, aisle bay)
- **`GOTHIC_NAVE_CROSSING`** compose style — rose window monument role; `vertical_stretch` transform
- Research preset + curated playable preset; world manifest embed verify; catalog **29**

## v2.126.0 — Gothic chapter house variant

- **`gothic_chapter_house_v1`** genome + **`GOTHIC_CHAPTER_HOUSE`** grammar (7 modules: portal nave, window bay, buttress, transept, tracery)
- **`GOTHIC_CHAPTER_HOUSE`** compose style + research preset + curated playable preset
- World manifest embed verify; genome catalog **28** entries

## v2.125.0 — Baroque church monolithic set

- **`baroque_church_v1`** genome + **`BAROQUE_CHURCH`** grammar (ornate facade, ogee portal, ribbed vault, niche chapel, balustrade choir, crossing dome)
- **`BAROQUE_CHURCH`** compose style + library bake for baroque niche
- Research preset `baroque_church_graph` + curated playable preset; `recursive_interior` transform
- Genome catalog **27** entries

## v2.124.0 — Byzantine basilica monolithic set

- **`byzantine_basilica_v1`** genome + **`BYZANTINE_BASILICA`** grammar (horseshoe narthex, cusped arch, vault nave, rose clerestory, crossing dome)
- **`BYZANTINE_BASILICA`** compose style + library bake for cusped arch, rose window, baroque vault
- Research preset `byzantine_basilica_graph` + curated playable preset; `vertical_stretch` transform
- Genome catalog **26** entries

## v2.123.0 — Sci-Fi compose family complete

- **`scifi_airlock_v1`** + **`scifi_industrial_yard_v1`** compose_style fixed to **`SCIFI_DECK`**
- Per-genome `compose_roles` overrides with library-prefixed greybox modules
- World manifest embed verify for airlock + industrial yard compose exports
- Sci-Fi catalog **4/4** genomes on dedicated compose style

## v2.122.0 — Sci-Fi deck compose style

- **`SCIFI_DECK`** compose style in `compose_roles.json` — greybox corridor spine, pressure-door gate, pillar-hall large, room sacred
- Library bake for `GREYBOX_ROOM`, `GREYBOX_CATWALK`, `GREYBOX_PILLAR_HALL`, `GB_SCIFI_PRESSURE_DOOR`
- **`scifi_deck_v1`** + **`scifi_deck_spine_v1`** compose_style fixed (was WESTERN_CASTLE bleed)
- World manifest embed verify for Sci-Fi deck compose export

## v2.121.0 — Sci-Fi industrial yard + endless tier-B loop

- **Endless loop:** `cursor_surreal_tierb_loop.ps1` tick prompt retargeted to AAA genome expansion; monitored 300s cadence
- **`scifi_industrial_yard_v1`** genome + **`SCI_FI_INDUSTRIAL_YARD`** grammar (pillar atrium, catwalk spine, bulkhead, service corridor)
- Research preset `scifi_industrial_yard_graph` + curated playable preset; `recursive_interior` transform coverage
- Genome catalog **25** entries

## v2.120.0 — Zen monolithic genome expansion

- **`zen_karesansui_v1`** genome wired to existing **`ZEN_KARESANSHUI_WALK`** grammar
- **`zen_stream_garden_v1`** + **`ZEN_STREAM_GARDEN`** — strolling water garden graph (8 modules)
- **`zen_pagoda_spire_v1`** + **`ZEN_PAGODA_SPIRE`** — vertical monument spine with `vertical_stretch`
- **`zen_kairo_enclosure_v1`** + **`ZEN_KAIRO_ENCLOSURE`** — cloister temple compound graph
- 4 research graph presets + 4 curated playable presets; Zen catalog **10** genomes

## v2.119.0 — Gothic cloister compose style

- **`gothic_cloister_v1`** compose_style fixed to **`GOTHIC_CLOISTER`** with dedicated compose roles + auto-stamp
- Library bake for greybox corridor + gothic portal; world manifest embed verify (`recursive_interior`)

## v2.118.0 — Venetian canal compose style

- **`venetian_canal_v1`** compose_style fixed to **`VENETIAN_CANAL`** with dedicated compose roles + auto-stamp
- Library bake for loggia, bifora, bridge; world manifest embed verify
- **Hotfix:** restored truncated `surreal_architecture_gen.py` tail from git HEAD

## v2.117.0 — Renaissance piazza architecture set

- **`renaissance_piazza_v1`** genome + **`RENAISSANCE_PIAZZA`** grammar chain (6 modules)
- **`RENAISSANCE_PIAZZA`** compose style — dome as sacred role, baroque facade as hero
- Curated **Renaissance Piazza** graph preset + world manifest embed verify

## v2.116.0 — Moorish courtyard architecture set

- **`moorish_courtyard_v1`** genome + **`MOORISH_COURTYARD`** grammar chain (6 modules)
- Moorish Courtyard preset retargeted to `moorish_courtyard_graph` (was Venetian canal clone)
- Compose style + world manifest embed verify for horseshoe-gate riyad typology

## v2.115.0 — Filigree generator + Art Nouveau set

- **`FILIGREE_PANEL`** / **`FILIGREE_RAIL_INSET`** — curve-swept ironwork with vine, gothic, and geometric modes
- **`art_nouveau_v1`** genome + **`ART_NOUVEAU`** grammar chain (ogee, filigree, balcony, facade)
- **`ART_NOUVEAU`** compose style + library bake entries; world manifest embed verify

## v2.114.0 — Western castle default genome

- **`western_castle_v1`** — baseline WESTERN_CASTLE compose + CLOISTER graph; auto-stamp on world compose
- World export verify tier for western_castle manifest embed

## v2.113.0 — Stale yaml genomes removed (tick 10 milestone)

- Deleted 8 duplicate `.yaml` genome files; `load_genome()` uses `.json` only
- 300s maintenance loop: 10 ticks, preset retarget wave complete (v2.105–v2.113)

## v2.112.0 — Grammar enum audit + genome prop sweep

- Fixed invalid `material_choice` / `gb_trim_mode` in genomes and zen research presets
- `audit_grammar_enums()` verify tier guards all OS grammar chains

## v2.111.0 — Sci-Fi Airlock curated graph preset

- Playable **`SCIFI_AIRLOCK`** preset spawns `SCIFI_AIRLOCK` graph chain
- OS verify tier for `scifi_airlock_graph` spawn

## v2.110.0 — Graph preset audit + civic retarget

- Hypostyle Hall, Baroque Piazza → OS graph spawns (**20** curated graph presets)
- `audit_graph_presets()` verify tier for all research presets with `graph_id`

## v2.109.0 — Civic/asian preset graph completion

- Basilica Nave, Japanese Gate, Town Hall, Guild Hall → OS graph spawns
- `zen_roji_path_graph` research preset; **18** curated graph presets total

## v2.108.0 — Third wave curated preset graph retarget

- Shinto Shrine, Sci-Fi Atrium, Tea Pavilion, Venetian Palazzo, Pailou, Market Colonnade → OS graphs
- 14 curated playable presets now spawn module chains

## v2.107.0 — Second wave curated preset graph retarget

- Chapel, Zen Courtyard, Moorish Courtyard, Brutalist Plaza, Covered Bazaar → OS graph spawns
- Research presets: `romanesque_apse_graph`, `venetian_canal_graph`

## v2.106.0 — Curated presets use graph spawns

- Gothic Cloister, Monastery Cloister, Temple Compound → `_make_graph_preset_op` + OS grammar chains
- Replaces tower-radius `MONASTERY` / single `CN_TIERED_PAGODA` masquerading as compounds

## v2.105.0 — Research presets spawn real graph chains

- Presets with `graph_id` now call `spawn_graph()` (full module chain) instead of single `generate()`
- Fixes misleading "Asian City / Cloister Graph / Shrine Axis" presets that only built one module

## v2.104.0 — Brutalist world manifest embed verify

- World export verify tier for `brutalist_plaza_v1` on WESTERN_CASTLE motte compose
- OS verify asserts `axis_compression` on `BRUTALIST_PLAZA` graph

## v2.103.0 — Asian recursive genome + world manifest embed

- **`asian_city_recursive_v1`** — `recursive_interior` on `ASIAN_CITY` graph chain
- `ASIAN_CITY` compose auto-stamps `asian_city_v1`; world export manifest verify tier
- Genome catalog: **16** entries

## v2.102.0 — BRUTALIST_PLAZA graph spawn verify

- OS verify spawns partial `BRUTALIST_PLAZA` graph chain (3 modules) — mirrors Asian city tier

## v2.101.0 — ASIAN_CITY graph spawn verify

- OS verify spawns partial `ASIAN_CITY` graph chain (3 modules) alongside zen axis tier
- Grammar enum fixes: `gb_trim_mode`/`material_choice` values aligned to Blender property enums

## v2.100.1 — Loop maintenance cadence (tick 28)

- Default Cursor wake interval **300s** (was 120s) — tier B/C backlog complete
- **`cursor_surreal_tierb_loop.ps1`** + start/stop scripts for `AGENT_LOOP_TICK_surreal_tierb`

## v2.100.0 — Dedicated Asian + Brutalist grammar graphs

- **`asian_city.json`** — pailou → lane → pavilion → kura → hanok → moon gate (6 modules)
- **`brutalist_plaza.json`** — pilotis hall → panel wall → offset corridor chain (5 modules)
- Genomes retargeted to native `ASIAN_CITY` / `BRUTALIST_PLAZA` grammar ids; **15** `os_grammar` graphs total
- Research presets: `asian_city_graph`, `brutalist_plaza_graph`

## v2.99.0 — Asian + Brutalist genome families

- **`asian_city_v1`** — `ASIAN_CITY` compose roles in OS `compose_roles.json`; canal-grid graph reuse
- **`brutalist_plaza_v1`** — low-ornament WESTERN_CASTLE + `axis_compression` on romanesque cloister spine
- Genome catalog: **15** entries; families Asian + Brutalist

## v2.98.0 — Genome `family` schema field

- All genome JSON files include explicit **`family`** (Zen, Gothic, Sci-Fi, Romanesque, Venetian)
- **`genome_family()`** resolves family for UI grouping and `.world.json` manifest embed

## v2.97.0 — Genome catalog groups + UE import notes

- Level Design UI groups genomes by family (Zen, Gothic, Sci-Fi, Romanesque, Venetian)
- `SURREAL_WORLD_RESEARCH.md` documents `resolved_compose_roles` → HISM import flow
- OS verify tier: 13+ genomes + `_STYLE_GENOME_GROUPS`

## v2.96.0 — Resolved compose roles in world manifest

- **`.world.json`** `style_genome.resolved_compose_roles` — effective role→lib map at export time
- **`sci_fi_deck.json`** grammar + **`scifi_deck_spine_v1`** genome (13 graph chains)
- Research presets for romanesque cloister + sci-fi deck spine graphs

## v2.95.0 — Final graph grammars + WESTERN_CASTLE compose

- **`romanesque_apse.json`**, **`sci_fi_deck_expansion.json`** — completes major graph externalization (12 chains)
- **`romanesque_apse_v1`**, **`scifi_deck_v1`** genomes with WESTERN_CASTLE compose overrides
- **`WESTERN_CASTLE`** role map in OS `compose_roles.json`

## v2.94.0 — Romanesque + Venetian grammars + genomes

- **`romanesque_cloister.json`**, **`venetian_canal.json`** — grammar externalization
- **`romanesque_cloister_v1`**, **`venetian_canal_v1`** genomes with `recursive_interior`
- 10 graph chains now OS grammar source of truth

## v2.93.0 — Gothic + sci-fi research presets

- **`scifi_airlock_graph`** preset — full airlock chain with genome + graph spawn
- **`gothic_cloister_graph`** preset — cloister walk with genome + graph spawn

## v2.92.0 — Gothic + sci-fi grammar manifests

- **`cloister.json`**, **`scifi_airlock.json`** — non-zen graph chains in OS grammar
- **`scifi_airlock_v1`** genome for airlock graph + `recursive_interior`
- Verify tier covers gothic/sci-fi `os_grammar` graphs

## v2.91.0 — Gothic genome + recursive_interior transform

- **`gothic_cloister_v1`** — first non-zen Style Genome (CLOISTER / WESTERN_CASTLE)
- **`recursive_interior`** surreal transform enabled for graph chains (progressive scale decay)
- Transform application filters by `applies_to` graph id

## v2.90.0 — Genome catalog metadata + tea preset

- **`_STYLE_GENOME_META`** cache at OS register (graph + surreal_transform per genome)
- Level Design UI shows graph/transform hints under catalog buttons
- Research preset **`zen_tea_garden`** for tea garden quick-launch

## v2.89.0 — Tea garden grammar + genome picker UI (Tier B complete)

- **`zen_tea_garden.json`** — final zen graph chain externalized to OS grammar
- **`zen_tea_garden`** genome with tea-garden compose role overrides
- Level Design panel lists full genome catalog via `select_style_genome` operator
- All 6 zen graphs now `os_grammar` source of truth

## v2.88.0 — Roji grammar + genome compose roles (Tier B)

- **`zen_roji_path.json`**, **`zen_karesansui_walk.json`** — externalized zen graph chains
- **`zen_roji_path`** genome with `compose_roles` per-genome overrides
- Sakura + courtyard genomes ship `compose_roles`; `.world.json` embeds role map

## v2.87.0 — Sakura walk + courtyard grammar manifests (Tier B)

- **`zen_sakura_walk.json`**, **`zen_shrine_courtyard.json`** — externalized graph module chains
- `merge_grammar_into_registry()` overwrites registry specs from OS grammar files
- Verify tier asserts `os_grammar` on axis, sakura walk, and courtyard graphs

## v2.86.0 — ZEN_SHRINE compose role polish (Tier B)

- Compose roles: `corner_tower` → goju pagoda, `monument` → tahōtō, `gate` → GB torii, `small` → GB lantern
- **`zen_shrine_courtyard`** genome for `ZEN_SHRINE_COURTYARD` graph + research preset
- Library + fallbacks aligned with GB kit path

## v2.85.0 — GB_ZEN_LANTERN kit (Tier B)

- **`GB_ZEN_LANTERN`** — greybox stone lantern (kiso, sao, hibukuro, kasa, hōju)
- Atom `stone_lantern_post`; graphs + grammar use GB kit instead of `ZEN_LANTERN` alias
- Fixed `GB_ZEN_HONDEN` kit registration typo in `integration.py`

## v2.84.0 — zen_shrine_sakura genome (Tier B)

- **`zen_shrine_sakura`** genome — sakura torii variant, `ZEN_SAKURA_WALK` default graph
- Sacred sequence through cherry allée path typology
- Research preset `zen_sakura_torii` uses dedicated genome

## v2.83.0 — zen_shrine_axis genome + vertical_stretch (Tier B)

- **`zen_shrine_axis`** genome — full sacred sequence through honden, `grammar_id: ZEN_SHRINE_AXIS`
- **`vertical_stretch`** surreal transform — Y-axis height exaggeration along graph chain
- `build_genome_manifest()` embeds `grammar_id`
- Research preset `zen_shrine_axis` uses dedicated genome (was `zen_shrine_v1` pilot)

## v2.82.0 — Genome manifest + axis_compression (Tier C complete)

- **`.world.json`** embeds `style_genome` DNA block via `build_genome_manifest()` / `resolve_genome_manifest()`
- Compose stamps `surreal_style_genome_id` on world root; export passes monolith for active genome
- **`zen_shrine_v1`** — `surreal_transform: axis_compression` enabled on genome
- World + OS verify tiers assert manifest embed and transform field

## v2.81.0 — Honden sanctuary (Tier C)

- **`GB_ZEN_HONDEN`** — raised sanctum, enclosed moya, engawa margin, threshold, noki
- Atom `honden_sanctuary` + node design card
- Compose `sacred` role → `_lib_GB_ZEN_HONDEN`
- `ZEN_SHRINE_AXIS` grammar — honden after haiden
- **`zen_honden_platform_rise`** property

## v2.80.0 — Tahōtō treasure pagoda (Tier C)

- **`GB_ZEN_TAHOTO`** — mokoshi base, drum body, double roof, sorin finial
- Atom `tahoto_treasure_tower` + node design card
- **`zen_tahoto_roof_span`** property
- Research preset `zen_tahoto_tower`

## v2.79.0 — MioUV invoke (Tier B complete)

- **Modifier** `miouv_pack_invoke` in procedural taxonomy + design card
- **`capabilities`** — MioUV / UVPackmaster addon detection
- **`integration`** — register `UV_OPERATOR_CLASSES` (was missing)
- **Level Design UI** — UV Proxy, MioUV Pack, UVPM Pack, Commit UV + status lines
- **`pipeline.uv_pack_hint()`** — trim-sheet pack workflow hint after generate
- **Verify** — UV operator registration tier

## v2.78.0 — Sakura torii variant (Tier B)

- **`GB_ZEN_SAKURA_TORII`** — blossom band on kasagi + petal accents on hashira
- Atom `sakura_torii_frame` (variant of `torii_frame`)
- `ZEN_SAKURA_WALK` graph entry module updated
- Genome flags: `torii_variant`, `sakura_graph` on `zen_shrine_v1`
- Research preset `zen_sakura_torii`

## v2.77.0 — Goju-no-tō pagoda (Tier B)

- **`GB_ZEN_GOJU_PAGODA`** — five-story pagoda greybox (plinth, tier cores/roofs, sorin)
- Atom `goju_pagoda_tower` + node design card
- Compose `corner_tower` → `_lib_GB_ZEN_GOJU_PAGODA`
- Research preset `zen_goju_pagoda`

## v2.76.0 — Haiden worship hall (Tier B)

- **`GB_ZEN_HAIDEN`** — genkan steps, raised haijo floor, posts, ranma transom, noki eave
- Atom `haiden_platform` + node design card + taxonomy entry
- **`zen_genkan_rise`** property (default 0.45 m)
- **`ZEN_SHRINE_AXIS`** grammar — haiden module after karesansui
- Research preset `zen_haiden_worship`

## v2.75.0 — Surreal Architecture OS (Zen pilot)

- **`deploy/surreal_os/`** — Style Genome, atoms, grammar loader, rules engine, taxonomy, critique
- **`zen_shrine_v1`** genome — floats, sacred_sequence, `ZEN_SHRINE_AXIS` default graph
- **`GB_ZEN_SANDO`** + **`GB_ZEN_KAIRO`** — shrine approach + cloister kits (v2.74)
- **`ZEN_SHRINE_AXIS`** — data-driven grammar graph (torii → sando → kairo → karesansui)
- **Compose** — `compose_roles.json` drives `ZEN_SHRINE` role→lib map via `resolve_compose_style()`
- **UI** — Style Genome picker, Apply, Spawn Graph (`os_ops.py`)
- **Surreal transform** — `axis_compression` post-chain hook in `spawn_graph()`
- **Research** — `research/zen/*` studies + node design cards for sando/kairo
- **Verify** — `_mcp_verify_os.py` tier in `run_verify.ps1 -Mode all`

## v2.73.0 — Sakura path kits (bridge, cherry allee, water edge)

- **`GB_ZEN_STONE_BRIDGE`** — deck, rails, abutments + bridge snaps
- **`GB_ZEN_CHERRY_ALLEE`** — sakura walk with blossom canopy + petal trim zones
- **`GB_ZEN_WATER_EDGE`** — stream bed, banks, stepping stones at bridge landings
- **`ZEN_SAKURA_WALK`** graph chain
- **`zen_stream_depth`** property for water-edge kits

## v2.72.0 — Karesansui + Machiai zen kits

- **`GB_ZEN_KARESANSUI`** — dry rock garden (sand bed, border stones, rake grooves)
- **`GB_ZEN_MACHIAI`** — waiting pavilion (posts, roof, bench)
- **`ZEN_KARESANSHUI_WALK`** graph + shrine courtyard uses greybox karesansui/machiai
- **Research presets** — karesansui garden + machiai pavilion

## v2.71.0 — Zen architecture expansion (engawa, bamboo fence, tobi-ishi)

- **`zen_kit.py`** — `GB_ZEN_ENGAWA`, `GB_ZEN_BAMBOO_FENCE`, `GB_ZEN_TOBIISHI` greybox builders + snap hooks
- **Graph library** — `ZEN_TEA_GARDEN` chain; roji/shrine graphs updated with new modules
- **Research presets** — engawa veranda, bamboo fence, tobi-ishi path quick-launch
- **World** — `spawn_zen_temple_plan` L-shaped compound + `plan_spawn_zen_temple` operator
- **Trim export** — per-kit trim groups for new zen greybox modules
- **Verify** — zen kit smoke + `ld_temple` world tier

## v2.70.0 — Beavel / Synthia / Higgsas pipeline + Polyhedra library

- **`bevel_bridge.py`** — Beavel Pro (`mesh.beavel_operator`) hybrid with native `MOD_BEVEL`; `bevel_backend` + `surreal_arch.bake_beavel`
- **`synthia_bridge.py`** — spawn wrapper, tagged capture, 4 `SYNTHIA_*` arch types with bmesh fallback; panel re-enabled
- **`higgsas_bridge.py`** — library path preference, `load_arch_nodes`, post-generate `higgsas_detail` pass
- **`capabilities.py` + `pipeline.py`** — optional-deps detection + ordered post-generate stages
- **`polyhedra.py`** — 14-shape registry (Kepler–Poinsot, Platonic, Archimedean, compounds); `spawn_polyhedron` operator
- **`bootstrap.py`** — addon preferences for Higgsas/Synthia paths; `repatch()` helper
- **Unicode** — `deploy/tools/fix_mojibake.py` + UI string restoration
- **Verify** — polyhedra smoke, bridge tiers, `_surreal_patched` assert; `register_overhaul` in headless path
- **UI** — Level Design: Bake Beavel Pro; Synthia panel dependency status; `FILE_TICK` icon fix

## v2.69.0 — World pipeline review + TD/LD contracts

- **TD manifest contract** — [`SURREAL_WORLD_MANIFEST.md`](SURREAL_WORLD_MANIFEST.md), `schema_version`, `hism_groups`, project MI paths in `ROLE_UE_HINTS`
- **LD QA checklist** — [`SURREAL_WORLD_LD_QA.md`](SURREAL_WORLD_LD_QA.md) + automated metrics tier in `_mcp_verify_world.py`
- **Unified verify** — `_mcp_verify_all.py` + `run_verify.ps1` (always `--factory-startup`)
- **FBX export verify tier** — per-role batch export in world verify
- **Layer 2 monolith extract** — library/compose/castle plan delegate to `surreal_world/` (no duplicate implementations)
- **UE importer** — [`Content/Python/import_world_manifest.py`](../Content/Python/import_world_manifest.py)

## v2.68.0 — Procedural world compose pipeline (AAA)

- **`surreal_world/` package** — library bake, plans, COLLECTION compose, UE manifest export
- **COLLECTION mode (default)** — non-destructive WorldRoot + linked instances + per-piece metadata
- **Fixes** — `is_sacred` tag dispatch, `BOULDER_PILE` in library spec, headless-safe library bake
- **ZEN_SHRINE** compose style + Zen Roji plan spawner
- **`export_world_ue`** operator — `surreal_arch_world_v1` JSON manifest
- **Verify** — `_mcp_verify_world.py` + dedicated `surreal_world_loop.ps1`

## v2.67.0 — Zen modular kit expansion

- **`zen_kit.py`** — `GB_ZEN_ROJI_STEP`, `GB_ZEN_TORII_GATE`, `GB_ZEN_TSUKUBAI` greybox builders + snap hooks for `ZEN_*` architecture types
- **Graph library** — `ZEN_ROJI_PATH`, `ZEN_SHRINE_COURTYARD` module chains (style: zen)
- **Research presets** — roji step, modular torii gate, tsukubai basin quick-launch
- **Trim export** — per-kit trim groups for zen greybox modules
- **Verify** — zen kit smoke + trim_groups tier in `_mcp_verify_overhaul.py`

## v2.66.11 — Trim export QA (micro)

- **`gn_trim_zone_faces`** in UE sidecar payload when GN trim zones are present
- Level Design QA row: trim group + GN trim-zone face counts
- Verify: trim-zone GN tier + export contract checks sidecar field (hot-reload safe)
- **`gb_bake_trim_colors`** routes `apply_trim_bake` through per-face `SURREAL_TRIM` vertex colors (`meshes.new_from_object` for GN-only meshes)
- Sidecar fields **`trim_color_layer`** / **`trim_bake_mode`** when zone bake active

## v2.66.10 — Trim wrapper hot-reload

- **`_wire_trim_box_wrapper`** re-applies after `surreal_greybox.attach_all` on every `patch_monolith` (fixes lost trim face attrs on addon reload)
- Verify tier unchanged; all GB_* kits still pass snaps + trim_groups

## v2.66.9 — Per-face trim zones in GN

- `_gb_box` geometry stamped with `surreal_trim_zone` / `surreal_trim_id` via `trim_color_bake.tag_trim_geometry`
- Arch/vault procedural segments tagged so **JoinGeometry** preserves face attributes through kit joins

## v2.66.8 — UE export sidecar

- **FBX sidecar JSON** — `write_sidecar_json()` writes `<fbx>.snap.json` on Bake & Export UE5
- **Snap normalization** — `normalize_snap_points()` standardizes type/rule casing in export payload
- **Level Design export row** — Bake & Export UE5 + Snap JSON buttons in N-panel / Level Design

## v2.66.6–2.66.7 — Stability + catalog dispatch

- ARCH_CATALOG-driven dispatch registry (`catalog_dispatch.py`)
- Named trim zones on kit `_gb_box` labels
- Verify script re-patches monolith after `importlib.reload`
- Gothic tracery panel snap points; idempotent overhaul class registration

## v2.66.0 — Growth plan implementation

### UE pipeline
- **Trim attribute bake** (`surreal_arch/trim_bake.py`) — writes `trim_id` vertex color layer + face attribute from trim metadata
- **Bake & Export to UE5** — auto-applies trim bake on baked mesh before FBX export
- **Bake Trim Attributes** operator in Level Design panel
- Extended snap JSON export with trim groups and UE material slot hints

### Engineering
- **`register_kit()` API** (`surreal_arch/kit_registration.py`) — single-call kit registration for builder + snap + dispatch
- **`surreal_greybox/` package** — extracted `_gb_box`, `_gb_join`, `_gb_bool_diff`, trim helpers, snap load utilities
- **Dynamic `_KIT_DISPATCH`** hook in generation pipeline
- **Workflow panel polls** — BLOCKOUT mode hides music, magic, Sverchok, Escher, effects, etc.

### Content
- **`GB_ROMANESQUE_APSE`** — semicircular choir apse with recess shell
- **Graph library** (style-grouped UI):
  - Romanesque Choir + Apse
  - Venetian Canal Block
  - Sci-Fi Command Deck (expanded)

### QA
- Extended `_mcp_verify_overhaul.py` — all `GB_*` kits, graphs, research presets, trim bake

---

## v2.65.x — Overhaul iterations

- v2.65.0 — Romanesque arcade, corridor offset, research presets, window reveals
- v2.65.1 — Brutalist panel wall, Romanesque cloister graph
- v2.65.2 — Venetian loggia bay
- v2.65.3 — Sci-Fi pressure door + airlock graph
- v2.65.4+ — ARCH_CATALOG glossary, quick-launch parity

## v2.64.0 — UI overhaul

- Searchable architecture picker, workflow modes, VIEW_3D panels
- Gothic kit, snap overlay, room graphs
