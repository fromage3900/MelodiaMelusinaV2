# Scene: SakuraPath — cute dreamy cherry-blossom garden

First portfolio **vertical slice**. UE 5.8 · Substrate Toon · `M_Master_Toon_Universal`.

## Concept
A cozy storybook Japanese garden path under blooming sakura at soft dusk — Infinity-Nikki
dreaminess: pastel pink/cream, gentle glow, drifting petals that catch the light.

## Mood / palette
- Soft warm **dusk**: pink-gold key light, lavender-blue ambient.
- Pastel pink blossom · cream stone · moss green · muted vermilion torii · warm lantern glow.
- Dreamy **bloom**, light volumetric fog for depth, gentle **petal shimmer** (Nikki sparkle).

## Composition (hero shot)
- **Foreground:** mossy stepping-stone path leading the eye in.
- **Midground:** arched canopy of 2–3 sakura trees framing the path.
- **Focal point:** a small red **torii gate** (or stone lantern) in a soft-lit clearing.
- **Background:** more blossom canopy fading into pastel fog; a hint of koi pond + arched bridge to one side.

## Asset kit (CC0 / Fab-Megascans / Blender)
| Asset | Source plan |
|---|---|
| Sakura tree (trunk + blossom canopy) | Sketchfab CC0 / Blender (sapling + blossom cards) |
| Blossom petals (scatter cards) | Blender / CC0 alpha (`T_Spark`/petal mask) |
| Torii gate | Sketchfab CC0 |
| Stone lantern (tōrō) | Sketchfab CC0 / Megascans |
| Stepping stones / rocks | Megascans (CC0 via Fab) |
| Wooden arched bridge | Sketchfab CC0 |
| Koi pond (water plane) | `MI_GrandWater_SakuraPond` on `M_Water_Master_Grand_v6` (`MI_Sakura_Water` = Universal fallback only) |
| Grass / moss / small flowers | Megascans / PCG scatter |

## Materials (all MI on `M_Master_Toon_Universal`)
| Instance | Setup |
|---|---|
| `MI_Sakura_Blossom` | pink albedo, high `PastelLift`, pink `RimColor`, `SparkleIntensity` (petal shimmer), low `GlowIntensity` |
| `MI_Sakura_Bark` | bark texture, low `TextureWeight` stylization |
| `MI_Sakura_StonePath` | stone tex, triplanar, moss in cavities (curvature) |
| `MI_Sakura_Moss` | soft green |
| `MI_GrandWater_SakuraPond` | grand water — caustics, gentle Gerstner, Nikki `MagicalIntensity` (see `setup_sakura_scene.py`) |
| `MI_Sakura_Water` | Universal glass fallback for props — not the koi pond plane |
| `MI_Sakura_ToriiRed` | muted vermilion lacquer, slight gloss |
| `MI_Sakura_Lantern` | weathered stone + warm emissive glow |
| `MI_Sakura_Grass` | two-sided, soft green, gentle wind |

## Lighting
- Directional sun: low dusk angle, warm pink-gold, soft Lumen shadows.
- SkyAtmosphere + pastel-gradient sky / dusk HDRI.
- Exponential height fog (subtle) + volumetric god-rays through canopy.
- Warm point lights inside lanterns (MegaLights).
- PostProcess: manual exposure, AgX, **Bloom up** (the Nikki glow), gentle vignette.

## PCG scatter (phased — see professional review)

**Phase 1 (implemented):** one stock graph — `PCG_Sakura_GroundCover` under `/Game/EnvSandbox/PCG/Sakura/`.

| Graph | Status | Notes |
|-------|--------|-------|
| `PCG_Sakura_GroundCover` | ✅ Phase 1 | VolumeSampler → Transform → StaticMeshSpawner; greybox grass proxy |
| `PCG_Sakura_FallenPetals` | ⏳ Phase 2 | Defer until ground cover validates; avoid overlap with `NS_SakuraGroundPetals` |
| `PCG_Sakura_PathFlowers` | ⏳ Phase 3 | Spline/corridor scatter — highest risk |

- **Build:** `py Content/Python/setup_pcg_sakura.py` (also in `run_editor_session.py`, optional step)
- **Audit:** `Saved/Audit/sakura_pcg_build.json` — expected ISM band 400–2500 on `PCG_Sakura_GroundCover`
- **Swap workflow:** replace grass proxy in `pcg_sakura_standards.py` → `SCATTER_MESHES["grass"]` when CC0 kit lands
- **Exclusion guides:** invisible `PCG_Exclude_*` box actors (path, pond, torii) — wire into graph in Phase 2

