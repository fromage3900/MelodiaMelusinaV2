# VFX Niagara full inventory — 2026-09-17

**Type:** documentary census (git + docs + scripts). Not a live Monolith graph read.
**Home:** [`Docs/VFX/`](README.md) — same folder as the 2026-09-14 Melodia Niagara spec
and Choral Sheep VFX work order. Chosen because that is the existing Melodia VFX
audit convention; `Saved/Audit/` holds JSON receipts, not durable inventories;
`Docs/Production/Materials/` is material-architecture, not Niagara systems.
**Machine table:** [`VFX_NIAGARA_INVENTORY_2026-09-17.csv`](VFX_NIAGARA_INVENTORY_2026-09-17.csv)
**Graph:** [`VFX_NIAGARA_GRAPH_2026-09-17.md`](VFX_NIAGARA_GRAPH_2026-09-17.md)
**Fix A:** [`VFX_FIXA_RISKS_2026-09-17.md`](VFX_FIXA_RISKS_2026-09-17.md)

## 1. Method and limits

Inspected:

- `git ls-files` for every tracked `NS_*`, `M_Niagara_*`, `MI_Niagara_*`, sheep VFX, `_PROJECT/VFX`
- Disk `find` under `Content/{Melodia,EnvSandbox,_PROJECT}/**/{VFX,Niagara,Particles}`
- Prior docs: `Docs/VFX_ASSET_MANIFEST.md`, `Docs/VFX/MELODIA_NIAGARA_ECOSYSTEM_SPEC_2026-09-14.md`,
  `Docs/NIAGARA_ECOSYSTEM_2026-08-09.md`, `Docs/Handoffs/CODEX_NIAGARA_LIBRARY_AUDIT_2026-08-01.md`,
  `Saved/Audit/vfx_stub_audit_2026-08-30.json`, `Saved/Audit/BATCH_B_SHEEP_2026-09-12.md`,
  `Docs/Evidence/BRANCH_LEDGER_2026-09-13.json`
- Binding scripts: `Content/Python/{setup_sakura_niagara,finalize_niagara_mcp,fix_zenforest_niagara_renderer_materials,live_niagara_audit,setup_niagara_library}.py`,
  `Tools/{fix_niagara_render_faults,author_endless_loops,build_melusina_anim_vfx}.py`

Not inspectable here:

- Niagara graph pins (`SubUVAnimation`, `SubImageSize`, `FlipFPS`) — tracked `.uasset` files
  are Git LFS **pointers** (~130 B). `strings` on them yields nothing.
- `Content/Melodia/VFX/NS_*.uasset` and `Content/EnvSandbox/VFX/Systems/**` — **gitignored**.
  They exist on the owner PC (ledger + 2026-08-15 manifest) and are absent from this clone.
- Live Asset Registry parent of each MI.

`fix_a_status` uses only in-repo text: **CLEAN / RISK / N_A / UNKNOWN / FIXED**.
**FIXED is unused** — no receipt after Batch B records SubUV off. Every system that
needs an editor confirm is tagged `LIVE_MONOLITH_PENDING` in CSV notes.

## 2. Summary counts

| Slice | Count | Notes |
|---|---:|---|
| CSV rows (this pass) | **109** | 11 master + 32 MI + 57 NS + 4 alias + 5 flipbook texture |
| Niagara systems **git-tracked** in this clone | **8** | 2 sheep + 1 Sea Above prototype + 1 water v10 + 4 candidates |
| Niagara systems **documented, gitignored** | **49** | EnvSandbox Systems + Melodia/VFX; presence on owner disk, not here |
| VFX masters **git-tracked** | **11** | flipbook + Sakura sprite + petal-loop family + 2 legacy |
| VFX MIs **git-tracked** | **32** | 14 `_PROJECT` flipbook/static + 16 EnvSandbox sprite + 2 sheep |
| Flipbook textures **git-tracked** | **5** scored; **58** total under `Content/_PROJECT/VFX/Textures/` | PR #215 LFS-closed the `_PROJECT/VFX` tree |
| `fix_a_status` RISK | **3** | BeatBurst, BeatStar MI, LeafPileLoop |
| `fix_a_status` CLEAN | **3** | WoolMotes, WoolMote MI, ConstellationDraw (owner + Batch B / claim) |
| `fix_a_status` UNKNOWN | **72** | includes all gitignored Melodia flipbook consumers |
| `fix_a_status` N_A | **31** | ribbons, mesh loops, SDF prototypes, textures, masters |
| `fix_a_status` FIXED | **0** | no post-Batch-B SubUV-off receipt |
| Unresolved owner aliases | **4** | HybridSparkles, PetalCascade, MotionTrails, FluidSplash |
| Ecosystem spec “11 instances / 17 Melodia NS” | **mismatch** | disk has **14** `_PROJECT` MIs on/near the flipbook master; Melodia `NS_*` names in docs exceed 17 when sheep are included |

