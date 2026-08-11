# Surreal Architecture — Loop State

**Version:** 2.131.0  
**Loop sentinel:** `AGENT_LOOP_TICK_surreal_tierb`  
**Interval:** 300s — **endless loop armed** (monitored shell, AAA genome expansion prompt)

## Micro-cycle 53 — genome `family` schema (v2.98.0) ✓

- **`family`** field on all 13 genome JSON files (Zen, Gothic, Sci-Fi, Romanesque, Venetian)
- **`genome_family()`** helper — explicit field with id-prefix fallback
- Manifest + UI meta embed `family`; grouping uses schema not heuristics

## Micro-cycle 52 — genome UI groups + UE import notes (v2.97.0) ✓

- **`_STYLE_GENOME_GROUPS`** — Zen / Gothic / Sci-Fi / Romanesque / Venetian families in Level Design UI
- **`SURREAL_WORLD_RESEARCH.md`** — `resolved_compose_roles` → HISM import mapping
- OS verify asserts 13+ genomes and grouped catalog

## Micro-cycle 51 — manifest compose roles + SCI_FI_DECK (v2.96.0) ✓

- **`.world.json`** embeds **`resolved_compose_roles`** (merged OS + genome overrides at export)
- **`sci_fi_deck.json`** grammar + **`scifi_deck_spine_v1`** genome
- Research presets **`romanesque_cloister_graph`**, **`scifi_deck_graph`**
- World verify asserts `resolved_compose_roles` on ZEN compose export

## Micro-cycle 50 — final grammars + WESTERN_CASTLE compose (v2.95.0) ✓

- **`romanesque_apse.json`** + **`sci_fi_deck_expansion.json`** — all major graph chains externalized
- **`romanesque_apse_v1`**, **`scifi_deck_v1`** genomes with per-genome `compose_roles`
- **`WESTERN_CASTLE`** compose role map in `compose_roles.json` (12 `os_grammar` graphs)

## Micro-cycle 49 — romanesque + venetian (v2.94.0) ✓

- **`romanesque_cloister.json`** + **`venetian_canal.json`** — grammar manifests
- **`romanesque_cloister_v1`** + **`venetian_canal_v1`** genomes with `recursive_interior`
- OS verify covers 10 `os_grammar` graph chains

## Micro-cycle 48 — gothic/sci-fi research presets (v2.93.0) ✓

- **`scifi_airlock_graph`** — SCIFI_AIRLOCK graph + `scifi_airlock_v1` genome quick-launch
- **`gothic_cloister_graph`** — CLOISTER graph + `gothic_cloister_v1` genome quick-launch

## Micro-cycle 47 — gothic + sci-fi grammars (v2.92.0) ✓

- **`cloister.json`** + **`scifi_airlock.json`** — non-zen graph modules externalized
- **`scifi_airlock_v1`** genome — `SCIFI_AIRLOCK` + `recursive_interior`
- `recursive_interior` applies to `SCIFI_AIRLOCK` graph

## Micro-cycle 46 — gothic genome + recursive_interior (v2.91.0) ✓

- **`gothic_cloister_v1`** — first non-zen genome (`CLOISTER` graph, `WESTERN_CASTLE` compose)
- **`recursive_interior`** transform implemented (`modifier` type) + applies to `CLOISTER`
- `apply_surreal_transform()` respects `applies_to` graph filter; passes `graph_id` from spawn

## Micro-cycle 45 — genome UI metadata + tea preset (v2.90.0) ✓

- **`_STYLE_GENOME_META`** — cached graph + surreal_transform per genome at OS register
- Level Design catalog shows `default_graph · transform` under each genome button
- Research preset **`zen_tea_garden`** quick-launch

## Micro-cycle 44 — tea garden grammar + genome picker (v2.89.0) ✓

- **`zen_tea_garden.json`** — last hardcoded zen graph chain externalized
- **`zen_tea_garden`** genome with tea-garden `compose_roles`
- **Level Design UI** — genome catalog buttons (`select_style_genome`) from `_STYLE_GENOMES`
- OS verify asserts all 6 zen grammar graphs + genome catalog

