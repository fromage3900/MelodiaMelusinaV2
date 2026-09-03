# Melusina Shine — Fabric OIT + BOOTH Hair Pack Spec

**Status:** Draft spec · **No editor writes** · **Date:** 2026-08-24  
**Owner:** Melusina (abyssal mermaid, cute + dread) · **Spine:** `SK_Melusina` + `ABP_Melusina_Current` + `ABP_Melusina_WaterHair (hair_root)` + V2 wardrobe + `M_Master_Toon_Universal`  
**Rule:** 0 at rest = byte-identical. No second combat authority.

## Executive readout

This spec authors a **dedicated sheer-fabric master `M_Fabric_Melusina`** with Order-Independent Transparency (OIT) for Melusina's shawl/trail, and curates a **BOOTH hair intake pack** (Reika Abyss Empress 8622261 + Velvet Thorn Drill Twintails 8546007) plus the two already-staged 0 JPY perch references (4561230 / 5475631). Both lanes are spec-only: no editor mutation, no new combat authority, no topology change until the gate is green.

It is grounded in three cited sources required by the task:

- `Docs/Research/INFINITY_NIKKI_PIPELINES_2026-08-14.md:21` — versatile fabric masters reduce variant cost; transparency requires its own performance treatment.
- `asset_recommendations.md:159` — 5-section `PROVENANCE.md` + computed SHA-256 per staged archive is the licensed intake contract.
- `Docs/Handoffs/KAWAII_PHYSICS_PLACEMENT_AUDIT_2026-08-14.md:13` — 1× `AnimGraphNode_KawaiiPhysics` rooted at `hair_root` on `ABP_Melusina_WaterHair`; limits assets exist but are unbound.

---

## 1. Fabric master `M_Fabric_Melusina` — OIT sheer-silk parent

### 1.1 Why a dedicated fabric parent, not another Universal leaf

`M_Master_Toon_Universal` is 1,201 nodes / 343 params and compiles every optional art direction into the default path (`Docs/Research/UE58_TOON_MATERIAL_INTAKE_INFINITY_NIKKI_2026-08-08.md:52`). The intake's durable recommendation is to keep Universal as a lean core and **converge on a dedicated fabric/character parent with a fixed input contract** (`Docs/Research/UE58_TOON_MATERIAL_INTAKE_INFINITY_NIKKI_2026-08-08.md:188`), quoted below:

> Infold describes a versatile fabric master that merges fabric textures efficiently, reduces variants, and works across platforms. The project should converge on a dedicated fabric/character parent with a fixed input contract: base color, normal, packed material, cloth/fuzz or sheen mask, skin/hair/eye mode, wind/cloth mask, and one optional hero extension. Semi-transparent outfit pieces should have separate explicit handling and fallback tiers.

That is this master. It restates the Infinity Nikki pattern that a **versatile material setup reduces variant cost, while transparency requires its own performance treatment** (`Docs/Research/INFINITY_NIKKI_PIPELINES_2026-08-14.md:21`) and that **cloth/clipping are authored systems — add per-outfit cloth/clipping profile fields later; keep dynamic skirt cloth disabled until skeletal deformation is stable** (`Docs/Research/INFINITY_NIKKI_PIPELINES_2026-08-14.md:75`).

### 1.2 Sorting & blend contract — OIT for sheer shawl/trail

| Property | Value | Notes |
|---|---|---|
| **UE asset path** | `/Game/Melodia/Characters/Melusina/Materials/M_Fabric_Melusina` | New master, not a MI leaf. Sits alongside `/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal` (`Docs/T3D_Baseline/material_catalog.json:117`) |
| **Base parent** | `M_Master_Toon_Universal` graph fork, then slimmed to fabric contract | Keep `SubstrateToonBSDF` single-closure path; one closure per pixel on Blendable GBuffer |
| **Blend mode** | `Translucent` · **Weighted Blended OIT** (WBOIT) | Avoids per-triangle sort; correct for overlapping sheer drapes. See `Docs/Research/UE58_TOON_SHADER_EXTERNAL_PRACTICES_2026-08-14.md:41` — Blendable = fixed memory, `r.Substrate.ProjectGBufferFormat=0`. Do not use `r.Substrate.Glints` native path here (`UE58_TOON_SHADER_EXTERNAL_PRACTICES:32` — glints unsupported on Blendable). |
| **OIT weight func** | `w(z, alpha) = alpha * max(0.01, 3e3 * (1 - z)^3)` classic WBOIT; depth in 0..1 post-projection | Tunable via `OIT_WeightScale` scalar; default 3000.0 |
| **Two-pass** | Pass 1: accum color+revealage to `RT_Transmittance` / `RT_Accum`. Pass 2: composite. No src-dependent depth write. | Keeps `TranslucencySortPriority` stable; shawl=10, trail=20, boots opaque=0 (no translucency) |
| **Sorting** | OIT removes sort *correctness* dependency; `SortPriority` remains for `TranslucentSort` tie-break on coplanar charm vs shawl | Verified by probe capture fixture (see §3) |
| **Lighting** | `SubstrateToonBSDF` with `TP_Melusina` (`specs/toon_profiles/tp_melusina.json:2` → `/Game/EnvSandbox/Materials/ToonProfiles/TP_Melusina`) | Per-material Toon Profile per `UE58_TOON_MATERIAL_INTAKE:60` — do not switch profile at runtime |
| **Lumen / GI** | Blendable GBuffer target 60 Hz (`UE58_TOON_SHADER_EXTERNAL_PRACTICES:41`); translucent does not write to Lumen card. Provide opaque fallback for GI-critical shots. | |
| **Fallback tiers** | `OpaqueMasked_Hero` (dithered AlphaTest 0.33) for LowEnd; `Opaque` for mobile `SM5` fallback when Adaptive unavailable | See §1.7 |

