# Melodia -- Unified Pipeline Architecture

```
◇─◇──◇──◇─◇
```

## System Map

```
                    MELODIA PIPELINE
                          
  Blender                          Unreal Engine
  ═══════                          ═════════════
  surreal_arch ──FBX──> LiveLink :9876 ──> /Game/LiveLink/
  material_bridge ──.material_map.json──> resolve_material_crosswalk.py
  melodia_gn ──GN groups──> bake.py ──> GN_Library/
  melusina_portrait ──keyframes──> FBX export
  
  VOICEVOX :50021 ──WAVs──> /Game/Melodia/Characters/{Name}/Audio/
  Melusina :50022 ──WAVs──> /Game/Melodia/Characters/Melusina/Audio/
  
  Material Maker 1.7 ──.ptex graphs──> Material Functions ──> 4 Master Materials ──> 50+ Instances
  
  PCG Scatter ──role──> surreal_world/export.py ──> *.world.json ──> import_world_manifest.py ──> HISM actors
  
  UE MCP :9316 ──Python──> Blueprint creation, material audit, PIE control
  Blender MCP :9317 ──genome──> surreal_arch style application
  GMM Python runtime ──rules──> MelodiaCore C++ plugin ──> gameplay

  Deploy Tools
  ════════════
  deploy_all.ps1 / stop_all.ps1 / loop_status.ps1 ── 11 autonomous agent loops
  validate_setup.ps1 ── pre-flight check for collaborators
  sync_surreal_to_live.ps1 ── deploy/ SSOT -> Blender addon dir
```

---

## Component Registry

```
◇─── Blender Side ───◇
```

### surreal_arch/ (Melodia Studio Addon)

| Module | Purpose | Key files |
|--------|---------|-----------|
| **Live Bridge** | Port dashboard, LiveLink start/stop, live sync, Send+Materials | `live_bridge.py` |
| **Material Bridge** | Blender slot <-> UE material crosswalk, fuzzy matching, .material_map.json | `material_bridge.py` |
| **GN Stack** | Bagapie-style modifier stacking UI with search, 9 categories, 49 builders | `melodia_gn/stack.py` |
| **Builder Registry** | 49 auto-registered GN tree builders, lazy-derived TREE_TYPES | `melodia_gn/core.py` |
| **Error Logging** | 4-level logger with addon preferences debug toggle | `melodia_gn/logging.py` |
| **Living Portrait** | USTX/UST parser, 15-viseme mapper, keyframe engine for voice-driven facial animation | `melusina_portrait/` |
| **Genome Carousel** | Style genome selection + apply, 30+ genomes | `genome_carousel.py` |
| **MCP Server** | HTTP REST on :9317, genome/agent control, smoke harness | `blender_mcp.py` |
| **LiveLink Bridge** | TCP on :9876, FBX/texture/animation streaming to UE | `livelink_bridge.py` |
| **Branding** | N_PANEL_CATEGORY = "Melodia Studio" | `branding.py` |
| **Integration** | All class registration, monolith patching, melodia_gn wiring | `integration.py` |

### melodia_gn/ (Geometry Nodes Library)

| Category | Modules | Builders |
|----------|---------|----------|
| Primitives | `primitives.py` | circular_array, linear_array, grid_array, bounding_box, instance_on_spline |
| Profiles | `profiles.py` | column, baluster, post, rail, star_finial, lissajous |
| Math | `math_ops.py` | add, subtract, power_scale, exponent_blend, store_named_attr, attribute_math |
| Effects | `effects.py` | displace, wave, cast, wireframe, smooth, magic |
| Ornament | `ornament.py` | vine, radial, grid, frame, panel |
| Music | `music.py` | note_head, treble_clef, staff, harmonic, phrase |
| Castle | `castle.py` | crenellation, wall, tower, gatehouse, window, buttress, keep, curtain_wall, machicolations, stairs, assembler |
| Structures | `structures.py` | gazebo, arch, portico |
| Operations | `operations.py` | iterate, bounded |
| Infrastructure | `core.py`, `stack.py`, `bake.py`, `logging.py` | safe_node, link_sockets, builder registry, modifier stack UI, library baking |

### surreal_world/

| Module | Purpose |
|--------|---------|
| `export.py` | World manifest builder (.world.json), role-based material hints, HISM group assembly, FBX batch export |
| `snap_export.py` | UE snap point metadata, trim attachment |

### surreal_os/