## Micro-cycle 43 — roji grammar + genome compose roles (v2.88.0) ✓

- **`zen_roji_path.json`** + **`zen_karesansui_walk.json`** — externalized graph chains
- **`zen_roji_path`** genome with `compose_roles` overrides (gate, small, medium)
- Sakura + courtyard genomes gain per-genome `compose_roles`; manifest embeds role map
- OS verify asserts grammar + genome compose override wiring

## Micro-cycle 42 — grammar manifests (v2.87.0) ✓

- **`zen_sakura_walk.json`** + **`zen_shrine_courtyard.json`** — externalized graph modules
- `merge_grammar_into_registry()` refreshes existing registry entries from OS grammar (source of truth)
- OS verify asserts `os_grammar` flag on axis, sakura walk, and courtyard graphs

## Micro-cycle 41 — compose role polish (v2.86.0) ✓

- **ZEN_SHRINE compose roles** — `corner_tower` → goju pagoda, `monument` → tahōtō, `gate` → GB torii, `small` → GB lantern
- **`zen_shrine_courtyard`** genome — `ZEN_SHRINE_COURTYARD` graph + compose fallbacks
- Library adds `GB_ZEN_TORII_GATE`; OS verify asserts full role map

## Micro-cycle 40 — GB_ZEN_LANTERN (v2.85.0) ✓

- **`GB_ZEN_LANTERN`** — greybox tōrō stack (kiso → hōju), replaces `ZEN_LANTERN` in graphs
- Atom `stone_lantern_post` + node design card
- Graphs + `zen_shrine_axis` grammar updated; integration bug on honden register fixed
- Library + taxonomy + verify tier

## Micro-cycle 39 — zen_shrine_sakura genome (v2.84.0) ✓

- **`zen_shrine_sakura`** — `torii_variant: sakura`, `default_graph: ZEN_SAKURA_WALK`
- Sacred sequence: sakura torii → sando → cherry allée → karesansui
- Research preset `zen_sakura_torii` wired to genome
- OS verify asserts sakura variant fields

## Micro-cycle 38 — zen_shrine_axis genome (v2.83.0) ✓

- **`zen_shrine_axis`** genome — full sacred spine (torii → honden), `grammar_id: ZEN_SHRINE_AXIS`
- **`vertical_stretch`** surreal transform — Y-axis height ramp from `verticality` DNA
- Research preset `zen_shrine_axis` points at new genome
- OS verify asserts genome + transform registry

## Micro-cycle 37 — axis_compression (v2.82.0) ✓

- **`zen_shrine_v1`** — `surreal_transform: axis_compression` enabled
- `spawn_graph` post-chain applies transform via `rules_engine.apply_surreal_transform`
- OS verify asserts genome field + transform registry

## Micro-cycle 36 — genome manifest export (v2.82.0) ✓

- **`build_genome_manifest()`** / **`resolve_genome_manifest()`** in `surreal_os/genome.py`
- `.world.json` payload embeds **`style_genome`** block (id, DNA sliders, sacred_sequence, prop_defaults)
- Compose stamps **`surreal_style_genome_id`** on world root; export passes monolith for active genome
- World verify asserts `style_genome` for ZEN_SHRINE compose

## Micro-cycle 35 — honden (v2.81.0) ✓

- **`GB_ZEN_HONDEN`** — main sanctuary (moya, engawa, threshold, noki)
- Atom `honden_sanctuary` + node card
- Compose `sacred` → `_lib_GB_ZEN_HONDEN`
- `ZEN_SHRINE_AXIS` grammar slot after haiden
- Property `zen_honden_platform_rise`

## Tier C backlog

_Complete._

## Tier B — complete

All zen graph chains externalized; genome catalog + compose overrides wired. Polish cycle 45 done.

## Loop milestone — tick 25

**25 ticks** at 120s interval; v2.82 → v2.98 (17 micro-cycles). Tier B/C complete; gothic/sci-fi/romanesque genome families live.

## Micro-cycle 54 — tick 26 (v2.99.0)