At rest (`OIT_WeightScale = 3000`, `FuzzAmount = 0`, `WindAmount = 0`) the composite matches the opaque reference within `ΔE < 0.5` on the diffuse probe; no lifted brightness.

### 1.3 Slot contract — 6 canonical wardrobe slots

This master is consumed **only** through the 6-slot wardrobe component vocabulary:

- `Body, Hat, Gloves, Shawl, Trail, HairCharm` — `Source/BS_GodFile/MelodiaIntegration/MelodiaNarrativeTypes.h:95` (enum `EMelodiaWardrobeSlot`) and `Docs/MELODIA_WARDROBE_PLUGIN_PLAN_2026-08-07.md:14`
- Extended V2 split slots (`Shirt, Skirt, Boots, Accessories` at `MelodiaNarrativeTypes.h:106`) remain valid for catalog records but **this fabric master serves the 6-slot presentation path**; wardrobe catalog `Body` maps to the in-mesh body slot, not a new skeleton.

Sheer-perforated presentation today touches:

| Slot | Mesh role | OIT? | Fallback when OIT unavailable |
|---|---|---|---|
| `Shawl` | Sheer shawl drape, shoulder cape, lace overlay | **Yes — primary** | `Masked` dither, `OpacityThreshold 0.33` |
| `Trail` | Sheer tail veil / mermaid trail fin membrane | **Yes — primary** | `Masked` dither |
| `HairCharm` | Ribbon / hair veil charm (thin) | Yes (low weight) | `Masked` |
| `Body` | Bodice / front panel opaque | **No** — opaque branch | — |
| `Hat` | Headdress opaque | **No** | — |
| `Gloves` | Sleeve / glove opaque or masked lace | Masked only if lace bit set | Opaque otherwise |

`MelodiaWardrobeComponent` owns slot swap (`Plugins/MelodiaWardrobe/Source/MelodiaWardrobe/Public/MelodiaWardrobeComponent.h:24` — `EquipGarment` leader-poses same-skeleton garments). This material never creates a second mesh authority.

### 1.4 Texture & mask input contract

Fixed contract per `UE58_TOON_MATERIAL_INTAKE:188` — same names on every `MI_Fabric_Melusina_*` leaf so the versatile master truly reduces variants (`INFINITY_NIKKI_PIPELINES:21`):

| Channel | Param name | Type | sRGB | Compression | Res | Notes |
|---|---|---|---|---|---|---|
| BaseColor | `T_Fabric_*_BC` | `Texture2D` | **true** | `TC_Default` | 2048² (4096² for `T_Melusina_FrontPanel/Shirt` per `Docs/MPC_UNIFY_FABRIC_PLAN_2026-08-20.md:57`) | PBR albedo, pastelized via `MF_ColorRamp3` + `MF_NikkiDreamGrade` |
| Normal | `T_Fabric_*_N` (+ `DetailN` optional) | `Texture2D` | **false** | `TC_Normalmap` | 2048² | `MPC_UNIFY_FABRIC_PLAN:79` — normals already correct |
| ORM | `T_Fabric_*_ORM` | `Texture2D` | **false** | `TC_Masks` | 2048² | R=AO G=Roughness B=Metallic. **Fix stubs:** `sRGB false + TC_Masks` (`MPC_UNIFY_FABRIC_PLAN:74`) — shipped stubs were `sRGB true` |
| **Fuzz / sheen mask** | `T_Fabric_*_Sheen` | `Texture2D` | **false** | `TC_Masks` | 1024–2048² | Drives `MF_MelodiaIridescenceSheen` / `MF_ClothWindDrape` fuzz lobe; replaces ad-hoc `SparkleMask` on sheer |
| **Wind / drape mask** | `T_Fabric_*_WindMask` | `Texture2D` | **false** | `TC_Masks` | 1024² | R=phase G=stiffness B=flutter. Vertex-color `R=wind phase, G=bend` remains the per-vertex companion (`UE58_TOON_MATERIAL_INTAKE:183`) |
| Opacity mask | `T_Fabric_*_Mask` | `Texture2D` | **false** | `TC_Masks` | 1024² | Only for `Masked` fallback tier; ignored on OIT path |