| Module | Purpose |
|--------|---------|
| `genome/` | 50+ style genome JSON definitions (zen, gothic, brutalism, scifi, nikki) |
| `grammar/` | Grammar graph JSON definitions for recursive composition |
| `rules/` | Compose roles and catalog dispatch |

---

```
◇─── Unreal Engine Side ───◇
```

### LiveLink Integration

| Component | Purpose |
|-----------|---------|
| `livelink_unreal.pyc` | UE-side client: receives FBX, imports to /Game/LiveLink/, processes material/animation payloads |
| `init_unreal.py` | Startup: loads LiveLink module, registers EnvUI menus |

### Monolith MCP (:9316)

| Component | Purpose |
|-----------|---------|
| `MonolithClient` | JSON-RPC 2.0 client with 28 tool categories |
| `monolith_mcp_client.py` | Light wrapper with ping, call_tool, niagara_query, editor_query |
| `gmm/core/mcp_client.py` | Full-featured client with Python execution, blueprint creation, blend space setup, actor spawning |

### Material Pipeline

| Layer | Files | Count |
|-------|-------|-------|
| Material Maker Graphs | `Tools/MaterialMaker/*.ptex` | 5 graphs + 6 subgraphs |
| Material Functions | `/Game/EnvSandbox/Materials/Functions/MF_*` | 38 .uasset files |
| Master Materials | `M_Master_Toon_Universal`, `M_Master_Toon_Landscape_HeightBlend`, `M_Water_Master_Grand_v6`, 2x Impressionist | 5 masters |
| Material Instances | `/Game/EnvSandbox/Materials/Instances/` | 50+ instances |

### MelodiaCore Plugin

| System | Key files | Status |
|--------|-----------|--------|
| Battle Session | `MelodiaBattleSession.cpp/h` | Working (4 P0 bugs fixed) |
| Roguelike Run | `MelodiaRoguelikeRunSubsystem.cpp/h` | Working (GS-006/007 fixed) |
| Combat State | `MelodiaCombatStateComponent.cpp/h` | Working (GS-001/002 fixed) |
| Dungeon Coordinator | `MelodiaDungeonRunCoordinator.cpp/h` | Working (GS-007 fixed) |
| Rhythm Execution | `MelodiaRhythmExecutionComponent.cpp/h` | Working |
| Opening Flow | `MelodiaOpeningFlowSubsystem.cpp/h` | New, not yet compiled |
| NPC System | `MelodiaNPCDefinition.cpp/h` | Stub |

### GMM (Python Game Runtime)

| System | Module | Lines |
|--------|--------|-------|
| Battle Manager | `gmm/game/battle_manager.py` | 808 |
| Player State | `gmm/game/player_state.py` | 391 |
| Rhythm Clock | `gmm/game/rhythm_clock.py` | 273 |
| Data Registry | `gmm/game/data_registry.py` | 313 |
| Roguelike | `gmm/game/roguelike.py` | 336 |
| Roguelike Dungeon | `gmm/game/roguelike_dungeon.py` | 834 |
| Elements | `gmm/game/elements.py` | -- |
| Modifiers | `gmm/game/modifiers.py` | -- |
| Tokens | `gmm/game/tokens.py` | -- |

### NPC Integration

| Character | VOICEVOX ID | Dialogue | Voice WAVs | Blueprint |
|-----------|-------------|----------|------------|-----------|
| Zundamon | 3 | 20 lines | 20 WAVs | BP_Zundamon_NPC |
| Tohoku Zunko | 14 | 20 lines | 20 WAVs | BP_Zunko_NPC |
| Tohoku Kiritan | 5 | 20 lines | 20 WAVs | BP_Kiritan_NPC |
| Tohoku Itako | 6 | 21 lines | 21 WAVs | BP_Itako_NPC |
| Shikoku Metan | 2 | 7 lines | 7 WAVs | BP_Metan_NPC |
| Kyushu Sora | 16 | 7 lines | 7 WAVs | BP_Sora_NPC |
| Chubu Tsurugi | 17 | 7 lines | 7 WAVs | BP_Tsurugi_NPC |
| Melusina | 100 (SBV2) | 18 lines | -- | BP_Melusina |

---

```
◇─── Data Flow ───◇
```

### Build -> Export -> Import -> Gameplay