- **`asian_city_v1`** genome — `ASIAN_CITY` compose roles externalized to OS
- **`brutalist_plaza_v1`** genome — concrete plaza preset with `axis_compression`
- Verify: 15 genomes; Asian + Brutalist family tiers

## Micro-cycle 55 — tick 27 (v2.100.0)

- **`ASIAN_CITY`** + **`BRUTALIST_PLAZA`** OS grammar graphs (15 chains total)
- Genomes retargeted from borrowed VENETIAN_CANAL / ROMANESQUE_CLOISTER spines
- `axis_compression` applies to `BRUTALIST_PLAZA`; research presets added

## Micro-cycle 56 — tick 28 (loop ops)

- Default wake interval **120s → 300s** (`start_cursor_agent_loop.ps1`, `cursor_surreal_agent_loop.ps1`)
- Formal **`cursor_surreal_tierb_loop.ps1`** + `start/stop_surreal_tierb_loop.ps1` for `AGENT_LOOP_TICK_surreal_tierb`
- Tier B/C backlog complete — loop enters maintenance cadence

## Micro-cycle 57 — tick 29 (v2.101.0)

- OS verify: partial **`ASIAN_CITY`** graph spawn tier (pailou → lane → pavilion)
- Fixed invalid grammar enums (`FLAT`→`RECESS`, `WOOD`/`CONCRETE`→`AUTO`/`STONE`) caught by spawn verify
- Restarted tier-B loop at **300s** — monitored shell session (replaces finished 120s inline loop + hidden PID 58116)

## Micro-cycle 58 — tick 30 / 300s tick 1 (v2.102.0)

- OS verify: partial **`BRUTALIST_PLAZA`** graph spawn tier (pilotis → panel wall → corridor)
- First **300s** maintenance wake — symmetric spawn coverage with Asian family

## Micro-cycle 59 — tick 31 (v2.103.0)

- **`asian_city_recursive_v1`** genome — `recursive_interior` on `ASIAN_CITY` graph
- World export: `ASIAN_CITY` compose auto-stamps `asian_city_v1` + manifest embed verify tier
- Genome catalog: **16** entries

## Micro-cycle 60 — tick 32 / 300s tick 2 (v2.104.0)

- World verify: **`brutalist_plaza_v1`** manifest embed on WESTERN_CASTLE motte compose
- OS verify: `axis_compression` applies to `BRUTALIST_PLAZA` explicit tier

## Micro-cycle 61 — tick 33 / 300s tick 3 (v2.105–v2.106)

- **v2.105** — research presets with `graph_id` spawn full chains (not single `generate()`)
- **v2.106** — curated playable presets retargeted: Gothic Cloister, Monastery Cloister, Temple Compound → OS graph spawns

## Micro-cycle 62 — tick 34 / 300s tick 4 (v2.107.0)

- Five more curated presets → graph spawns: Chapel, Zen Courtyard, Moorish Courtyard, Brutalist Plaza, Covered Bazaar
- New research presets: `romanesque_apse_graph`, `venetian_canal_graph`

## Micro-cycle 63 — tick 35 / 300s tick 5 (v2.108.0)

- Six more graph retargets: Shinto Shrine, Sci-Fi Atrium, Tea Pavilion, Venetian Palazzo, Chinese Pailou, Market Colonnade
- **14** curated playable presets now use `_make_graph_preset_op`

## Micro-cycle 64 — tick 36 / 300s tick 6 (v2.109.0)

- Basilica Nave, Japanese Gate, Civic Town Hall, Guild Hall → OS graph spawns
- Research preset: `zen_roji_path_graph`
- **18** curated playable presets on graph spawns; tower clones largely cleared from civic/asian buckets

## Micro-cycle 65 — tick 37 / 300s tick 7 (v2.110.0)

- Hypostyle Hall + Baroque Piazza → graph spawns (`BRUTALIST_PLAZA`, `VENETIAN_CANAL`)
- OS verify: `audit_graph_presets()` tier — **17** research presets with `graph_id`
- **20** curated playable presets on graph spawns

## Micro-cycle 66 — tick 38 / 300s tick 8 (v2.111.0)