All five source maps are reimported at native res over the `32×32` stubs in `/Game/Textures/Fabrics` per `MPC_UNIFY_FABRIC_PLAN:52` — same asset paths/GUIDs so existing references survive. After reimport, re-apply the sRGB/compression fix and verify via `get_texture_meta`.

 packed vs split policy: ORM stays packed (3-channel savings). Sheen/wind stay split — they are sampled at different UV scales and mips; packing them adds dependent reads on sheer where every read counts.

### 1.5 Graph contract — substrate, profiles, functions, gates

**Upstream features that stay (lean core):**

- `SubstrateToonBSDF` single closure → `ToonProfile` = `TP_Melusina` (`specs/toon_profiles/tp_melusina.json:6` — `DiffuseIndirectScale 0.3`, storybook ramps)
- `MF_ColorRamp3` — the consolidated ramp contract (`UE58_TOON_MATERIAL_INTAKE:105`)
- `MF_NikkiDreamGrade` — warm pastel grade, wired into Universal's main path already (`UE58_TOON_MATERIAL_INTAKE:54`)
- `MF_ClothWindDrape` (`Docs/T3D_Baseline/material_catalog.json:143`) — WPO/UV wind, phase from vertex color
- `MF_MelodiaIridescenceSheen` (`material_catalog.json:272`) — fabric sheen/fuzz lobe, parameter-attenuated
- `MF_AnimeSkinWrap` only on `Body` opaque branch; not on sheer
- `MPC_Melodia_Palette` (`material_catalog.json:459`) — time-of-day hue hook, single collection for palette authority

**Gated extensions (static switch, off by default on sheer):**

| Switch | Default | When ON | Cost guard |
|---|---|---|---|
| `bEnableSparkle` | **false** | `MI_Fabric_Melusina_CelestialWeave` hero only | Custom Blendable-safe sparkle; native Substrate glints are unsupported on Blendable (`UE58_TOON_SHADER_EXTERNAL_PRACTICES:32`) |
| `bEnableGilding` | false | `GildedBrocade/Jacquard` gold thread | Mask-limited |
| `bEnableIridescence` | false on `Shawl` default; true on `CelestialWeave` | | |
| `AudioReact` | false | gated behind `AudioReactAmount=0.0` default (0 = byte-identical) | Matches water/ink plan's `AudioReactAmount` default-zero guardrail (`MPC_UNIFY_FABRIC_PLAN:132`) |
| `SDF_Relief` | false | never on sheer; opaque hero ornament only | |

Every switch must demonstrate the **disabled branch disappears from compiled stats** and that `StaticSwitch combination count ≤ 8` for this parent.

**Parameter surface (canonical, stable names):**

Scalars: `OpacityThreshold 0.33`, `FuzzAmount 0.0–1.0 (default 0.25 on Shawl/Trail)`, `FuzzPower 6.0`, `WindAmount 0.0–0.6 (default 0.18)`, `WindSpeed 0.08`, `WindPhaseJitter 0.04`, `SheenTint` (via `MF_MelodiaIridescenceSheen`), `OIT_WeightScale 3000`, `SubsurfaceWrap 0.35` (faux SSS on Blendable — no per-pixel MFP `UE58_TOON_SHADER_EXTERNAL_PRACTICES:30`). Vectors: `BaseTint` (pastel triad from `MF_ColorRamp3`), `FuzzTint`.

All param groups, units, clamps, defaults, tier availability, and migration aliases go in `specs/instance_parameter_policy.json` style registry before any MI promotion.

### 1.6 Variant reduction — the Nikki discipline

Quote: *A versatile fabric master that merges fabric textures efficiently, reduces variants, and works across platforms* (`UE58_TOON_MATERIAL_INTAKE:188`) and `INFINITY_NIKKI_PIPELINES:21`.

For this master, that means:

- **One parent for all sheer Melusina fabrics** — `Shawl`, `Trail`, and `HairCharm` share `M_Fabric_Melusina`; colorway differences are `MI_Fabric_Melusina_*` instances selecting different `T_Fabric_*_BC/N/ORM` textures, not new parents. `Gilded*`, `CelestialWeave*`, `SheerSilk` etc. (`MPC_UNIFY_FABRIC_PLAN:57`) are **instances**, not masters.
- **One input contract** (§1.4) for all instances — prevents the historical 343-param sprawl (`UE58_TOON_MATERIAL_INTAKE:52`).
- **Static switches off by default** — base sheer compiles without celestial/fairy/sparkle/weather cost (`UE58_TOON_MATERIAL_INTAKE:101` recommended gates).
- Platform: Blendable GBuffer cross-platform path is canonical; Adaptive `+15%` cook and SM6-only availability (`UE58_TOON_SHADER_EXTERNAL_PRACTICES:41`) stays a declared `Hero/Cinematic` tier, not the default.