Third-party (ArtOfShader glitch NS, Greybox waterfalls, JRPG `M_Fire_SubUV`, UDS
`Basic_SubUV_Animation`) are **out of ecosystem scope** and are not in the CSV.

## 3. Git-tracked Niagara systems (this clone)

| Path | Documented material | Fix A |
|---|---|---|
| `Content/Melodia/Companions/ChoralSheep/VFX/NS_ChoralSheep_BeatBurst.uasset` | `MI_NS_ChoralSheep_BeatStar` | **RISK** — Batch B enabled Niagara SubUV 4×2; owner says Fix A later |
| `Content/Melodia/Companions/ChoralSheep/VFX/NS_ChoralSheep_WoolMotes.uasset` | `MI_NS_ChoralSheep_WoolMote` | **CLEAN** — Batch B 1×1 single-frame |
| `Content/EnvSandbox/Monoliths/SeaAbove/Prototype/VFX/NS_SeaAbove_UpwardDroplets_Prototype.uasset` | unknown | UNKNOWN |
| `Content/EnvSandbox/Water/v10/NS_MelodiaWaterContact.uasset` | unknown | UNKNOWN |
| `Content/EnvSandbox/VFX/Candidates/Melodia/NS_Melodia_BattleBackdropPulse.uasset` | likely `MI_Niagara_Cosmic` | UNKNOWN |
| `.../Candidates/AdvancedReplacements/NS_ConstellationDraw_AdvancedCandidate.uasset` | unknown | UNKNOWN |
| `.../NS_ConstellationTwinkle_AdvancedCandidate.uasset` | unknown | UNKNOWN |
| `.../NS_SakuraLanternMotes_AdvancedCandidate.uasset` | unknown | UNKNOWN |

Also tracked, not systems: `ET_Melodia_CharacterFX`, `ENV_StorybookAmbientVFX`,
`MF_MelodiaPetalLifecycle`, `MF_Niagara_SDF_Sample`.

## 4. Material families (tracked)

### 4.1 Flipbook master — `/Game/_PROJECT/VFX/Materials/M_Niagara_MelodiaFlipbook`

Spec (2026-08-15 / 2026-09-14): `FlipFPS=15`, `GridCols/Rows=4`, param `FlipbookTexture`.
**This master is the material-side clock in Fix A.**

| Instance | Documented sheet / role | Documented NS |
|---|---|---|
| `MI_Niagara_MelodiaFlipbook_Water` | `T_Alpha_water_globule_flipbook` 4×4 | `NS_Melusina_Globules` |
| `MI_Niagara_Melodia_SplashFlip` | `T_Alpha_fluid_metaball_flipbook` 4×4 | `NS_Melusina_Splash` |
| `MI_Niagara_Melodia_Static_Arc` | static / quantum palette | `NS_Melusina_Arc` |
| `MI_Niagara_Melodia_Static_Chaos` | static | `NS_Melusina_ChaosDrift` |
| `MI_Niagara_Melodia_Static_DropletRing` | static | **orphan MI** |
| `MI_Niagara_Melodia_Static_Dust` | static | `NS_Melusina_Dust`, `EntropyDust` |
| `MI_Niagara_Melodia_Static_Glint` | static | `NS_Melusina_Glint` (WoolMotes donor) |
| `MI_Niagara_Melodia_Static_GlobuleCluster` | static | Globules (unverified which MI wins) |
| `MI_Niagara_Melodia_Static_Provider` | static | `NS_Melusina_ProviderSigil` |
| `MI_Niagara_Melodia_Static_Ripple` | static | `NS_Melusina_Ripple` |
| `MI_Niagara_Melodia_Static_Sigil` | static | `NS_Melusina_Sigil` |
| `MI_Niagara_Melodia_Static_SplashBurst` | static | Splash (unverified which MI wins) |
| `MI_Niagara_Melodia_Static_StarGold` | **no texture override** (spec) | **orphan MI** |
| `MI_Niagara_Melodia_Static_StateB` | parent **unverified** (flipbook vs Cosmic) | `NS_Melusina_Superposition` |