- **`SCIFI_AIRLOCK`** curated playable preset → `scifi_airlock_graph` spawn
- OS verify: `scifi_airlock_graph` partial spawn tier
- **21** curated graph presets; preset retarget wave largely complete

## Micro-cycle 67 — tick 39 / 300s tick 9 (v2.112.0)

- Genome + research preset enum sweep (`WOOD`/`METAL`/`FLAT` → valid Blender values)
- `audit_grammar_enums()` OS verify tier for all 15 grammar chains

## Loop milestone — 300s tick 10 (v2.113.0)

**10 maintenance ticks** at 300s; v2.105→v2.113 preset retarget wave complete (**21** graph curated presets, enum audits live).
Removed stale `.yaml` genome duplicates — `.json` is sole source of truth for `load_genome()`.

## Micro-cycle 68 — tick 40 / 300s tick 11 (v2.114.0)

- **`western_castle_v1`** genome — default `WESTERN_CASTLE` compose stamp + manifest embed verify
- Genome catalog: **17** entries; Western family

## Micro-cycle 69 — v2.115.0 (filigree + Art Nouveau)

- **`FILIGREE_PANEL`** + **`FILIGREE_RAIL_INSET`** generators — 3 styles (vine, gothic iron, geometric)
- **`art_nouveau_v1`** genome + **`ART_NOUVEAU`** grammar graph (6 modules)
- Curated presets: filigree vine/geometric/rail + Art Nouveau facade graph
- Genome catalog: **18**; graph research presets: **18+**

## Micro-cycle 70 — v2.116.0 (Moorish courtyard set)

- **`moorish_courtyard_v1`** genome + **`MOORISH_COURTYARD`** grammar (horseshoe gate, arabesque, arcade, fountain)
- Retargeted **Moorish Courtyard** curated preset from VENETIAN_CANAL → real OS graph
- **`MOORISH_COURTYARD`** compose style + library bake; manifest embed verify
- Genome catalog: **19**; graph research presets: **19+**

## Micro-cycle 71 — v2.117.0 (Renaissance piazza set)

- **`renaissance_piazza_v1`** genome + **`RENAISSANCE_PIAZZA`** grammar (facade, arcade, balustrade, fountain, pillar, dome)
- **`RENAISSANCE_PIAZZA`** compose style + curated graph preset
- Genome catalog: **20**; graph research presets: **20+**

## Micro-cycle 72 — v2.118.0 (Venetian canal compose) ✓

- **`venetian_canal_v1`** retargeted to **`VENETIAN_CANAL`** compose style (was WESTERN_CASTLE bleed)
- Compose roles: loggia medium, palazzo large, bridge gate + `recursive_interior` manifest verify
- **Repair:** truncated `surreal_architecture_gen.py` tail restored from git; full verify green

## Micro-cycle 73 — v2.119.0 (Gothic cloister compose) ✓

- **`gothic_cloister_v1`** retargeted to **`GOTHIC_CLOISTER`** compose style (was WESTERN_CASTLE bleed)
- Compose roles: corridor medium, gothic portal gate, chapel sacred + library bake
- Manifest embed verify for `recursive_interior` + resolved gate role

## Micro-cycle 75 — v2.121.0 (Sci-Fi industrial yard + endless loop) ✓

- **Endless tier-B loop** armed via monitored `cursor_surreal_tierb_loop.ps1` (300s, AAA expansion prompt)
- **`scifi_industrial_yard_v1`** genome + **`SCI_FI_INDUSTRIAL_YARD`** grammar (pillar hall, catwalk, bulkhead, corridor)
- Curated graph preset + research quick-launch; Sci-Fi family **4** genomes; catalog **25**

## Micro-cycle 76 — v2.122.0 (Sci-Fi deck compose style) ✓

- **`SCIFI_DECK`** compose style + library bake (corridor, room, catwalk, pillar hall, pressure door)
- **`scifi_deck_v1`** + **`scifi_deck_spine_v1`** retargeted off WESTERN_CASTLE bleed
- Manifest embed verify for `recursive_interior` + resolved pressure-door gate role