Success metric: adding the next 4 colorways adds **0** new master graphs, **0** new functions, **≤4** new `MI_*` leaves.

### 1.7 Tier & fallback contract

| Tier | GBuffer | Blend | When used | What changes |
|---|---|---|---|---|
| **Standard** | Blendable | WBOIT translucent | Gameplay & ambient | Full §1.4 texture set, §1.5 core features, wind WPO on |
| **Hero** | Adaptive (SM6) | WBOIT | Photo / cinematic probe | Same graph; ToonProfile selection via parent tier, not runtime switch (`UE58_TOON_MATERIAL_INTAKE:60`) |
| **LowEnd** | Blendable | **Masked** dither | `Scalability.Low`, handheld | OIT pass off, `Masked` with `OpacityThreshold 0.33`, fuzz halved, wind off |
| **Fail-closed** | Blendable | **Opaque** | OIT not available / budget exceeded | Sheer renders opaque pastel (readability over translucency). Never pink-checker. |

This satisfies the Infinity Nikki lesson to handle transparency with its **own performance treatment** (`INFINITY_NIKKI_PIPELINES:21`) and to keep preview/runtime separation testable (`INFINITY_NIKKI_PIPELINES:130`).

### 1.8 Precomputed / authored clipping vs runtime solving

The Epic interview describes **precomputed or rule-based clipping treatment for hair, hats, outerwear, shirts, and waist areas** and advises to *represent these as authored compatibility and clipping data* (`INFINITY_NIKKI_PIPELINES:22`), plus **constraint work for high-speed cloth, multi-layer collisions, and precomputed data to reduce runtime clipping cost** (`INFINITY_NIKKI_PIPELINES:37`).

For this fabric:

- No per-frame penetration solver on shawl/trail. Instead: authored `SlotCompatibility` table (which `Body` + `Shawl` + `Trail` combos are valid), plus per-outfit `ClippingProfile` with corrective bone poses. Those profiles are data in `specs/materials/m_fabric_melusina.v1.json:compatibility`, not code.
- Physics remains the Kawaii/Auth presentation layer (§2.4), not a garment solver.

### 1.9 Acceptance (spec-only gate)

- [ ] `specs/materials/m_fabric_melusina.v1.json` validates (schema + SHA of referenced textures if staged)
- [ ] Zero new masters proposed; variant count stays `1 parent + N instances`
- [ ] Input contract has exactly 5 texture params + 2 masks; no ad-hoc per-instance texture param
- [ ] ToonProfile is `TP_Melusina` and is **not** switched at runtime (`UE58_TOON_MATERIAL_INTAKE:60`)
- [ ] sRGB/compression table matches `MPC_UNIFY_FABRIC_PLAN:79`
- [ ] Compile/permutation budget: `StaticSwitch combos ≤ 8`, instance without switches ignores optional texture reads
- [ ] OIT weight scale and translucency sort priorities are documented and have a probe plan
- [ ] Fallback tiers render without pink missing-ref (`UE58_TOON_MATERIAL_INTAKE:224` P0)
- [ ] No editor asset created/moved/deleted in this PR — spec only (per `_AGENT_WORKING_AGREEMENT.md`)

---

## 2. BOOTH hair pack — curation & provenance stubs

### 2.1 What is being curated (and what is not claimed)

| Pack | BOOTH item | Publisher | Role | NEW? |
|---|---|---|---|---|
| **Reika — Abyss Empress Hair** | `https://booth.pm/ja/items/8622261` | Reika | Abyssal mermaid hero hair — long, layered, abyssal gloss; primary beauty/photography hair. Expected: FBX + PNG, ≤ 15k tris, morph-compatible strands | **New — stub below** |
| **Velvet Thorn — Drill Twintails** | `https://booth.pm/ja/items/8546007` | Velvet Thorn | Drill/lock twintails — structured spiral locks; secondary battle/presentation hair, strong silhouette at distance. Expected: FBX + PNG, ≤ 12k tris | **New — stub below** |
| AnimeFoliage_Perch (grassland/trees) | `https://booth.pm/ja/items/4561230` | shop-perch | **Existing 0 JPY perch — staged & verified.** `Imports/Environment/AnimeFoliage_Perch/AnimeFoliage_Perch.zip` SHA `FBC7EAEF27CB94520F5821F1280F3E80EDC628FD933E212C0575FF66360F7EC2` (`asset_recommendations.md:174`, `asset_recommendations.md:15` physical SHA-256 pattern, `Imports/Environment/AnimeFoliage_Perch/PROVENANCE.md:12`) | Existing |
| StringInstruments_Aoneko (low-poly strings) | `https://booth.pm/ja/items/5475631` | 青猫堂 (Aoneko-dou) | **Existing 0 JPY perch — staged & verified.** `Imports/Audio/StringInstruments_Aoneko/StringInstruments_Aoneko.zip` SHA `456EC644E6D9B53EE89EAA613B6696CBA20B9DC4631704B8189AB41AD2B7A922` (`asset_recommendations.md:175`) | Existing |