```
[Blender]                     [Unreal]                       [Gameplay]
    |                             |                              |
    v                             v                              v
surreal_arch gen           import_world_manifest.py       MelodiaCore
    |                             |                         C++ plugin
    v                             v                              |
surreal_world/export.py     HISM actor spawns              Rhythm battle
    |                             |                         Roguelike run
    v                             v                         NPC dialogue
.world.json ──────────>  /Game/Melodia/                     Token economy
    |                             |
material_bridge.py          resolve_material_crosswalk.py
    |                             |
.material_map.json ───────>  Auto-apply to meshes
```

### Voice Pipeline

```
VOICEVOX :50021                    Melusina :50022
    |                                  |
generate_all_voices.py         serve_melusina_voice.py
    |                                  |
Content/Melodia/Characters/    Content/Melodia/Characters/
  {Name}/Audio/*.wav             Melusina/Audio/*.wav
    |                                  |
    +────────── UE Import ────────────+
                    |
            ZunZunDialogueComponent
            (Blueprint playable)
```

### Material Pipeline

```
Material Maker 1.7 (.ptex JSON)
    |
    v
build_missing_subgraphs.py  (6 subgraphs)
build_surreal_tile_master_v2.py  (static + dynamic graphs)
    |
    v
Texture export (Manual via MM GUI or batch_mm_surreal_convert.py)
    |
    v
UE Material Functions (38 MF_*.uasset)
    |
    v
4 Master Materials (setup_master_universal.py, setup_landscape_height_blend.py, etc.)
    |
    v
50+ Material Instances (MI_Show_*, MI_Zen_*, MI_Melusina_*, MI_Impressionist_*, etc.)
    |
    v
PCG Spawner assignment (setup_pcg_universal.py)  OR  Material Bridge crosswalk (Blender)
```

---

```
◇─── Port Map ───◇
```

| Port | Protocol | Service | Direction |
|------|----------|---------|-----------|
| `9876` | TCP + JSON (length-prefixed) | LiveLink -- FBX, textures, materials, animations | Blender -> UE |
| `9317` | HTTP REST | Blender MCP -- genome apply, smoke harness, agent control | Any -> Blender |
| `9316` | HTTP JSON-RPC 2.0 | UE Monolith MCP -- Python execution, 1,325 tools across 28 categories | Any -> UE |
| `50021` | HTTP REST | VOICEVOX -- text-to-speech, 7 ZunZun characters, multi-style | Any -> VOICEVOX |
| `50022` | HTTP REST | Melusina Voice -- custom Style-Bert-VITS2 TTS model | Any -> Melusina |

---

```
◇─── Key Scripts Index ───◇
```

| Script | Domain | Purpose | Runtime |
|--------|--------|---------|---------|
| `Tools/setup_zunzun_studio.py` | Blender | Import all ZunZun models, studio layout, cameras, lighting | Blender |
| `Tools/generate_all_voices.py` | Voice | Batch VOICEVOX pipeline for 7 characters, 102 WAVs | Terminal |
| `Tools/serve_melusina_voice.py` | Voice | Custom SBV2 TTS server for Melusina | Terminal |
| `Tools/setup_voicevox.py` | Voice | Download, install, configure VOICEVOX | Terminal |
| `Tools/retarget_mmd_zunzun.py` | Animation | MMD motion retarget to ZunZun armature | Blender |
| `Tools/MaterialMaker/build_missing_subgraphs.py` | Materials | Build SG_Triplanar, SG_Flow_Generator, SG_Spherical_Projection | Terminal |
| `Content/Python/import_zundamon.py` | UE | Import Zundamon FBX, create materials, assign to mesh | UE Python |
| `Content/Python/create_zunzun_bps.py` | UE | Auto-create 7 NPC BPs, quest/shop/party data assets | UE Python |
| `Content/Python/resolve_material_crosswalk.py` | UE | Post-import material auto-resolver | UE Python |
| `Content/Python/fix_vertical_slice_p0.py` | UE | Flag and report P0 game bugs | UE Python |
| `Content/Python/setup_material_functions.py` | UE | Build/rebuild 17 material functions (Phase 2) | UE Python |
| `deploy/deploy_all.ps1` | Agent | Launch all 11 autonomous loops | Terminal |
| `deploy/loop_status.ps1` | Agent | Live dashboard of PID/state per loop | Terminal |
| `deploy/validate_setup.ps1` | Collab | Pre-flight check for new collaborators | Terminal |
| `deploy/sync_surreal_to_live.ps1` | Dev | Sync SSOT from deploy/ to live Blender addon directory | Terminal |