Registered flipbook **system** consumers (manifest, gitignored): `NS_Melodia_ClickSparkle`,
`NS_Melusina_EyeSparkle`, `NS_Melusina_Globules`, `NS_Melusina_Splash`. U1 polish pack
also names `NS_Melusina_Ripple`.

Spec said **11 instances**; git tracks **14** MIs next to the master. Treat “11” as stale.

### 4.2 Sakura sprite master — `M_Niagara_SakuraSprite`

Parent of `MI_Niagara_{Petal,Sparkle,Mote,Pond,Gust,NebulaPetal,Cosmic,AuroraRibbon,LanternGlow}`
per `repair_zenforest_niagara.py` / `setup_sakura_niagara.py`. `MI_Niagara_Petal_Instance`
and `MI_Niagara_Gust_Instance` are children of Petal/Gust. Role-tint motes
(`MI_Niagara_Mote_*`) differentiate the five systems that once shared one emitter GUID.

### 4.3 Petal loop masters (promoted 2026-08-15)

`M_Niagara_PetalMesh_Loop` → `NS_Melodia_PetalEndlessLoop` (mesh, Fix A N_A).
`M_Niagara_PetalSprite_Loop`, `M_Niagara_PetalPile`, `M_Niagara_SDF_Loop` have
**no committed NS row** in this clone (sprite-loop / pile / SDF wrapper orphans
until editor confirm).

### 4.4 Sheep

| MI | NS | Notes |
|---|---|---|
| `MI_NS_ChoralSheep_BeatStar` | `NS_ChoralSheep_BeatBurst` | Flipbook MI. Parent **not** readable from LFS pointer. |
| `MI_NS_ChoralSheep_WoolMote` | `NS_ChoralSheep_WoolMotes` | Diamond-glint / pearl-lilac intent (work order). |

## 5. Documented gitignored Niagara systems

Paths below are **ledger/script/manifest**, discarded if the owner PC no longer
holds them. `CURRENT_STATE.md` (2026-09-13) records deletion of a duplicate
`NS_MagicTrail` + 11 mirrored flipbook materials — the root
`Content/EnvSandbox/VFX/Systems/NS_MagicTrail.uasset` row may already be gone.

### EnvSandbox Systems (from `live_niagara_audit.py` + BRANCH_LEDGER + manifest)

Ambient: `NS_ConstellationTwinkle`, `NS_EmberMotes`, `NS_FairyDust`.
Magical: `NS_MagicTrail`, `NS_MagicalHenshinBurst`.
Sakura: `NS_ConstellationDraw`, `NS_CosmicPetalOrbit`, `NS_SakuraCosmicAurora`,
`NS_SakuraDreamSparkle`, `NS_SakuraGroundPetals`, `NS_SakuraLanternMotes`,
`NS_SakuraPetalGust`, `NS_SakuraPetals` (redirector?), `NS_SakuraPetals_v2`,
`NS_SakuraPondShimmer`, `NS_SakuraWaterPetals`, `NS_WindRibbonGust`,
six `NS_SDF_*`, `NS_Melodia_PetalEndlessLoop`, `NS_Melodia_LeafPileLoop`.
Universal: `NS_Uni_{DustShafts,Fireflies,GroundWisps,LeafDrift,MistSheet,PollenSparkle,RainRipples,WaterMist}`.