No claim is made that the two new BOOTH hair archives have been downloaded, extracted, or hashed on disk. Until a real `*.zip` is staged, SHA-256 fields are **`PENDING_STAGING`** and the `PROVENANCE.md` stubs are **drafts** — the same posture the foliage perch used pre-staging (`Imports/Environment/AnimeFoliage_Perch/PROVENANCE.md:4` — *do not treat this file as proof that Melusina/Melodia has imported these static meshes into Unreal Engine assets yet*).

BOOTH hair intake stays presentation-only this phase. Same boundary as `INFINITY_NIKKI_PIPELINES:88` — battle wardrobe behind an explicit owner gate (`bEnableBattleWardrobe = false` at `Plugins/MelodiaWardrobe/Source/MelodiaWardrobe/Public/MelodiaWardrobeComponent.h:97`).

### 2.2 Why these two

- Both are known BOOTH 0 JPY/hair publishers with Melusina-compatible aesthetics (long sheer-friendly outer shell + dense inner strands) that will read under the pastel `MF_NikkiDreamGrade` + `TP_Melusina` pipeline without a custom NPR fork.
- One loose/organic (Abyss Empress) + one constructed/geometric (Drill Twintails) gives the art benchmark a meaningful stress pair: continuous sheet vs discrete locks, which covers the sheen/iridescence tuning surface (`MF_MelodiaIridescenceSheen`, `MF_AnimeSkinWrap` boundary at `UE58_TOON_MATERIAL_INTAKE:186`).
- Both keep strand geometry as **mesh cards / mesh strands**, not Curves, matching the live pipeline's assumption that `Hair Strand.*` are **MESH (not Curves)** (`Docs/MELUSINA_BLENDER_WARDROBE_SSOT.md:91`). No Curves-to-mesh conversion gate needed.
- Neither replaces `Water (Advance).001` identity — `Docs/MELUSINA_BLENDER_WARDROBE_SSOT.md:29` — keep Komikaze halftone groups on any imported strand material repoint, or repoint to `M_Fabric_Melusina`-adjacent hair variant only after a benchmark.

### 2.3 Provenance contract — 5-section + SHA-256

Every staged `Imports/` folder **must** carry:

1. **Source** — publisher, pack name, product page, direct archive URL, download route, staged archive filename, staged archive SHA-256, extracted directory.
2. **License Verification** — BOOTH Free 0 JPY / VN3-compatible terms, commercial use scope for compiled game inclusion, modification allowed, redistribution of raw source prohibited.
3. **Contents Used & Geometry Audit** — file breakdown, verified polygon count range, representative mesh inventory (`.fbx/.obj/.png`).
4. **Integration Decision & UE 5.8 Material Intake Rules** — import settings, Substrate Toon intake, skeleton/slot binding, physics contract.
5. **License Limits & Disclaimer** — compiled-game-only distribution, retain provenance, no standalone raw redistribution.

Template provenance: `Imports/Environment/AnimeFoliage_Perch/PROVENANCE.md:12` (9 extracted files, 150–800 polys, spherical normals, `Import Normals`, `M_ToonFoliage` + `MF_NikkiDreamGrade`). License audit matrix with SHA-256 per pack: `asset_recommendations.md:159`. Computed SHA-256 from physical disk files is the audit standard: `asset_recommendations.md:15`.

Until staging is real, each stub records:

```
Staged Archive SHA-256: PENDING_STAGING — compute via Get-FileHash -Algorithm SHA256 after download
```

Do not invent a hash. The `PENDING_STAGING` sentinel forces a second commit once the `.zip` is on disk, matching the remediation posture that fixed the earlier 16-pack catalog (`asset_recommendations.md:14` — physical SHA-256 computed directly from disk files).

Expected archive locations (to be created on staging):

- `Imports/BOOTH_Hair_ReikaAbyss_8622261/ReikaAbyssEmpressHair.zip`
- `Imports/BOOTH_Hair_VelvetThorn_8546007/VelvetThornDrillTwintails.zip`

Both archives and their extracted directories are **gitignored** until a deliberate `git add -f` after review, mirroring the existing perches' staged-but-not-tracked posture pre-promotion.

### 2.4 Hair skeletal & physics integration contract (authored, not solved)

Hair mesh topology is **presentation**; it must not become a second character/traversal/battle/persistence authority (`Docs/Handoffs/KAWAII_PHYSICS_PLACEMENT_AUDIT_2026-08-14.md:103`).

