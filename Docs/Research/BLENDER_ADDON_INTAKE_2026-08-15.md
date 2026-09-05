# Blender Addon Intake — 2026-08-15

**Scope:** every entry in `C:\Users\froma\AppData\Roaming\Blender Foundation\Blender\5.2\scripts\addons` (77 entries), plus `C:\EnvironmentPortfolio\BS_GodFile\Tools\BlenderAddons\`.
**Method:** each `bl_info` dict was parsed programmatically from `__init__.py` / single-file headers / nested addon roots. Nothing below is inferred from a folder name unless explicitly marked **UNIDENTIFIED** or **INFERRED FROM CODE**.
**Project context:** Melusina — anime female character, Blender → Unreal Engine 5.8. Character art, rigging, weight painting, facial blendshapes, cloth/outfits, environment art.

Relevance scale: **5** = core to Melusina · **4** = strong support · **3** = situational · **2** = marginal · **1** = irrelevant to this project.

---

## 1. Full inventory

### Rigging / Skinning

| Addon (folder) | What it is (evidence) | Rel. | Notes |
|---|---|---|---|
| `voxel_skinning` | **Voxel Heat Diffuse Skinning** v3.5.3, mesh online. `"description": "Voxel skinning toolset"`, `wiki_url: mesh-online.net/vhd.html`. Ships `voxel_heat_diffuse_skinning.py`, `surface_heat_diffuse_skinning.py`, `corrective_smooth_baker.py`, `joint_alignment_tool.py` | **5** | The single most valuable weight tool present. Voxel heat diffuse beats Blender's "Automatic Weights" badly on layered/loose geometry (skirts, sleeves, hair). Corrective Smooth Baker bakes a corrective-smooth modifier into real weights → export-safe for UE. `blender: (2,80,0)` — old target, verify it loads on 5.2. |
| `SwingyBonePhysicsAddon` | **Swingy Bone Physics** v1.9.0. `"An easy-to-use, artist friendly bone chain physics solver"`, doc_url `swingy-bone-physics.github.io/wiki/` | **4** | Hair/skirt/ribbon secondary motion. Blender-side only — UE needs its own AnimDynamics/Kawaii Physics equivalent, but useful to author and preview the chains and to bake reference animation. |
| `Jiggle_Maker` | v1.4. No description, but **INFERRED FROM CODE**: `__init__.py` loads `meshes/Boob_Proxy_Big.fbx / _Med / _Small`, creates vertex groups on fixed face indices and wires an armature modifier | **3** | Very narrow, proxy-mesh-driven chest jiggle rig. Overlaps Swingy Bone. Use Swingy Bone instead unless you specifically want its preset proxies. |
| `remap_presets` | **No addon** — 5 loose `.bmap` files: `unreal_mannequin_remap.bmap`, `mixamo_fk.bmap`, `mixamo_ik.bmap`, `mixamo_fbx_ik.bmap`, `unity_export.bmap`. Contents are bone-name pairs: `c_foot_ik.r → foot_r`, `c_neck.x → neck_01`, `thigh_twist_01_l`, `ik_hand_gun` | **4 (as data)** | These are **Auto-Rig Pro Remap** preset files, and the `c_*` naming is Auto-Rig Pro's rig prefix. **Auto-Rig Pro itself is NOT installed.** These presets are inert without it. Strong evidence the intended rig pipeline was ARP → UE Mannequin. See Gaps. |
| `autoConstraintsFree_v1_1_0` | **autoConstraints Free** v1.1.0, SpaghetMeNot. Category `Transform`, description is just a Telegram link | **2** | Constraint-automation helper for animation, not rigging deformation. |
| `_HOLD_20260730/rokoko-studio-live-blender-master` | **Rokoko Studio Live for Blender** v1.4.3, Rokoko Electronics | **3 (held)** | In the `_HOLD_` folder, i.e. not loaded. Contains the retargeting + **face shapekey** modules — the only facial-adjacent code in the whole set. Only useful if you own Rokoko hardware/Studio. |

### Weight painting

Nothing in this set is a dedicated weight-*painting* UX addon (no brush/gradient/mirror/normalize toolkit). What exists is weight *generation*:

| Addon | Rel. | Notes |
|---|---|---|
| `voxel_skinning` (above) | **5** | Base-weight generation + corrective smooth baking. This is your base setup. |
| `MACHIN3tools` | 3 | Contains `shape_key` handling in its operators, and general mode-switching/pie QoL that speeds up paint↔pose iteration. Not a weight tool per se. |

### Facial / blendshape

**Nothing.** A recursive `grep -ril "arkit"` across all 77 entries returned **zero hits**. No Faceit, no FACEIT/ARKit generator, no shape-key manager, no corrective-shape driver tool. The only shape-key-aware code paths are incidental (`send2ue` export IO, `animaide`, `Animation_Layers`, `audvis`, Rokoko in `_HOLD_`). See Gaps — this is the largest hole.

### Cloth / garment

| Addon | What it is (evidence) | Rel. | Notes |
|---|---|---|---|
| `wrapper_addon` | **Wrapper Addon** v1.0.0, Pamir Bal. `bl_info` description is empty; **INFERRED FROM CODE** — operators are `Generate Clothes`, `Generate Wrap`, `Set cloth`, `Set Collision`, `Add Solidify`, `Add Subd`, `Bake`, `Clear`, `Reset` | **4** | A shrink-wrap/cloth-drape garment generator: wraps a surface to the body, adds solidify + subdiv, runs cloth sim, bakes. This is your best in-set answer to garment fitting and body-clipping. Cryptic name, real utility. |
| `Curtain_Maker_Pro_S4c_v6` | **Curtain Maker Pro (Procedural)** v1.1.6. `"Create and live-edit procedural curtain meshes (quad topology) with pin controls, presets, and optional cloth simulation"` | **3** | Sold as curtains, but quad-topology + pin + cloth = usable for skirts, capes, drapery folds. Repurposable. |
| `fluffy_maker` | **Fluffy Maker** v1.0.0, "Blender Procedural". Empty description; Serpens-generated addon (`sna_` operator prefix pattern) | **3** | **Partially unidentified** — no description in `bl_info`. Name + author line implies procedural fluff/fur geometry (collar trim, fur lining). Verify in-app before relying on it. |
| `ctools_braids` | **CTools Braids** v5.0.1, Carlsu. Empty description; **INFERRED FROM CODE**: node names `_Hair Braids Generator`, `RealizeObject`, and a `convert_uv_attr` operator | **4** | Geometry-Nodes braid generator with a realize + UV-convert step, so output is bakeable to real geometry with UVs. Directly relevant to anime hair. |

### Retopo / UV

| Addon | What it is | Rel. | Notes |
|---|---|---|---|
| `ZenUV` | **Zen UV** v5.0.3.0. `"Optimize UV mapping workflow"`, doc_url zenmastersteam.github.io | **5** | Strongest UV tool here by a wide margin. Texel density, trims, stacking, UDIM/packing — all the things UE texel-density consistency needs. |
| `quad_remesher` | **Quad Remesher Bridge** v1.3.0, Maxime (Exoside). `"description": "https://"` (placeholder) | **5** | Auto-retopo. Essential for turning sculpts into a deformable quad cage. Requires a Quad Remesher license. |
| `UvSquares-master` | **UV Squares** v1.15.0. `"UV Editor tool for reshaping quad selection to grid"` | **3** | Small, useful, non-conflicting with ZenUV. Grid-straightening for hair cards and trims. |
| `quad_unwrap-master` | **Quad Unwrap** v1.0.1, Keith Boshoff. `blender: (2,80,0)`, no description field | **1** | Superseded by ZenUV. Ancient. Uninstall candidate. |
| `Mesh Cleaner Pro v0.1.3` | **Mesh Cleaner Pro** v0.1.3, Bayankin Artem. `"Professional mesh cleaning with healing brush"`, `blender: (4,5,0)` | **3** | Modern target version. Useful pre-export mesh hygiene (non-manifold, doubles). |
| `MESHmachine` | **MESHmachine** v0.16.0, MACHIN3. `"The missing essentials."` | **3** | Hard-surface. Relevant for armor/props/accessories, not for the body. |
| `speedsculpt` | **SpeedSculpt** v0.2.3, pitiwazou. `"Create models for sculpt and manage Dyntopo sculpt"` | **3** | Sculpt-stage blockout management. |
| `Beavel` | **Beavel Pro** v1.1.0, Egret. `"Bevel your Edges Like a Pro"`. `warning: "Save your work and bevel with care..."` | **2** | Bevel workflow tool. Hard-surface accessories only. |
| `projection_modeling` | **Projection modeling** v1.1.4. `"Addon for modeling using projections of 2D projections objects (mesh or curves)"` | **3** | Orthographic-reference modeling — genuinely useful for building an anime character from front/side concept art. |
| `ocd_2` | **OCD - One Click Damage** v2.0.2, VFXGuide | **1** | Procedural damage/dents. Environment/prop only. |
| `CURVEmachine` | **CURVEmachine** v1.4.1, MACHIN3. `"The missing (POLY + NURBS) Curve essentials."` | **2** | Curve editing; marginal use for hair-card guide curves. |
| `Handy Curve Profile` | **Handy Curve Profile** v1.4.5, "Young". Empty description; **INFERRED FROM CODE**: drives `curve_profile_squash` / `_stretch` / `_scale` on objects tagged `HCP_Pro` / `HCP_End` | **2** | Curve-profile squash/stretch rig for extruded shapes. Prop/trim work. |
| `Advanced-Cones-master` | **Advanced Cones** v2.0.2. `"Tool to generate various nose cone shapes"` | **1** | Rocket nose cones. Irrelevant. |
| `coiled_spring` | **Coiled Spring** v1.0 | **1** | Irrelevant. |
| `quicksnap-1_4_9` | **QuickSnap** v1.4.9, Julien Heijmans. `"Quickly snap objects/vertices/curve points"` | **3** | General precision-placement QoL. Useful for accessory placement. |
| `MACHIN3tools` | **MACHIN3tools** v1.10.1 'DeusEx'. `"Streamlining Blender 3.6+."`, `location: "Everywhere"` | **4** | Broad workflow accelerator — pies, smart modes, mirroring, group. High daily value. |
| `Surface Fill v0.2.7` | **Surface Fill** v0.2.7, Bayankin Artem. `"Fill surfaces and edges with tiled objects (boards, tiles, etc.)"`, `blender: (4,5,0)` | **2** | Environment trim/tiling. |
| `Combine V2` | **Combine** v2.0.0, studioromanrec. No description | **2 — BROKEN INSTALL** | The addon is nested one level too deep: `Combine V2/Combine V2/__init__.py`. Blender will not register it as installed. Purpose unverified. |

### Texturing / baking

| Addon | What it is | Rel. | Notes |
|---|---|---|---|
| `SimpleBake` | **SimpleBake** v2.3.2. `"Simple baking of PBR and other textures"`, `blender: (4,5,2)` — **newest Blender target in the entire set** | **5** | The strongest and most current bake tool here. Use this one. |
| `Sanctus-Bake` | **Sanctus Bake** v1.0.0. `"Utility addon for baking textures"`, doc_url `sanctuslibrary.xyz/.../baking-procedural-materials` | **3** | Purpose-built to bake **Sanctus Library** procedural materials specifically. Keep it only as the companion to Sanctus-Library; don't use it as a general baker. |
| `auto_bake` | **Auto Bake** v1.5, Tsybe. `"Automate your texture baking and saving process, set up baked versions automatically for materials and objects, and export the baked objects!"` | **2** | Batch-oriented. Overlaps SimpleBake. |
| `Blender-BakeLab2-master` | **BakeLab** v2.0.1. `"Bake textures easily"`, `blender: (2,81,0)` | **1** | Oldest of the four bakers. Uninstall candidate. |
| `Sanctus-Library` | **Sanctus-Library** v3.3.2. `"Sanctus Material Library"`, 2469 files | **3** | Large procedural material library. Grep found no toon/anime/cel-specific shaders — it is a PBR/stylized-realistic library. Useful for outfit fabrics and environment, **not** an anime character shader solution. |
| `deep_paint_pro_v1.2.7` | **Deep Paint Pro** v1.2.7, VEDA. Category `Pipeline`, `"Deep Paint Workflow"`, doc_url gakutada.com/deeppaint | **4** | Texture-painting workflow layer (layered paint / channel management). The closest thing to a Substance-style paint layer stack in-Blender. Also one of the few things touching `weight_paint` code paths. |
| `SeamlessLab` | **SeamlessLab** v1.0.0, KunyongChen. `"Automated Tiling for Blender's Procedural Textures."` | **2** | Tileable procedural textures — environment/fabric. |
| `poliigon-addon-blender` | **Poliigon** v1.16.1. `"Load models, textures, and more from Poliigon and locally"` | **3** | Asset/texture sourcing for environment. Requires a Poliigon account. |
| `assets_library_builder` | **Assets Library Builder** v2.0.5, SHEEP. `"Helps to build assets library with custom settings"` | **3** | Worth using to catalog Melusina's outfit pieces/accessories as a real Asset Browser library. |

### Animation

| Addon | What it is | Rel. |
|---|---|---|
| `Animation_Layers` | **Animation Layers** v2.2.6, Tal Hershkovich. `"Simplifying the NLA editor into an animation layers UI and workflow"` | **4** — layered animation authoring, useful for additive facial/body passes |
| `animaide-master` | **AnimAide** v1.0.38, Ares Deveaux. `"Helpful tools to manipulate keys on f-curves"`. `warning: "This addon is still in development."` | **4** — ease/blend/tween tooling |
| `AnimationRetimer-main` | **Animation Retimer (Multi-Object)** v1.1.0. `"Scale animation between markers for multiple selected objects, preserving key types."` Author field literally reads `"Your Name (Modified by AI)"` | **3** — functional but clearly an ad-hoc/AI-modified script; treat as unsupported |
| `AE2BLEND_1_3_1` | **AE2Blend** v1.2. `"Copy AfterEffects transform data directly into Blender"`. `warning: tested with AE CC 2017 and Blender 2.79` | **1** — abandonware, irrelevant |
| `sound_waveform_display` | **Sound Waveform Display** v2.0.0, Samuel Bernou. `blender: (5,0,0)` | **2** — only if doing lipsync-to-audio by hand |
| `audvis` | **AudVis** v8.0.0. Audio visualization drivers | **1** |
| `VSEQF-master` | **VSE Quick Functions** v5.0.2, `blender: (5,0,0)` | **1** — video sequencer |
| `Bligify-master` | **Bligify** v1.3.9. `"export/import animated GIF from VSE"`. `warning: "Requires imagemagick & gifsicle"` | **1** |

### Export / UE pipeline

| Addon | What it is | Rel. | Notes |
|---|---|---|---|
| `send2ue` | **Send to Unreal** v2.6.7, `"Epic Games Inc (now a community fork)"`, wiki `poly-hammer.github.io/BlenderTools/send2ue`, `blender: (3,6,0)` | **5** | The **Poly Hammer maintained fork** — newer than Epic's abandoned original. This is the one to keep. |
| `BlenderTools-20231109043947` | Contains **Send to Unreal v2.4.3**, Epic Games Inc, wiki `epicgames.github.io/BlenderTools/send2ue` | **CONFLICT** | Same Python module name `send2ue`, older version. **Two copies of the same addon are installed.** See §4. |
| `Blender-Unreal-Export-Addon` | **Unreal Exporter** v4.0.1, Tarmunds. `"Exports selected objects or hierarchies into separate files at the provided path. Also include some option for Yup engine, and to join meshes before export."`, `blender: (4,5,0)`, doc_url tarmunds.gumroad.com | **4** | A batch FBX exporter, not a live bridge. Complementary to send2ue, not redundant with it — good for outfit-variant batch export. Newest Blender target of the three. |
| `collider_tools` | **Collider Tools** v1.0.1, Matthias Patscheider. `"create physics colliders for games and real-time applications"` | **4** | UE-facing collision authoring — UCX naming conventions for props/environment. |
| `blender_mcp_addon.py` / `addon.py` | Both are **Blender MCP** v1.2. `"Connect Blender to Claude via MCP"`. Opens a socket server on **port 9876**, and defines `blendermcp_auto_start_server` | **3 — see §4 warning** | Two identical copies loose at addons root. This is the same class of auto-starting network daemon the 2026-07-30 manifest quarantined. |

### Environment / procedural

| Addon | What it is | Rel. |
|---|---|---|
| `sverchok-master` | **Sverchok** v1.4.0. `"Parametric node-based geometry programming"`, 3831 files | 3 |
| `archipack_20` | **Archipack PRO** v2.7.2. `"Architectural objects and 2d polygons detection from unordered splines"` | 3 |
| `surreal_architecture_gen.py` | **Melodia Studio — Surreal Architecture** v2.131.0, Melodia Team, `blender: (5,2,0)`. `"Procedural surreal architecture with style genomes, greybox kits, GN builders, and game pipeline. 56 styles, 49 GN builders, 8 architectural groups."` | 4 — project-owned, and the only addon actually targeting Blender 5.2 |
| `surreal_arch`, `surreal_greybox`, `surreal_os`, `surreal_world` | **No `bl_info` in any of them** — support packages for the above (`greybox_graph.py`, `genome.py`, `rules_engine.py`, `export.py`, `taxonomy.py`). Not standalone addons | 4 (as libraries) — **but see §4, these are the previously-quarantined loose files** |
| `blender_brutalist_gn` | **Melodia Brutalist Geometry Nodes** v2.0.0, Melodia Studio | 3 — project-owned |
| `blender_kawaii_gn` | **Melodia Kawaii Geometry Nodes** v2.0.40. `"World's most comprehensive Kawaii Geometry Nodes addon"` | 4 — project-owned; the stylistic match to an anime project |
| `fromage_roof_generator` | **🏠 Fromage's Roof Generator** v3.2.0, Surreal Architecture Studio, `blender: (5,1,0)`. `"...20+ styles, Y2K Dome, Dreamy Materials, Heart/Star Accents, Materials, Baking, Shingles, Dormers, Gutters. Game-ready output."` | 3 — project-owned |
| `FromageRoof_v3.1` | Same addon, v3.1 | **DUPLICATE — older** |
| `rust_gpu_sdf_addon` | **SDF.R** v15.9.8.1, hinata_hugu. `"Next-gen SDF Modeling Tool with Professional Workflow"` | 3 |
| `Procedural_Generation_Toolkit` | **Procedural Generation Toolkit** v1.0.0, Jonas Mangelschots. Empty description | 2 — a framework; see `JDLC_Base` |
| `JDLC_Base` | **`__init__.py` is 0 bytes.** **INFERRED FROM CODE**: `GenSpaceshipBase.py`, `GenScifiMaterial.py`, `MeshScramble.py` all `import Procedural_Generation_Toolkit.*` | 1 | A **content pack** for Procedural Generation Toolkit (spaceship/sci-fi generators). Not a standalone addon; with an empty `__init__.py` it registers nothing on its own. Sci-fi content — irrelevant to Melusina. |
| `cloud_generator` | **Cloud Generator** v2.0.0, CGBlender. `"One-click transformation of meshes into realistic clouds"` | 2 |
| `flip_fluids_addon` | **FLIP Fluids** v1.8.1 | 1 |
| `LiquiFeel` | **Liquifeel** v1.2, BlenderMight. `"Fill recipient models with liquid."` | 1 |
| `surreal_os` | see above | — |
| `melodia_icons` | **No `bl_info`, no `.py`** — icon assets only (`README.md` + `melodia_icons/`) | n/a — asset folder, not an addon |
| `modules` | **No `bl_info`** — contains only `_audvis_modules` (1661 files). AudVis's vendored Python dependencies | n/a — support folder |

### Rendering / lookdev

| Addon | What it is | Rel. |
|---|---|---|
| `LightPainter` | **Light Painter** v1.0.9, ShaderError. `"Paint cinematic light with your mouse"` | **4** — fastest path to good character portrait/turnaround lighting |
| `physical-starlight-atmosphere` | **Physical Starlight and Atmosphere - PSA** v1.9.2 | 3 — environment sky/atmosphere |
| `nijigp` | **nijiGPen** v0.13.0. `"A Grease Pencil toolbox for 2D graphic design and illustrations"` | 3 — 2D/GP illustration, not a 3D toon shader |
| `inkform.py` + `inkform_v1.0` | **Inkform** v1.0.0, Kevin Ramirez (Kevandram), `blender: (5,0,0)`. `"Turns Grease Pencil strokes into mesh geometry."` | 3 — GP→mesh; usable for stylized hair/decal shapes. **Two copies installed.** |

### Utility

| Addon | What it is | Rel. |
|---|---|---|
| `N-Panel Orchestrator` v1.2.2 / `N-Panel_Orchestrator` v1.1.6 | **N-Panel Orchestrator**, Sunkanwei. `"Advanced management system for third-party N-Panels with categorization, search, and quick switching"` | **4** — with 75 addons installed, this is genuinely load-bearing. **Two versions installed.** |
| `_HOLD_20260730/ZenDock` | ZenDock UI (held) | 2 |
| `__pycache__` (addons root) | Compiled bytecode for `blender_mcp_addon`, `inkform`, `surreal_architecture_gen` | n/a — confirms those loose files have been executed |
| `.Sanctus-Library_preferences.json` | Sanctus prefs file | n/a |

---

## 2. Flagged by job

### Weight painting quality and automation
Strong on generation, empty on painting UX.

- **`voxel_skinning` — the anchor.** Three separate deliverables in one folder: `voxel_heat_diffuse_skinning.py` (volumetric bind — handles the skirt/sleeve/hair cases where Blender's automatic weights bleed across gaps), `surface_heat_diffuse_skinning.py` (surface-based alternative for watertight body meshes), and `corrective_smooth_baker.py`. The corrective smooth baker is the pipeline-critical piece: UE will not evaluate Blender's Corrective Smooth modifier, so baking it into vertex weights is the only way that deformation quality survives export. `joint_alignment_tool.py` helps get joints centered before binding, which is upstream of weight quality.
- **`MACHIN3tools`** — indirect. Fast mode-switching between Pose and Weight Paint tightens the hand-paint iteration loop.
- **Nothing else.** No weight-gradient, weight-mirror-by-topology, weight-transfer-between-outfits, or delta-mush-to-weights tool. For a hand-painting workflow this is workable (Blender's native weight tools are decent) but see Gaps.

### Facial blendshape / ARKit authoring
**Zero coverage.** `grep -ril "arkit"` across all 77 entries: no matches. No shape-key manager, no shape-key mirror/split tool, no ARKit 52-target generator, no corrective-driver setup tool. The `_HOLD_20260730/rokoko-studio-live-blender-master` package has face-shapekey retarget code but it is (a) held/unloaded, (b) hardware-dependent. This is the biggest gap between the current set and a AAA anime-character pipeline — MetaHuman-grade facial in UE 5.8 wants either ARKit-named blendshapes or a MetaHuman Animator path, and nothing here authors either.

### Blender → UE export fidelity
- **`send2ue` v2.6.7 (Poly Hammer fork)** — the primary bridge. Handles skeletal mesh + shape keys + sockets + collision, with validations for scale/naming that catch most of the classic UE import failures. Keep this one.
- **`Blender-Unreal-Export-Addon` (Tarmunds, v4.0.1, `blender: (4,5,0)`)** — complementary batch FBX exporter with Y-up handling and pre-export joining. Best for shipping many outfit variants in one pass.
- **`collider_tools`** — UCX collision authoring for accessories/props/environment.
- **`remap_presets/unreal_mannequin_remap.bmap`** — direct evidence of an intended Auto-Rig Pro → UE5 Mannequin retarget (`c_foot_ik.r → foot_r`, `c_neck.x → neck_01`, `ik_hand_gun`, full twist-bone chain `upperarm_twist_01_r` / `thigh_twist_01_l`). The presets are here; **the addon that consumes them is not**.
- **`BlenderTools-20231109043947`** — actively harmful, see §4.

### Anime / toon rendering and lookdev
**Essentially uncovered on the shader side.**
- `Sanctus-Library` v3.3.2 is a large material library, but a case-insensitive grep for toon/anime/cel across its Python found no stylized-NPR shader modules — it is a PBR/procedural library.
- `nijigp` and `inkform` are Grease-Pencil tools (2D illustration, GP→mesh). Useful for stylized *geometry* (hair shapes, eyelash cards, effect meshes), not for a cel shader.
- `LightPainter` is the strongest lookdev item present — anime characters live or die on light shaping, and painting key/rim positions directly is the fastest route to a good rim-light read.
- `blender_kawaii_gn` (project-owned) is the only stylistically aligned tool.
- Worth noting: for UE 5.8 the toon shading has to be a UE-side material/post-process anyway. The Blender-side gap is *previewing* what UE will do, which nothing here does.

### Garment / outfit fitting and clipping
- **`wrapper_addon`** — best in set. Its operator list (`Generate Clothes` → `Generate Wrap` → `Add Solidify` / `Add Subd` → `Set Collision` → `Set cloth` → `Bake`) is a complete surface-conform + drape + bake garment loop. The `Set Collision` step is exactly the body-clipping control you want.
- **`Curtain_Maker_Pro_S4c_v6`** — quad-topology + pin controls + cloth. Repurposable for skirts/capes; quad output means it stays riggable.
- **`ctools_braids`** — hair braids via Geometry Nodes with realize + UV conversion, so the output can be baked to game-ready geometry.
- **`fluffy_maker`** — likely fur/fluff trim, but its `bl_info` description is empty; **unverified**.
- **`SwingyBonePhysicsAddon`** — the motion layer on top of fitted garments.

---

## 3. Gaps

Things a AAA anime-character Blender→UE pipeline normally has that are **absent from this set**:

1. **A character rig system.** No Auto-Rig Pro, no Rigify enabled as a workflow, no Mixamo/UE-mannequin rig generator. The `.bmap` presets prove ARP was the plan — **buying/installing Auto-Rig Pro (with its Remap module) is the single highest-value addition**, and it immediately activates the five preset files already sitting on disk. ARP also ships an FBX exporter with UE-specific skeleton handling that outperforms raw FBX.
2. **Facial blendshape / ARKit tooling.** Nothing. Options: Faceit (ARKit 52-target generation + validation), or a shape-key manager for hand-authored targets. Without this, facial work is entirely manual shape-key sculpting with no naming validation — and UE 5.8 will silently accept mis-named curves.
3. **Shape-key utilities in general.** No mirror-shapekey-by-topology, no split-left/right, no shape-key driver setup, no corrective-shape-on-bone-rotation tool. These are day-one needs for a character.
4. **Weight-transfer / weight-editing UX.** No tool to transfer weights from body → each new outfit piece with proper falloff, which is the highest-frequency operation in a character-with-many-outfits project.
5. **A toon/NPR shader kit** for previewing the UE look in Blender (outline, ramp shading, matcap-driven face shadow). Anime faces in particular need face-shadow control (the "SDF face shadow map" technique) — nothing here authors that.
6. **Hair card tooling.** `ctools_braids` makes braids, but there's no hair-card generator/UV-atlas tool (curve→card, card unwrap to an atlas strip). For a UE-bound anime character, hair cards or stylized hair geometry are mandatory (UE Groom is expensive for stylized).
7. **LOD generation.** Nothing generates LODs Blender-side; you'd rely on UE's auto-LOD, which is acceptable but not AAA-controlled for a hero character.
8. **A mesh/skeleton validator for UE.** `send2ue` has some validations but there's no independent checker for non-manifold, ngons on deforming areas, >8 influences per vertex (UE's practical limit), or scale/unit drift.
9. **Texture-set/channel-packing tool** for UE's ORM (Occlusion/Roughness/Metallic) convention. `SimpleBake` can bake channels but packing to UE's expected layout is manual.

---

## 4. Redundant, conflicting, and broken

**Act on these before doing anything else — several are correctness issues, not tidiness.**

| Issue | Detail | Recommendation |
|---|---|---|
| **`send2ue` installed twice** | `send2ue/` (v2.6.7, Poly Hammer fork) and `BlenderTools-20231109043947/send2ue/` (v2.4.3, Epic original). **Same Python module name.** Two registrations of the same operators/panels — nondeterministic which wins, and a classic source of "Send to Unreal silently does the wrong thing." | **Remove `BlenderTools-20231109043947`.** Keep `send2ue` 2.6.7. |
| **Blender MCP daemon, twice, loose at addons root** | `blender_mcp_addon.py` and `addon.py` are both **Blender MCP v1.2**, both open a socket on **port 9876**, both define `blendermcp_auto_start_server`. `__pycache__/blender_mcp_addon.cpython-313.pyc` confirms it has run. | The 2026-07-30 manifest quarantined this exact pattern (auto-starting daemon on 9876/9877 causing a 1-second UI hitch). **Delete one copy, and confirm `blendermcp_auto_start_server` is off.** |
| **Quarantined Melodia loose files are back** | The manifest states `surreal_architecture_gen.py`, `surreal_arch/`, `surreal_greybox/`, `surreal_os/`, `surreal_world/` were quarantined and should be *"reinstalled properly as one isolated addon folder if/when wanted back, not loose files."* They are currently loose at addons root again, and `__pycache__/surreal_architecture_gen.cpython-313.pyc` shows they've executed. | Not a safety issue by itself, but it is the exact regression the manifest was written to prevent. **Repackage as one addon folder** (the four `surreal_*` folders have no `bl_info` — they are libraries for `surreal_architecture_gen.py`). |
| **4 bake addons** | `SimpleBake` (2.3.2, `blender: 4.5.2`), `Sanctus-Bake` (4.2), `auto_bake` (3.3), `Blender-BakeLab2-master` (2.81) | **Strongest: `SimpleBake`** — most current by a wide margin. Keep `Sanctus-Bake` only as the Sanctus-Library companion. **Remove `Blender-BakeLab2-master` and `auto_bake`.** |
| **3 UV addons** | `ZenUV` (5.0.3.0), `UvSquares` (1.15), `quad_unwrap` (2.80-era) | **Strongest: `ZenUV`.** `UvSquares` coexists fine. **Remove `quad_unwrap-master`.** |
| **N-Panel Orchestrator twice** | `N-Panel Orchestrator` v1.2.2 and `N-Panel_Orchestrator` v1.1.6 | Keep **v1.2.2**, remove the underscore copy. |
| **Inkform twice** | `inkform.py` (loose) and `inkform_v1.0/inkform.py` | Keep the folder version, remove the loose file. |
| **Fromage Roof twice** | `fromage_roof_generator` v3.2.0 (`blender: 5,1,0`) and `FromageRoof_v3.1` | Keep **v3.2.0**. |
| **Zen UV twice** | live `ZenUV` v5.0.3.0 + `_HOLD_20260730/Zеn UV v5.0.3.0 vfxMed` — note the held folder name contains a **Cyrillic `е`** in "Zеn", a repack marker | Keep the live one. |
| **`Combine V2` is broken** | Nested one level too deep: `Combine V2/Combine V2/__init__.py`. Blender won't register it. | Move the inner folder up, or remove. |
| **`JDLC_Base` registers nothing** | `__init__.py` is **0 bytes**; its modules import `Procedural_Generation_Toolkit.*` | It's a sci-fi content pack for PGT, irrelevant to Melusina. **Remove.** |
| **Two jiggle/secondary-motion tools** | `SwingyBonePhysicsAddon` v1.9.0 (general bone-chain solver, documented) vs `Jiggle_Maker` v1.4 (hardcoded proxy FBXs, fixed face indices, no description) | **Strongest: `SwingyBonePhysicsAddon`.** |
| **Version-target risk on Blender 5.2** | Many addons declare old minimums: `voxel_skinning` (2.80), `quad_remesher` (2.80), `UvSquares` (2.80), `Blender-BakeLab2` (2.81), `AE2Blend` (2.70), `Bligify` (2.80), `SwingyBone` (3.0), `wrapper_addon` (3.0), `ctools_braids` (3.0.3). Only `surreal_architecture_gen.py` targets 5.2. | `bl_info["blender"]` is a *minimum*, not a guarantee — but `voxel_skinning` and `quad_remesher` are load-bearing for this project and both ship compiled binaries/bridges. **Verify these two actually register on 5.2 before planning around them.** |
| **`melodia_icons` / `modules` are not addons** | `melodia_icons` = icon assets + README only. `modules` = AudVis's vendored dependencies | Leave alone; don't expect them in the addon list. |

**Cross-reference with `Tools/BlenderAddons/`:** that folder holds 8 project-owned addons (`blender_brutalist_gn`, `blender_kawaii_gn`, `fromage_roof_generator`, `FromageRoof_v3.1`, `GenesisCore`, `melodia_icons`, `Procedural_Generation_Toolkit`, `rust_gpu_sdf_addon`) — all 8 are **still duplicated** in the live addons folder. The manifest's stated plan (add `Tools\BlenderAddons\` as a Script Directory, then delete the AppData copies) has **not been completed**. Note `GenesisCore` v0.0.1 declares `"category": "AI"` with a Chinese-language author string (幻之境开发小组) and no description — the manifest calls it a project support library, but its `bl_info` doesn't corroborate that; **treat its identification as unconfirmed.**

---

## 5. Recommended working set for Melusina

Everything below is installed **unless marked ADD**.

| Job | Use | Why |
|---|---|---|
| **Base skin weights** | `voxel_skinning` → Voxel Heat Diffuse | Correct bind through gaps (skirt/sleeve/hair) where automatic weights fail |
| **Weight cleanup before export** | `voxel_skinning` → Corrective Smooth Baker | Bakes smoothing into real weights; UE can't evaluate the modifier |
| **Joint placement** | `voxel_skinning` → Joint Alignment Tool | Upstream of weight quality |
| **Hand weight painting** | Blender native + `MACHIN3tools` for fast Pose↔Weight-Paint switching | No dedicated weight-paint addon exists in this set |
| **Character rig** | **ADD: Auto-Rig Pro (+ Remap)** | `remap_presets/*.bmap` is already ARP-format and already maps to the UE5 Mannequin |
| **UE retarget** | `remap_presets/unreal_mannequin_remap.bmap` — once ARP is installed | Full twist-bone + IK mapping already authored |
| **Facial blendshapes** | **ADD: Faceit** (or equivalent ARKit generator) | Nothing in the set does this — zero ARKit hits |
| **Garment fitting / anti-clipping** | `wrapper_addon` (Generate Wrap → Set Collision → Set cloth → Bake) | Only complete conform+drape+bake loop present |
| **Skirts / capes / drapery** | `Curtain_Maker_Pro_S4c_v6` | Quad topology + pin controls = riggable output |
| **Braided hair** | `ctools_braids` | GN braids with realize + UV conversion |
| **Hair/skirt secondary motion** | `SwingyBonePhysicsAddon` | Documented, general-purpose; drop `Jiggle_Maker` |
| **Retopo** | `quad_remesher` | Verify 5.2 compatibility first |
| **UV** | `ZenUV`, with `UvSquares` for hair-card grids | Texel density control matters for UE consistency |
| **Baking** | `SimpleBake` | Newest and strongest of the four |
| **Texture painting** | `deep_paint_pro_v1.2.7` | Layered paint workflow |
| **Mesh hygiene pre-export** | `Mesh Cleaner Pro v0.1.3` | Targets Blender 4.5, actively maintained-looking |
| **UE export (live)** | `send2ue` v2.6.7 — **after removing `BlenderTools-20231109043947`** | Poly Hammer fork is the maintained one |
| **UE export (batch/variants)** | `Blender-Unreal-Export-Addon` (Tarmunds) | Per-object files, Y-up, pre-join |
| **Collision for props/accessories** | `collider_tools` | UCX conventions |
| **Character lookdev** | `LightPainter` | Rim/key shaping by hand |
| **Toon shading** | **ADD: an NPR/toon kit**, or accept that toon shading is UE-side only | Nothing here previews the UE look |
| **Blockout / concept-driven modeling** | `projection_modeling` + `speedsculpt` | Front/side reference projection is a natural fit for anime character construction |
| **Environment art** | `surreal_architecture_gen.py` + `surreal_*` libs, `blender_kawaii_gn`, `archipack_20`, `physical-starlight-atmosphere`, `poliigon-addon-blender` | Project-owned tools target 5.1/5.2 — the most current things installed |
| **Asset organization** | `assets_library_builder` + `N-Panel Orchestrator` v1.2.2 | With ~75 addons the N-panel is unusable without the orchestrator |

**Disable for this project** (noise, no Melusina relevance): `AE2BLEND_1_3_1`, `Advanced-Cones-master`, `coiled_spring`, `Bligify-master`, `VSEQF-master`, `audvis` (+ `modules`), `flip_fluids_addon`, `LiquiFeel`, `ocd_2`, `JDLC_Base`, `cloud_generator`, `Blender-BakeLab2-master`, `auto_bake`, `quad_unwrap-master`.

---

## 6. Honest unknowns

Stated rather than invented:

- **`fluffy_maker`** — `bl_info` description is empty. Serpens-generated. Name and author suggest procedural fluff/fur; not verified.
- **`Combine V2`** — no description, and the nesting bug means it isn't even registering. Purpose unknown.
- **`GenesisCore`** — `bl_info` gives only `category: "AI"` and a Chinese-language author. The 2026-07-30 manifest asserts it's a support library for the Melodia GN tools; the `bl_info` does not confirm this.
- **`wrapper_addon`, `ctools_braids`, `Handy Curve Profile`, `Procedural_Generation_Toolkit`** — all have empty `description` fields. Their purposes above are **inferred from operator labels and node names in the source**, and are flagged as such in the table.
- **`Sanctus-Library`** — 2469 files; the toon/anime/cel grep was over `.py` only. Material content is stored in `.blend` assets that were not opened, so a stylized shader could exist there without showing in the code search.
- **Blender 5.2 runtime compatibility was not tested** for any addon — only declared `bl_info["blender"]` minimums were read. `voxel_skinning` and `quad_remesher` are the two load-bearing ones with old targets and native/bridge components; both need an in-app check.

---

# CORRECTION — 2026-08-15, appended after the original sweep

**The inventory above is materially incomplete.** It scanned only
`AppData/Roaming/Blender Foundation/Blender/5.2/scripts/addons` and missed
`.../5.2/extensions/user_default` entirely — **37 further packages**, including the two
the original report explicitly declared absent.

That error had consequences: it produced a "no character rig system" finding and a
"facial/ARKit: literally zero" finding, both of which are false, and it led to an export
being run without ARP that failed its promotion gate.

## The two the report got backwards

| Package | Version | Reality |
|---|---|---|
| **Auto-Rig Pro** | 3.77.25 | **Installed.** `extensions/user_default/auto_rig_pro`. Enables headless as `bl_ext.user_default.auto_rig_pro`; `bpy.ops.arp.arp_export_fbx_panel` confirmed live. This is the rig Melusina was built with — the earlier "ARP was clearly the plan; installing it is the highest-value single addition" conclusion was wrong on its face. |
| **Faceit** | 2.3.56 | **Installed.** `extensions/user_default/faceit`. "Facial Expressions And Performance Capture". The stage's leftover `FaceitControlRig` object is from this, and its ARKit retarget/bake tooling is available — which changes the shape-key recommendation entirely. |

## Full extensions inventory (37)

| Extension | Version | What it is |
|---|---|---|
| `auto_rig_pro` | 3.77.25 | Rig generation from reference bones + game-engine export |
| `faceit` | 2.3.56 | Facial expressions and performance capture (ARKit) |
| `live_link_unreal` | 3.3.1 | Real-time Blender → Unreal sync |
| `blender_to_unreal` | 2.2.2 | Meshes, animations, collisions, sockets, LODs → UE |
| `blender_org_vrm_addon` | 4.4.0 | VRM import/export/editing |
| `amp_rig_ui` | 2.24.1224 | AniMatePro — character rig UIs |
| `proxy_picker` | 1.1.10 | Rig proxy picker |
| `gui_slider` | 1.1.0 | Armature sliders driving shape keys / custom props |
| `simply_cloth_studio` | 1.5.2 | Cloth creation and simulation |
| `woolly` | 2.0.1 | Woolly hair / fabric systems |
| `stylized_hair_pro` | 4.1.6 | Stylized hair from curves |
| `uvpackmaster3` | 3.4.4 | UV packing engine |
| `qremeshify` | 1.1.0 | Quad remesher |
| `tris_to_quads_ex` | 1.3.0 | Optimized tris→quads conversion |
| `instantclean` | 2.2.4 | Mesh cleanup |
| `quick_baker` | 2.4.0 | PBR texture baker |
| `deep_paint` | 2.3.1 | Texture paint workflow |
| `truedepth` | 1.5.4 | Depth map generation |
| `antitile` | 1.7.1 | Removes texture tiling artifacts |
| `gob` | 4.1.7 | ZBrush ↔ Blender bridge |
| `motion_presets_for_blender` | 1.0.0 | Animation presets |
| `simplify_plus` | 1.1.0 | Viewport/playback performance |
| `CleanPanels` | 7.0.18 | Panel and workspace manager |
| `BoxCutter` | 7.20.8 | Hard-surface cutting |
| `ocd_extension` | 2.5.0 | One Click Damage |
| `rockform` | 1.4.1 | Procedural rock formations — **see hazard below** |
| `GeoCables` | 2.3.1 | GN cable generator |
| `hifi_builder` | 3.8.0 | Architecture builder |
| `trowel_core` / `trowel_ui` | 2.2.0 / 1.3.0 | Brick wall generator |
| `ornament_generator` | 1.0.1 | Ornament generation |
| `handy_curve_profile` | 1.5.0 | Curve shape assistant |
| `fadeassets` | 1.4.3 | Toon nature assets |
| `ParticleLink` | 4.2.0 | Particle linking |
| `audvis` | 6.0.0 | Audio/MIDI visualization |
| `synthia` | 1.0.0 | Mathematical visualization |

## Operational hazard: `rockform`

`rockform` registers depsgraph handlers that raise on **every** update when its expected
modifier is absent:

```
KeyError: 'bpy_prop_collection[key]: key "RF Shape Formation" not found'
  in depsgraph_update_pre_handler / depsgraph_update_post_handler / load_post_handler
```

Any script that manipulates objects triggers this continuously. It killed two headless
export runs outright. It also inflates load time badly: the v22 stage loads in **1:06**
with addons enabled and **12.9 seconds** under `--factory-startup`.

**Rule for all headless work on this project:** run `--factory-startup` and enable only
what the job needs, e.g.

```
blender --background --factory-startup <stage>.blend \
  --python <enable_arp.py> --python <job.py> -- <args>
```

where the pre-script does `bpy.ops.preferences.addon_enable(module="bl_ext.user_default.auto_rig_pro")`.

## Corrected working set for Melusina

| Job | Use | Note |
|---|---|---|
| Rig + game export | **auto_rig_pro** | The export gate only accepts `bpy.ops.arp.arp_export_fbx_panel+bpy.ops.export_scene.fbx(contract_finalize)` |
| Facial / ARKit | **faceit** | Can retarget the 46 FACS keys onto the 52 empty ARKit names instead of sculpting them |
| Weight painting | **voxel_skinning** (Corrective Smooth Baker) | Base pass already applied: all meshes limited to 4 influences, normalized |
| Garment fitting / clipping | **wrapper_addon**, **simply_cloth_studio** | Anti-clipping for swappable outfits |
| Hair | **stylized_hair_pro**, **woolly** | |
| UE transfer | **blender_to_unreal**, **live_link_unreal** | Distinct from the contract export route, which is hand-rolled |
| UV | **uvpackmaster3** | Supersedes the ZenUV recommendation above |

## Remaining gaps (revised)

Genuinely absent, after accounting for extensions: hair-card tooling, ORM channel
packing, automated LOD generation, and a toon/NPR shader kit. The "no rig system" and
"no ARKit tooling" gaps claimed above are **withdrawn**.