`NS_CosmicPetalOrbit` and `NS_SakuraCosmicAurora` appear in the live-audit list
but **not** in the 2026-09-13 BRANCH_LEDGER EnvSandbox slice — presence extra-unknown.

### Melodia/VFX (from `vfx_stub_audit_2026-08-30.json` + ecosystem / polish pack)

`NS_Melodia_ClickSparkle`, `NS_Melodia_CursorTrail`,
`NS_Melusina_{Arc,ChaosDrift,Dust,EntropyDust,EyeSparkle,Glint,Globules,Splash,Ripple,SwingTrail,ProviderSigil,Superposition,Sigil}`.
Folder also held `BP_MelodiaNiagaraDriver` and `Melusina_WaterFX` (not systems).
Names seen only in older scripts (`NS_Melodia_LaneHit`, `CymaticDust`,
`PulseWavefront`) are **not** given rows — no ledger path.

### Not built / fixture-only (discarded as live inventory)

`Content/Python/gmm/fixtures/niagara_nikki_library.json` (2026-07-15) names
`NS_Nikki_{SparkleDrift,FloatingMotes,WishBurst,FabricTrail,FlowerPetals}` under
`/Game/EnvSandbox/VFX/Nikki/`. No git path, no BRANCH_LEDGER hit. **Not counted.**

## 6. Cross-links MI ↔ NS (from receipts, not live refs)

Highest-confidence (script assignment or named clone):

| NS | MI / master | Source |
|---|---|---|
| `NS_ChoralSheep_BeatBurst` | `MI_NS_ChoralSheep_BeatStar` | Batch B + work order |
| `NS_ChoralSheep_WoolMotes` | `MI_NS_ChoralSheep_WoolMote` | same |
| `NS_SakuraPetals_v2` / Ground / WaterPetals | `MI_Niagara_Petal_Instance` | `fix_zenforest_niagara_renderer_materials.py` |
| `NS_SakuraPetalGust` | `MI_Niagara_Gust_Instance` | same |
| `NS_CosmicPetalOrbit` | `MI_Niagara_NebulaPetal` | same |
| `NS_SakuraCosmicAurora` | `MI_Niagara_AuroraRibbon` | same |
| `NS_SakuraPetals` v1 / v2 Fountain | `MI_Niagara_Petal` | `finalize_niagara_mcp.py` |
| `NS_SakuraDreamSparkle` | `MI_Niagara_Sparkle` | same |
| `NS_SakuraLanternMotes` | `MI_Niagara_Mote` | same |
| `NS_SakuraPondShimmer` | `MI_Niagara_Pond` | same |
| `NS_Uni_MistSheet` etc. mote five | `MI_Niagara_Mote_*` | `Docs/VFX_ASSET_MANIFEST.md` |
| `NS_Melodia_PetalEndlessLoop` | `M_Niagara_PetalMesh_Loop` | manifest |
| `NS_Melodia_LeafPileLoop` | `MI_Leaves` (Effects, **untracked**) | manifest + `author_endless_loops.py` |
| ClickSparkle / EyeSparkle / Globules / Splash | flipbook master / Water / SplashFlip | manifest §4 |

## 7. Orphans (documented, no opposite-side link)

**MIs with no documented NS:** `MI_Niagara_Melodia_Static_DropletRing`,
`MI_Niagara_Melodia_Static_StarGold`, `M_Niagara_PetalSprite_Loop`,
`M_Niagara_PetalPile`, `M_Niagara_SDF_Loop` (consumers unproven in this clone).

**NS with unknown material:** Sea Above droplets, `NS_MelodiaWaterContact`,
three AdvancedReplacement candidates, `NS_ConstellationTwinkle`,
`NS_ConstellationDraw` (owner Fix A OK; material still unnamed here),
six SDF systems, `NS_Melodia_CursorTrail`.

**Names with no path:** HybridSparkles, PetalCascade, MotionTrails, FluidSplash.

## 8. Follow-up

A Windows editor lane with Monolith should run `Tools/niagara_ecosystem_audit.py`
and a SubUV/`FlipFPS` pin dump, then merge into the CSV. Until that lands, treat
every UNKNOWN row as **not proven clean**.