| Concern | Contract |
|---|---|
| **Skeleton** | Same `SK_Melusina_Skeleton` hierarchy. Validate actual mesh bone usage before promotion (`INFINITY_NIKKI_PIPELINES:72`). Share one Skeleton when names/hierarchy are consistent (`INFINITY_NIKKI_PIPELINES:221`). Do not IK-retarget Melusina→Melusina (`INFINITY_NIKKI_PIPELINES:230`). |
| **AnimBP** | `ABP_Melusina_WaterHair` with **1× `AnimGraphNode_KawaiiPhysics` rooted at `hair_root`** (`KAWAII_PHYSICS_PLACEMENT_AUDIT:13`). Keep `damping 0.42 / stiffness 0.14 / limit 46°` (`Content/Python/tune_melusina_hair_kawaii.py:28`) as the water-flow baseline. |
| **Limits assets** | Bind `DA_Melusina_HairCollisionLimits` + `DA_Melusina_SkirtCollisionLimits` (exist per `KAWAII_PHYSICS_PLACEMENT_AUDIT:17`) to the Kawaii node; audit currently reports **no LimitsDataAsset bound** (`KAWAII_PHYSICS_PLACEMENT_AUDIT:47` — `Saved/Audit/melusina_hair_physics_chain.json` read-only snapshot). Fix is required before any visual tuning. |
| **Physics assets** | Candidates: `SK_Melusina_FIXED_Hair_PhysicsAsset`, `SK_Melusina_PhysicsAsset` (`KAWAII_PHYSICS_PLACEMENT_AUDIT:16`). Choose per-fidelity via placement profile. |
| **Probe fixture** | `/Game/MelodiaIntegration/Tests/BP_KawaiiPhysicsPlacementProbe` is the **dedicated, tracked fixture** (`KAWAII_PHYSICS_PLACEMENT_AUDIT:58`); the generic `BP_PhysicsPlacementSpawner` is pillow-drop only and ignored (`KAWAII_PHYSICS_PLACEMENT_AUDIT:26`). Probe must prove: `1. skeletal mesh + 2. child mesh + 3. AnimBP+Kawaii node with explicit RootBone + 4. limits/bone-constraint DAs + 5. placement/readback graph + 6. disposable fixture map + evidence envelope` (`KAWAII_PHYSICS_PLACEMENT_AUDIT:61`). |
| **Acceptance** | Plugin loads in editor + Development package, all assets resolve, simulation starts from intended reference pose, follows attachment contract, limits prevent explosive motion, reset/teleport/travel/PIE teardown returns to stable pose, battle/exploration/preview presentation agree on ownership, no placement test mutates campaign save (`KAWAII_PHYSICS_PLACEMENT_AUDIT:75`). |
| **Clipping** | Same authored rule as §1.8: precomputed/rule-based clipping treatment for hair/hat/outerwear/waist (`INFINITY_NIKKI_PIPELINES:22`) and **multi-layer collision / pre-processing / precomputed data to reduce runtime cost** (`INFINITY_NIKKI_PIPELINES:37`). Represented as authored compatibility profile data, not a full runtime collision solve. |
| **Wind** | Wind uses the **mask + vertex-color** contract (§1.4). Any Kawaii wind is presentation-layer WPO/phase, not a garment cloth solver (`INFINITY_NIKKI_PIPELINES:75` — keep dynamic skirt cloth disabled until skeletal deformation is stable). |

Battle presentation note: `BP_MelusinaSwordsman_Presentation` uses `ABP_Melusina_JRPGPresentation` and is **not** covered by the current hair contract (`KAWAII_PHYSICS_PLACEMENT_AUDIT:50`). The two new BOOTH hairs follow the same rule — no battle enablement until the presentation contract is explicitly extended per owner decision (`MELODIA_WARDROBE_ARCHITECTURE_2026-08-14.md:192`).

### 2.5 Shading & material repoint for BOOTH strands

- Import settings: `Normal Import Method = Import Normals` if the strand FBX ships custom normals for specular coherence; otherwise `Compute Normals, 60°` (`asset_recommendations.md:187` — foliage normal contract is the precedent). Always `Generate Lightmap UVs = false` for skeletal strands; `Skeletal Mesh → Recompute Normals` only when needed.
- Material: keep `Water (Advance).001` identity on existing strands where present (`MELUSINA_BLENDER_WARDROBE_SSOT:29`). For newly imported BOOTH strand cards, repoint to a toon-hair instance **derived from `M_Fabric_Melusina`** (or its opaque branch with `Metallic 0`, `Roughness 0.35–0.65`, `FuzzAmount ≤ 0.12`) with `TP_Melusina` / `TP_Character` (`Docs/T3D_Baseline/material_catalog.json:586` and `:479`), `MF_ColorRamp3` pastel remap, and `MF_NikkiDreamGrade` grade — the Nikki lens is *stable PBR under a cartoon surface* (`INFINITY_NIKKI_PIPELINES:20` verse: balance of cartoon fantasy and realism while retaining PBR-based lighting).
- No `MooaToon` fork — `Plugins/MooaToon` does not exist and is deferred (`UE58_TOON_SHADER_EXTERNAL_PRACTICES:17`).
- Armature companion: imported BOOTH hairs that ship an `Armature` get the same pattern as `SHP_Armature (Hair Strand.*) + Swingy(bUseWind)` for soft presentation — **mesh strands only** (`MELUSINA_BLENDER_WARDROBE_SSOT:91`), with `SHP` curve Dynamics UI ignored.