Legacy note: fallen petals on path + grass were originally one bullet; Niagara handles drift/shimmer, PCG handles static ground cover first.

## Shots (Movie Render Graph)
1. **Hero:** low path-to-torii, canopy framing — 2560×1440.
2. **Detail:** petals on a mossy stepping stone, shallow DOF.
3. **Detail:** lantern glow at dusk.
4. **Flythrough:** slow push down the path — 1080p/4K.

## Build order (the prep — what the loop is doing)
1. Source the kit assets (trees, torii, lantern, rocks, bridge) — CC0, license-checked.
2. Build the `MI_Sakura_*` set on the universal master.
3. Greybox layout (path + tree positions + focal point) in `L_SakuraPath` from `_Template`.
4. Replace greybox with kit assets; PCG-scatter petals + grass.
5. Light + post (dusk + bloom).
6. Render hero shots.

## Nanite + Niagara plan
- **Nanite:** enable on the imported high-poly kit (rocks, lantern, torii, tree trunks) — no manual LODs under Lumen. Blossom canopy → Nanite if dense geo, else masked alpha cards.
- **Niagara (Sakura Dream kit — `/Game/EnvSandbox/VFX/Systems/Sakura/`):**

| System | Role | Sprite material |
|--------|------|-----------------|
| `NS_SakuraPetals` | Continuous canopy petal drift | `MI_Niagara_Petal` |
| `NS_SakuraGroundPetals` | Fallen petals on path / moss | `MI_Niagara_Petal` |
| `NS_SakuraDreamSparkle` | Nikki air shimmer under canopy | `MI_Niagara_Sparkle` (JRO zen07 + T_Spark_*) |
| `NS_SakuraLanternMotes` | Warm motes at stone lantern | `MI_Niagara_Mote` (JRO zen03 + bokeh) |
| `NS_SakuraPondShimmer` | Sparkle sheet over koi pond | `MI_Niagara_Pond` (JRO zen35/zen30 sand/stone) |
| `NS_SakuraPetalGust` | One-shot wind gust burst | `MI_Niagara_Gust` (petal + JRO zen23 bamboo) |

- **MPC:** `MPC_SakuraDream` — `WindStrength`, `GustTrigger`, `SparklePulse`, `PetalDensity` (wired into `M_Niagara_SakuraSprite` emissive/opacity)
- **Build:** `py Content/Python/run_sakura_niagara_plan.py` (full prerequisites + kit + spawn + validate)
- **MCP:** UnrealMCP **55557** when editor is open; Monolith **9316** unavailable until plugin is rebuilt (see `Docs/MATERIAL_INTEGRATION.md`)
- **Kit only:** `py Content/Python/setup_sakura_niagara.py` (`--rebuild` deletes all six systems and recreates via MCP or portfolio seeds)
- **Validate:** `py Content/Python/validate_sakura_niagara.py` → `Saved/Audit/sakura_niagara_validation.json`
- **Showcase:** `py Content/Python/run_sakura_niagara_plan.py --showcase` → `L_VFX_SakuraShowcase`
- **Magical burst (henshin):** `NS_MagicalHenshinBurst` — separate from sakura kit; sync via `MPC_Magical`
- **PCG:** fallen petals (density falloff near trunks) + grass / tiny flowers on the ground.

## Prep progress (autonomous loop)
- ✅ Master ① macro/detail + ② magical-girl — **code-ready, one rebuild pending** (`py setup_master_universal.py`, full path)
- ✅ Materials — `setup_sakura_instances.py` (8 `MI_Sakura_*`)
- ✅ Scene — `setup_sakura_scene.py` (`L_SakuraPath`: dusk rig + toon/bloom post + greybox torii/path/trunks + CineCamera)
- ✅ Motif alphas — `_AssetLibrary/Magical/` (heart/star/ribbon)
- ⏳ CC0 kit assets (tree/torii/lantern/rocks/bridge) — sourcing pending (license-checked)
- ✅ Niagara Sakura Dream kit — scripts + level spawns (`run_sakura_niagara_plan.py`); hand-tune emitters in Niagara Editor after scaffold
- ⏳ PCG scatter graphs — Phase 1 ground cover via `setup_pcg_sakura.py`; petals/path deferred
- ⏸️ Master ③ MF-refactor — deferred until rebuild verified

**Run order when live:** `setup_master_universal.py` → `setup_sakura_instances.py` → `setup_sakura_scene.py` → import CC0 kit → swap greybox → PCG/Niagara → light + render.

---
*Prepared autonomously by the sakura loop (job 7c4186f8). Status updated each iteration.*