## Micro-cycle 77 — v2.123.0 (Sci-Fi compose family complete) ✓

- **`scifi_airlock_v1`** + **`scifi_industrial_yard_v1`** retargeted to **`SCIFI_DECK`** compose
- Per-genome compose role overrides (airlock sealed chamber, industrial pillar-hall large)
- World manifest embed verify for both Sci-Fi genomes

## Micro-cycle 78 — v2.124.0 (Byzantine basilica monolithic set) ✓

- **`byzantine_basilica_v1`** genome + **`BYZANTINE_BASILICA`** grammar (7 modules: narthex, arcade, cusped arch, vault, pillar, rose, dome)
- **`BYZANTINE_BASILICA`** compose style + library bake; `vertical_stretch` transform
- Curated graph preset + research quick-launch; genome catalog **26**

## Micro-cycle 79 — v2.125.0 (Baroque church monolithic set) ✓

- **`baroque_church_v1`** genome + **`BAROQUE_CHURCH`** grammar (facade, ogee portal, ribbed vault, niche, balustrade, dome)
- **`BAROQUE_CHURCH`** compose style + library bake for baroque niche; `recursive_interior` transform
- Curated graph preset + research quick-launch; genome catalog **27**

## Micro-cycle 80 — v2.126.0 (Gothic chapter house variant) ✓

- **`gothic_chapter_house_v1`** genome + **`GOTHIC_CHAPTER_HOUSE`** grammar (portal, nave, bay, buttress, transept bend, tracery)
- **`GOTHIC_CHAPTER_HOUSE`** compose style + curated graph preset; Gothic family **2** genomes
- World manifest embed verify; catalog **28**

## Micro-cycle 81 — v2.127.0 (Gothic nave crossing variant) ✓

- **`gothic_nave_crossing_v1`** genome + **`GOTHIC_NAVE_CROSSING`** grammar (portal, long nave, T-crossing, transept, rose clerestory)
- **`GOTHIC_NAVE_CROSSING`** compose style + `vertical_stretch`; Gothic family **3** genomes; catalog **29**

## Micro-cycle 82 — v2.128.0 (Romanesque compose polish) ✓

- **`ROMANESQUE_CLOISTER`** + **`ROMANESQUE_APSE`** dedicated compose styles + library bake for apse module
- **`romanesque_cloister_v1`** + **`romanesque_apse_v1`** retargeted off WESTERN_CASTLE bleed
- World manifest embed verify for both Romanesque genomes

## Micro-cycle 83 — v2.129.0 (Brutalist + Western compose retarget) ✓

- **`BRUTALIST_PLAZA`** dedicated compose style + library bake for `GB_BRUTALIST_PANEL_WALL`
- **`brutalist_plaza_v1`** retargeted off WESTERN_CASTLE bleed → `BRUTALIST_PLAZA` compose
- **`western_castle_v1`** — `recursive_interior` + CLOISTER-aligned gate/corridor compose roles
- World manifest embed verify for both genomes

## Micro-cycle 84 — v2.130.0 (Asian city recursive compose polish) ✓

- **`ASIAN_CITY_RECURSIVE`** grammar + dedicated compose style (kura-forward alley roles)
- **`asian_city_recursive_v1`** retargeted off shared `ASIAN_CITY` bleed → recursive grammar + compose
- World manifest embed verify for `recursive_interior` + resolved kura medium role

## Next loop targets

- Mesoamerican pyramid courtyard (new family)
- Art Nouveau / Moorish manifest parity audit (compose tests green)
- Industrial Art Deco hybrid or Streamline Moderne variant

## Micro-cycle 85 — v2.131.0 (Art Deco lobby set) ✓

- **`art_deco_lobby_v1`** genome + **`ART_DECO`** grammar (tessellation tower, geometric panel wall, chevron filigree, cusped portal, obelisk)
- **`ART_DECO`** compose style + library bake for **`TESSELLATION_TOWER`**
- Research preset `art_deco_lobby_graph` + curated playable preset; `vertical_stretch` transform
- World manifest embed verify; genome catalog **30**