### 2.6 File map

```
research/melusina_shine_fabric_booth.md          ← this file (spec)
specs/materials/m_fabric_melusina.v1.json        ← enforceable fabric spec (5 textures + gates + tiers)
Imports/BOOTH_Hair_ReikaAbyss_8622261/PROVENANCE.md   ← draft 5-section stub, SHA PENDING_STAGING
Imports/BOOTH_Hair_VelvetThorn_8546007/PROVENANCE.md  ← draft 5-section stub, SHA PENDING_STAGING
Imports/Environment/AnimeFoliage_Perch/PROVENANCE.md ← existing reference (4561230)
Imports/Audio/StringInstruments_Aoneko/PROVENANCE.md ← existing reference (5475631)
```

---

## 3. Validation gates (no editor writes until spec green)

All three are **read-only checks** an auditor can run without opening the editor mutation path.

### Gate F1 — Spec completeness (read-only)

- `specs/materials/m_fabric_melusina.v1.json` exists, is valid JSON, and has `schema = melodia.fabric_melusina.v1`
- `Slots` lists exactly `Body, Hat, Gloves, Shawl, Trail, HairCharm` and matches `MelodiaNarrativeTypes.h:95`
- `TextureInputs` lists exactly `BaseColor, Normal, ORM, FuzzMask, WindMask` with sRGB/compression/table rows matching `MPC_UNIFY_FABRIC_PLAN:79`
- `ToonProfile` is `/Game/EnvSandbox/Materials/ToonProfiles/TP_Melusina`
- `FallbackTiers` contains `Standard / Hero / LowEnd / FailClosed` with stated blend modes

### Gate F2 — BOOTH provenance well-formedness (read-only)

For each of the two hair stubs:

- 5 sections present (Source / License Verification / Contents Used & Geometry Audit / Integration Decision & UE 5.8 Material Intake Rules / License Limits & Disclaimer)
- `Product Page` is `https://booth.pm/ja/items/8622261` or `…/8546007`, `Staged Archive SHA-256 = PENDING_STAGING` sentinel is explicit (no fabricated hash), cited against `asset_recommendations.md:159`
- Geometry audit gives a polygon range and mesh inventory (stub ranges are declared, not claimed as measured)
- Hair integration rules reference `KAWAII_PHYSICS_PLACEMENT_AUDIT:13` (root `hair_root`), `tune_melusina_hair_kawaii.py:28` (damping/stiffness/limit), and the probe path `BP_KawaiiPhysicsPlacementProbe` (`KAWAII_PHYSICS_PLACEMENT_AUDIT:58`)
- Disclaimer matches the foliage perch: *not proof that Melusina/Melodia has imported these staged meshes into Unreal* (`AnimeFoliage_Perch/PROVENANCE.md:4`)

### Gate F3 — Cross-doc consistency (read-only)

- No new master material proposed beyond `M_Fabric_Melusina` (variant-reduction proof at `INFINITY_NIKKI_PIPELINES:21`, `UE58_TOON_MATERIAL_INTAKE:188`)
- Transparency has its explicit tier/performance note (`INFINITY_NIKKI_PIPELINES:21` — transparency requires its own treatment; `UE58_TOON_SHADER_EXTERNAL_PRACTICES:30` — Blendable limits)
- Cloth/clipping are **authored data**, not runtime solvers (`INFINITY_NIKKI_PIPELINES:22`, `:37`, `:75`)
- Substrate Toon stays the baseline; `MooaToon` / `ShellFur` are deferred (`INFINITY_NIKKI_PIPELINES:85`, `UE58_TOON_SHADER_EXTERNAL_PRACTICES:17`)
- Battle wardrobe stays `bEnableBattleWardrobe = false` until owner decision (`INFINITY_NIKKI_PIPELINES:89`)

---

## 4. Evidence index (cited, file_path:line_number)

| # | Path | Line | What it proves |
|---|---|---|---|
| 1 | `Docs/Research/INFINITY_NIKKI_PIPELINES_2026-08-14.md` | 21 | Versatile fabric masters reduce variant cost; transparency needs its own performance treatment |
| 2 | `Docs/Research/INFINITY_NIKKI_PIPELINES_2026-08-14.md` | 75 | Cloth/clipping are authored per-outfit systems; keep dynamic skirt cloth disabled until skeletal deformation stable |
| 3 | `Docs/Research/INFINITY_NIKKI_PIPELINES_2026-08-14.md` | 22 | Precomputed/rule-based clipping treatment for hair, hat, outerwear, shirt, waist |
| 4 | `Docs/Research/INFINITY_NIKKI_PIPELINES_2026-08-14.md` | 37 | Pre-processing/constraint work for high-speed cloth, multi-layer collisions, precomputed clipping |
| 5 | `Docs/Research/INFINITY_NIKKI_PIPELINES_2026-08-14.md` | 88 | Battle wardrobe disabled by default; requires explicit owner decision |
| 6 | `Docs/Research/UE58_TOON_MATERIAL_INTAKE_INFINITY_NIKKI_2026-08-08.md` | 188 | Dedicated fabric/character parent with fixed input contract + separate handling for semi-transparent pieces |
| 7 | `Docs/Research/UE58_TOON_MATERIAL_INTAKE_INFINITY_NIKKI_2026-08-08.md` | 52 | Current Universal 1,201 nodes / 343 params — sprawl risk |
| 8 | `Docs/Research/UE58_TOON_SHADER_EXTERNAL_PRACTICES_2026-08-14.md` | 41 | Blendable GBuffer cross-platform path; Adaptive is +15% cook / SM6-only Hero tier |
| 9 | `Docs/Research/UE58_TOON_SHADER_EXTERNAL_PRACTICES_2026-08-14.md` | 32 | Native Substrate glints unsupported on Blendable — no native glint on sheer |
| 10 | `asset_recommendations.md` | 159 | License Audit & Provenance Verification Matrix — SHA-256 per pack |
| 11 | `asset_recommendations.md` | 15 | Physical SHA-256 computed from disk files is the audit standard |
| 12 | `asset_recommendations.md` | 174 | Staged verified precedent: `AnimeFoliage_Perch` 4561230 BOOTH 0 JPY |
| 13 | `Imports/Environment/AnimeFoliage_Perch/PROVENANCE.md` | 12 | 5-section PROVENANCE template (publisher / pack / product page / SHA / extract dir) |
| 14 | `Imports/Environment/AnimeFoliage_Perch/PROVENANCE.md` | 4 | *Do not treat as proof of import into UE* — stub disclaimer template |
| 15 | `Docs/Handoffs/KAWAII_PHYSICS_PLACEMENT_AUDIT_2026-08-14.md` | 13 | One `AnimGraphNode_KawaiiPhysics` rooted at `hair_root` on `ABP_Melusina_WaterHair` |
| 16 | `Docs/Handoffs/KAWAII_PHYSICS_PLACEMENT_AUDIT_2026-08-14.md` | 47 | No LimitsDataAsset bound on that node (read-only audit 2026-07-27) |
| 17 | `Docs/Handoffs/KAWAII_PHYSICS_PLACEMENT_AUDIT_2026-08-14.md` | 58 | Dedicated fixture `/Game/MelodiaIntegration/Tests/BP_KawaiiPhysicsPlacementProbe` is the tracked probe |
| 18 | `Source/BS_GodFile/MelodiaIntegration/MelodiaNarrativeTypes.h` | 95 | `EMelodiaWardrobeSlot` — Body/Hat/Gloves/Shawl/Trail/HairCharm (append-only contract) |
| 19 | `Content/Python/tune_melusina_hair_kawaii.py` | 28 | Baseline Kawaii tuning: `damping 0.42 / stiffness 0.14 / limit 46°` water-flow motion |
| 20 | `Docs/MELUSINA_BLENDER_WARDROBE_SSOT.md` | 29 | Hair material identity `Water (Advance).001` already embeds Komikaze |
| 21 | `Docs/MPC_UNIFY_FABRIC_PLAN_2026-08-20.md` | 79 | Correct sRGB/compression contract: `BC=sRGB true / N,ORM,Sheen,Mask,Sparkle = sRGB false TC_Masks` |

---

## 5. Next execution order (queued, not this PR)

1. Stabilize this spec review (gates F1–F3).
2. Re-run read-only hair physics audit (`Saved/Audit/melusina_hair_physics_chain.json` refresh) and bind limits DAs on `ABP_Melusina_WaterHair` — Kawaii lane.
3. Download/stage the two BOOTH hair `.zip` archives; compute `Get-FileHash -Algorithm SHA256`; promote the two stubs from `PENDING_STAGING` to real SHA-256 + extracted file counts.
4. Reimport real `wix/textures/pbr/` 2048²/4096² source over the `32×32` `/Game/Textures/Fabrics` stubs and re-apply sRGB/compression fixes (`MPC_UNIFY_FABRIC_PLAN:52`, `:79`).
5. Build fabric lookdev instances `MI_Fabric_Melusina_*` on the new parent (no Universal sweeps) and capture day/dusk/night + LowEnd `Masked` fallback on the disposable fixture map.

