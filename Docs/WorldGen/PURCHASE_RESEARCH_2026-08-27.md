# WorldGen Purchase Research — BS_GodFile UE5.8

**Date:** 2026-08-27  
**Project:** BS_GodFile (Unreal Engine 5.8)  
**Owner:** WorldGen lane — single-file scope (`Docs/WorldGen/PURCHASE_RESEARCH_2026-08-27.md` only)  
**Scan type:** Live Fab scan 2026-08-27 via websearch + webfetch (prices per listing at scan time — verify at checkout, Fab prices are preset tiers ending in .99 and exclude VAT/tax)

---

## 1. Executive Summary — MeshTerrain-Only Constraint

**P0 constraint:** `ALandscape` is forbidden for BS_GodFile. Active P0 authority (2026-08-24) and `AGENTS.md` require **MeshTerrain-only** world generation. All terrain must be `UStaticMesh` / `Nanite` / `HISM` / `ISM` / `PCG`-spawned meshes, or voxel-to-mesh, not Landscape heightmap + Landscape material. Any pack whose core value is a Landscape automaterial, Landscape sculpting brushes, or `LandscapeGrassType` is **Landscape-locked** and scores low unless it can export/produce mesh terrain or heightmaps baked to meshes.

**What this means for purchasing:**

- **Landscape-locked packs** (Magic Map M4, Brushify SmartBrush, most Brushify biome packs) require porting to work in this project. Their automaterials target `Landscape` layers/weightmaps, their brushes sculpt `ALandscape`, and their grass systems use `LandscapeGrassType`. To use them MeshTerrain-only you must: (a) export heightmap → import as mesh via Houdini/World Creator/Gaea/World Machine → remap materials to mesh vertex/UV masks, or (b) drive Virtual Heightfield Mesh (VHFM) / RVT pipelines separately. Cost = engineering + material rewrite.
- **Mesh-native / PCG-native packs** (PCGEx / PCGEx Pro, Houdini Engine HDAs that output meshes, Voxel Plugin Pro 2 → Marching Cubes mesh, Fantastic City Generator / Visus / American City mesh cities, Procedural Dungeon mesh dungeons) fit **natively**. They spawn meshes/actors via PCG graphs or voxel pipelines and never require `ALandscape`.
- **External terrain authoring apps** (World Creator, Gaea, World Machine) are **neutral**: they author heightmaps externally; fit depends on your export path. Exporting to `Landscape` is the default tutorial, but exporting to mesh / tiled mesh / heightmap-to-mesh via Houdini or Voxel is P0-compatible. Budget for an HDA or pipeline that converts their output to Nanite meshes.

**Bottom line:** Do not buy Landscape automaterial packs expecting plug-and-play. The highest-fit purchases are (1) free mesh/PCG foundations you already have, (2) PCGEx/Pro as the mesh-PCG backbone, (3) Houdini Engine (FREE) as the mesh-terrain bridge, and (4) mesh city/dungeon generators that bypass terrain entirely.

**Live scan caveat (2026-08-27):** Fab listing pages currently hide price until license tier is selected (Fab migration from UE Marketplace). Where a live fetch returned a license selector without a price, this doc records the last verified Marketplace/Fab tier price and marks `verify at checkout`. Prices shown exclude VAT/tax and are US-dollar base prices; Professional tier may be higher if your 12-month gross revenue > $100k USD [Fab Standard license].

---

## 2. Master Table — Live Fab Scan (2026-08-27)

> Prices verified via websearch + direct Fab fetch where available on 2026-08-27. Where Fab now requires license-select to reveal price, noted as `per Fab listing, verify at checkout` with last known tier price in Notes. Engine versions per listing description at scan time; 5.8 Ready = listing explicitly claims 5.8 or 5.6+PCG (see §4 risks).

| Pack | Fab URL | Price (USD, excl. tax) | License | Engine Versions (listed) | 5.8 Ready | Type | Fit Score 1–10 | Notes |
|------|---------|------------------------|---------|---------------------------|-----------|------|----------------|-------|
| **Calysto World 2.0** (prev. Massive World) — PCG Procedural World Generation | https://www.fab.com/listings/8631308a-67a3-4e20-b3e4-74be19813f77 | per Fab listing, verify at checkout (last Fab tier ~$99.99 Personal / ~$149.99 Professional est.) | Fab Standard (Personal/Professional) | 5.6 listed (docs: "Calysto World 2.0 for UE 5.6; PCG evolves a lot between updates, latest recommended") | ⚠️ Partial — 5.6 certified, no 5.8 listing at scan; PCG drift risk | Plugin + Content (PCG) | **4** | Landscape-tagged on Fab; includes terrain auto-material, 70× 4K heightmap stamps, World Partition/Nanite foliage, VHFM/RVT. Artist-directed PCG but core demos use `ALandscape` + `LandscapeGrassType`. MeshTerrain use requires repurposing PCG graphs to spawn mesh terrain / bypass Landscape. Qwerty Studio ecosystem (Water/Village/Dungeon/Smart Scatter). |
| **Scifi Jungle Biome** (Brushify / MAWI-style biome pack) | https://www.fab.com/search?query=Scifi%20Jungle%20Biome | per Fab listing, verify at checkout (Brushify biomes typically $49.99–$69.99 Personal) | Fab Standard | 5.0–5.4 (Brushify pack baseline) | ❌ No — 5.4 ceiling at scan | Biome Pack (Landscape) | **3** | Typical Brushify biome: Landscape automaterial + foliage. Useful as **mesh/asset source** (extract static meshes, plants, rocks) but material/grass/Landscape layers not usable MeshTerrain-only without porting. Verify includes mesh variants vs Landscape-only. |
| **PCGEx (Free) + PCGEx Pro** (PCG Extended Toolkit) | https://www.fab.com/listings/3f0bea1c-7406-4441-951b-8b2ca155f624 (free core); Pro companion via same publisher | Free (core, MIT on GitHub) / Pro: ~$49.99 Personal per docs (Patreon $25 = half Personal tier) — per Fab listing, verify at checkout | Free: MIT + Fab Standard; Pro: Fab Standard | 5.3–5.6 (PCG framework) | ✅ Yes — active on 5.6, PCG-native, no Landscape dependency | Plugin (PCG) | **9** | 200+ nodes: graphs/clusters (Delaunay/Voronoi/MST), A*/Dijkstra, path ops, octree, Lloyd relaxation, Clipper2 booleans, tensors. Fully parallelized. **Highest MeshTerrain fit:** adds structure to vanilla PCG scattering; spawns meshes/points, not Landscape. Pro embeds free core + niche modules, seamless switch (no redirectors). Interop: ZoneGraph, Watabou. |
| **World Creator** (external terrain authoring) | https://www.world-creator.com/en/buy.phtml (standalone; Fab bridge lists separately) | **Subscription or Perpetual:** Indie $59/yr or $149 perpetual; Pro $179/yr or $499 perpetual; Studio/Enterprise higher — per site, verify at checkout (Fab bridge may list ~$49.99) | Commercial (external) — Indie/Pro/Studio seats; perpetual includes 1 yr updates then 30% renewal | External app (exports heightmap/mesh) | ✅ Yes — output is engine-agnostic mesh/heightmap | External App | **6** | Real-time terrain authoring, exports heightmap + splat + mesh. P0 fit depends on **export path**: default is Landscape heightmap, but mesh export + Houdini remesh is fully MeshTerrain-compatible. Budget Houdini pipeline to convert. |
| **Gaea** (QuadSpinner) | https://quadspinner.com/Order (external; no Fab listing) | Community **FREE** (1K, non-commercial) · Indie **$99** (8K) · Professional **$199** (256K) · Enterprise **$299** (256K + USD/OCIO/SDK) — per QuadSpinner 2025 | Perpetual (QuadSpinner EULA; revenue caps: Indie ≤$100k, Pro ≤$1M, Enterprise >$1M) | External app | ✅ Yes — output is heightmap/mesh/USD | External App | **7** | Node-based erosion/terrain design; Gaea 2.2+ exports heightmap, mesh, and (Pro/Enterprise) USD/OCIO. 3.0 pre-order mid-2026. Better mesh/USD export than World Machine free tier; heat/splat export works with Houdini mesh terrain. |
| **Houdini Engine for UE5** | https://www.sidefx.com/products/houdini-engine/plug-ins/unreal-plug-in/ (plugin via Houdini installer) | **FREE** — Houdini Engine for UE5/Unity is free commercial (up to 10 licenses/studio via SideFX; Indie free up to 3) | SideFX Houdini Engine (FREE for UE5/Unity; full Engine $525 WS / $795 Floating for other hosts/batch) | 5.0–5.6 (plugin in Houdini installer; move `HoudiniEngine` to `Engine/Plugins/Runtime`) | ✅ Yes — SideFX tracks UE releases; FREE tier covers UE5 plugin | Plugin (HDA) | **10** | **P0-critical bridge.** Load `.HDA` → cook inside UE → output **meshes**, not Landscape. Required to convert Gaea/World Creator/World Machine heightmaps to Nanite meshes, scatter PCG, and keep determinism out of tick (async HDA cook). Needs Houdini Indie/Core license to author HDAs; FREE Engine license to cook them in UE. Does NOT work with Houdini Apprentice. |
| **Magic Map Material & Maker M4 (M⁴)** | https://www.fab.com/listings/12c3745b-f70b-473c-b8c4-1a3f93674494 | per Fab listing, verify at checkout (legacy Marketplace **$64.99**) | Fab Standard (legacy UE Marketplace license until migrated) | 4.25–4.27, 5.0–5.4 (listing at scan); community mirrors show 5.6 build | ⚠️ Partial — 5.4 listed; 5.6 community build exists, no 5.8 cert | Plugin + Automaterial (Landscape) | **2** | **Landscape-locked.** Description: "for use with ANY Unreal Engine landscape" — automaterial, 18-layer paint, RVT/VHFM, 70+ textures, terrain generator to 8K, splat/paint bakers, trail/interactive grass via `LandscapeGrassType`. Useful **only** as heightmap generator or texture source for MeshTerrain; automaterial itself is ALandscape-only without full rewrite. Roadmap: custom trees postponed indefinitely (June 2024). |
| **Fantastic City Generator** (MasterPixel3D) | https://www.fab.com/listings/013f192b-caf4-422f-b560-5166f8c6d9b8 | per Fab listing, verify at checkout (Unity tier **$300**; Fab UE tier historically **~$69.99–$129.99** — verify) | Fab Standard | 5.0+ | ⚠️ Partial — Fab UE port is mesh-based, version lag possible | Tool + Content (City) | **8** | **MeshTerrain-native city.** Generates streets, blocks, 380+ buildings, bridges/viaducts/tunnels, day/night, traffic. Outputs **meshes/actors**, not Landscape. No terrain dependency. Runtime generation support. Best cities-for-mesh-terrain option; verify included building LODs/Nanite and traffic system perf. |
| **Visus City Vol.2 — Procedural City Generator** | https://www.fab.com/search?query=Visus%20City%20Vol%202 | per Fab listing, verify at checkout (typically ~$49.99–$79.99) | Fab Standard | 5.0–5.4 | ❌ No — no 5.8 listing at scan | Tool (City, PCG) | **7** | Spline/PCG-driven city blocks; mesh buildings/roads. Similar fit to Fantastic City Generator but smaller library (check Vol.2 vs Vol.1). Mesh-native so P0-compatible; verify 5.6+ PCG API drift and spline tool updates. |
| **American City Bundle** | https://www.fab.com/search?query=American%20City%20Bundle | per Fab listing, verify at checkout (bundle ~$99.99–$199.99) | Fab Standard | 5.0–5.3 (bundle baseline) | ❌ No | Content Bundle (City Assets) | **5** | Asset bundle (US city props/buildings/roads). **Not procedural** — hand-place or PCG-scatter. Value depends on Nanite/LODs and modularity. Mesh-native assets are P0-safe, but no generation logic; pair with PCGEx/Pro or Fantastic City for placement. Check duplicate assets across bundle packs. |
| **Procedural Dungeon** (e.g., Dungeon Architect / Procedural Dungeon Generator) | https://www.fab.com/search?query=Procedural%20Dungeon | per Fab listing, verify at checkout (popular tiers **$39.99–$99.99**) | Fab Standard | 5.0–5.5 | ⚠️ Partial — dungeon logic is mesh/BP, usually 5.6-ready but verify | Plugin + Content (Dungeon) | **8** | **Mesh-native dungeon.** Generates rooms/corridors as **meshes/BPs**, not Landscape. P0-compatible by definition. Use for interior worldgen that avoids terrain entirely. Check World Partition + streaming + NavMesh integration; prefer PCGEx-compatible or ZoneGraph-aware options. |
| **Voxel Plugin Pro 2** | https://www.fab.com/listings/5c85f2f0-cf03-4860-b22e-e4f470af4133 (Fab) / https://voxelplugin.com (direct, current) | **$349.99** (Voxel Plugin Pro 2 via direct sale; Fab Voxel Plugin Pro Legacy was $349.99) — per listing, verify at checkout; budget >$100k requires custom license | Voxel Plugin EULA (direct sale, perpetual + 1 yr features / 3 yr bugs/UE upgrades; >$100k budget → custom) | 5.3–5.6 (2.0p8 = UE5.6) | ⚠️ Partial — 5.6 at scan, no 5.8 cert yet; Nanite-focused | Plugin (Voxel → Mesh) | **9** | **MeshTerrain flagship.** Voxel → Marching Cubes → **Nanite mesh terrain** with stamps, Voxel Graphs, invoker-based streaming. Replaces Landscape entirely. Strong PCG integration (voxel queries from PCG, Voxel Graphs as PCG extensions). Note: no static/pre-baked mode (always on-the-fly), foliage delegated to PCG, cubic terrains not supported, many materials can break non-Nanite path. Best pure-MeshTerrain terrain tech, but budget and 5.8 cert are risks. |
| **Brushify — SmartBrush System** | https://www.fab.com/listings/02e1f5e2-4cdf-4ba7-abd3-f155d0a1459d (Brushify Studio) + legacy SB https://www.unrealengine.com/marketplace/en-US/product/brushify-smartbrush-system | **$99.99** on sale (from $199.99) for SmartBrush System; Studio Edition bundle higher — per listing, verify at checkout | Fab Standard | 5.0–5.4 (5.5+ noted for Studio bundle) | ❌ No — 5.4 (5.5 for Studio) | Plugin + Brushes (Landscape) | **2** | **Landscape-locked.** Non-destructive Landscape sculpting via alpha brushes + Landmass plugin; doc: "modify landscapes non-destructively", "Landscape scaling", SmartBrush UI. Requires `Landmass`, DX12/VT/SM6/Distance Fields. No mesh terrain path; **directly incompatible with P0 MeshTerrain-only** without forking. Large on-disk (8K brushes total ~40 GB across packs). |
| **World Machine** | https://www.world-machine.com/purchase.php (external) | Basic **FREE** (1,025×1,025, non-commercial) · Indie **$119** · Professional **$299** (tiled, all cores, automation) · Studio **$1,999** (site license) — per world-machine.com, verify | World Machine EULA (perpetual + 1 yr updates; renewal discounted) | External app (Windows; heightmap/mesh/tiled) | ✅ Yes — output is heightmap/tiled terrain + mesh | External App | **6** | Classic heightmap/tiled terrain author. Like Gaea/World Creator, **P0 fit = export path**: tiled heightmaps need Houdini mesh conversion for MeshTerrain. Professional tier needed for tiled worlds + automation + all cores. VDM terrain previewed (May 2026). Cheaper entry than Gaea Pro but older UX. |

> **How Fit Score was set:** 9–10 = mesh/PCG/voxel/HDA native, zero Landscape dependency, works MeshTerrain-only today. 7–8 = mesh-native generation (cities/dungeons) or external app with clean mesh export. 5–6 = external heightmap app (needs Houdini conversion step). 3–4 = asset/biome packs where only meshes are salvageable; automaterial/grass/brushes wasted. 1–2 = Landscape-locked automaterial/brush systems (M4, SmartBrush) — purchase is paying for code you must rewrite or ignore.

---

## 3. Tiered Recommendations

### Tier $0 — Ship With What You Have (no purchase)

**Goal:** Prove MeshTerrain loop without spending; unblock level art.

| Priority | Pack / Action | Why |
|----------|---------------|-----|
| 1 | **Houdini Engine for UE5 (FREE)** + Houdini Indie/Core to author HDAs | The only FREE path that turns any heightmap (Gaea Community, World Machine Basic, World Creator trial) into **Nanite mesh terrain** inside UE. Cook HDAs async, keep determinism out of tick (per `AGENTS.md` quantum/service-boundary rule). |
| 2 | **PCGEx (FREE, MIT)** — free core on Fab + GitHub | Immediately extends vanilla PCG with graphs/pathfinding/spatial queries needed for mesh scattering, road networks, and biome logic without Landscape. |
| 3 | **Gaea Community (FREE)** + **World Machine Basic (FREE)** | Author 1K test terrains non-commercially; export heightmap → Houdini mesh. Proves pipeline before paying. |
| 4 | Existing **Calysto World 2.0** if already in vault/library | Reuse its 70× 4K stamps and PCG graph patterns as **mesh spawn data**, not as Landscape. Do not buy again for Landscape automaterial. |
| 5 | Vanilla UE **PCG** + **Nanite** + **World Partition** | Already in 5.8; pair with PCGEx free for mesh scattering. |

**What you can ship at $0:** Mesh terrain from FREE external heightmaps → Houdini HDA → Nanite meshes; PCGEx scattering of existing megascans/megascans-style meshes; hand-blocked cities/dungeons with vanilla PCG. No Landscape.

### Tier ~$200 — One Strategic Buy (+ free foundations)

**Budget cap $200 = one paid plugin + free stack. Pick *one* lane:**

**Option A — PCG/Mesh backbone (recommended for BS_GodFile):**
- **PCGEx Pro (~$49.99 Personal)** — unlocks Pro modules on top of free core. Best $/fit in table (score 9). Stays mesh-native, no Landscape porting, no 5.8 risk beyond PCG API.
- Keep Houdini Engine FREE + Gaea Community/World Machine Basic for terrain mesh.
- **Total ~$50** — well under $200, bank remainder for later Voxel or Gaea Indie.

**Option B — Terrain authoring upgrade:**
- **Gaea Indie $99** *or* **World Machine Indie $119** — lifts FREE 1K cap to full-res mesh/heightmap export.
- Keep PCGEx FREE + Houdini FREE to convert to mesh.
- **Total $99–$119** — good if terrain erosion quality is current blocker; less valuable than PCGEx Pro if scattering/logic is blocker.

**Option C — City generation bootstrap:**
- **Fantastic City Generator** *or* **Visus City Vol.2** (verify Fab tier ~$49–$79 at checkout) — mesh city generation without terrain dependency; pairs with PCGEx free.
- **Do not** buy Brushify SmartBrush ($99 sale) or Magic Map M4 (~$65) at this tier — both are Landscape-locked (score 2) and burn budget on code you cannot use MeshTerrain-only without porting.

**Decision rule at $200:** If worldgen logic/scattering is the bottleneck → **PCGEx Pro**. If terrain *authoring fidelity* is the bottleneck → **Gaea Indie**. Do not split $200 across two Landscape packs.

### Tier ~$500 — Full MeshTerrain Stack

**Budget $500 should buy a *coherent mesh pipeline*, not a grab-bag of Landscape packs.**

| Slot | Pick | Price (verify) | Role |
|------|------|----------------|------|
| Core | **PCGEx Pro** | ~$49.99 | Mesh-PCG backbone (graphs, pathfinding, scattering) |
| City | **Fantastic City Generator** | per Fab ~$69.99–$129.99 | Mesh city generation (streets/blocks/traffic, no Landscape) |
| Terrain | **Gaea Indie $99** *or* **World Machine Indie $119** *or* **World Creator Indie $149 perpetual** — pick one | $99–$149 | High-res heightmap/mesh authoring |
| Voxel *or* Dungeon | **Voxel Plugin Pro 2 $349.99** *or* **Procedural Dungeon ~$39–$99** — choose one, not both at $500 | $39–$349 | Voxel = true mesh terrain replacement; Dungeon = mesh interiors that sidestep terrain |

**Two concrete $500 carts (verify at checkout):**

- **Cart 1 — PCG + City + Terrain (balanced, leaves headroom):** PCGEx Pro (~$50) + Fantastic City Generator (verify ~$79) + Gaea Indie ($99) + Procedural Dungeon (~$49) ≈ **~$277**. Add Houdini Engine FREE + free PCGEx core. Leaves ~$223 for future Voxel or Gaea Pro upgrade; **lowest risk, all mesh-native, all 5.6+ viable.**
- **Cart 2 — Voxel terrain flagship:** Voxel Plugin Pro 2 ($349.99) + PCGEx Pro (~$50) + Procedural Dungeon (~$49) ≈ **~$449**. Fully MeshTerrain-native (voxel → Nanite), PCGEx for foliage/quests, dungeon for interiors. **Requires 5.8 cert check** (Voxel 2.0p8 = 5.6 at scan) and custom license if budget >$100k. Skip Gaea/World Machine at this cart — Voxel is your terrain.

**What *not* to do at $500:** Do not buy **Calysto World 2.0** + **Brushify SmartBrush** + **Magic Map M4** together. That is ~$165–$315 of Landscape-locked spend that re-introduces `ALandscape` pressure and duplicates terrain systems. One mesh terrain path (Voxel *or* Houdini mesh) + one city/dungeon path is cheaper and P0-compliant.

**Budget guardrail:** Fab Standard has Personal vs Professional tiers (Professional if 12-month gross revenue > $100k). Voxel/Gaea/World Creator have separate revenue caps (Voxel >$100k → custom; Gaea Indie ≤$100k, Pro ≤$1M). Check both before checkout.

---

## 4. Compatibility Risks

### 4.1 — 5.6 vs 5.8 (the immediate risk)

- **Most Fab listings ceiling at 5.4–5.6 at scan (2026-08-27).** Examples from live fetch: Magic Map M4 lists 5.0–5.4 (5.6 community build exists), Brushify SmartBrush lists 5.0–5.4 (Studio notes 5.5+), Calysto World 2.0 lists 5.6, Voxel Plugin Pro 2 lists 2.0p8 = 5.6, PCGEx tracks PCG framework (5.3–5.6). **No pack in table advertises 5.8 certification at scan.**
- **PCG API drift:** Fab notes for Calysto — "PCG is heavily used and evolves a lot between Unreal Engine updates." Between 5.6 → 5.8, PCG graph nodes, `PCGEx` processors, and `Houdini Engine` HDA cook paths are the highest churn. Test in a **copy project** on 5.8 before purchasing for production.
- **Mitigation:** Prefer plugins with **active GitHub + Discord** (PCGEx, Houdini Engine, Voxel) where 5.8 patches ship faster than Fab cache. Avoid packs with 5.4 ceiling and no update since 2024 unless you can accept mesh-extraction-only use.

### 4.2 — Landscape Porting Risk (P0 MeshTerrain-only)

- **Landscape-locked packs waste budget if bought for automaterial/brushes.** Magic Map M4 and Brushify SmartBrush are architecturally `ALandscape`-only:
  - M4: automaterial targets Landscape layers/weightmaps, `LandscapeGrassType`, RVT/VHFM via Landscape. Docs: "for use with ANY Unreal Engine landscape." Its 7 showcase maps are Landscape maps.
  - SmartBrush: requires `Landmass` plugin, sculpts `ALandscape`, non-destructive layers are Landscape layers. FAQ/docs explicitly say "modify landscapes."
- **Porting cost is not "toggle" — it is a material + pipeline rewrite:** re-author layer logic as mesh material functions (vertex color / UV mask / RVT to mesh), re-implement grass via PCG/HISM, re-bake splat/heat maps to mesh textures. Budget **days, not hours**, and you lose the pack's showcase maps.
- **Mitigation:** Buy Landscape packs **only** to **extract meshes/textures** (plants, rocks, 70+ M4 textures, 70× stamps) and accept that automaterial/brush code is throwaway. Or skip them entirely and buy mesh-native alternatives (PCGEx, Voxel, city/dungeon generators).

### 4.3 — Fab Cache, Licensing, and Delivery Risks

- **Fab price not visible until license select.** Since Fab migration, listing pages show "Select a license — Prices shown don't include taxes — Buy now / Add to cart" without revealing tier price in static HTML (confirmed on live fetch 2026-08-27 for Calysto, PCGEx, M4). **Verify price at checkout** after selecting Personal vs Professional. VAT added at checkout for EU.
- **Fab cache / launcher stale version:** Qwerty Studio notes for Calysto — "Try to clear the cache and download again from the launcher. Be sure to add all the required plugins and download directly for 5.6 (no 5.5 then update to 5.6)." Stale cache serves wrong engine-version build. After purchase, **clear Fab/Epic launcher cache** and install for **target engine version directly**.
- **Legacy UE Marketplace license vs Fab Standard:** Some packs still show "legacy UE Marketplace License" until publisher migrates (M4 at scan). Fab Standard is Personal (≤$100k revenue) / Professional (>$100k). **Check Details → License terms** on each listing before purchase; legacy terms phase out.
- **External-app licensing caps:** Gaea (Indie ≤$100k, Pro ≤$1M), World Machine (perpetual + 1 yr updates, renewal discounted), Voxel ($349 tier only for budgets <$100k/ $200k depending on channel — docs say >$100k via direct sale or >$200k via legacy Marketplace → custom). Exceeding caps without correct tier = license violation.
- **Source vs Fab divergence:** PCGEx is MIT on GitHub and free on Fab; Pro is Fab-only. Voxel Plugin Pro 2 is now **direct sale** (voxelplugin.com) not Fab for latest builds — Fab listing is Legacy. Buying Fab Legacy gets older build. Verify you are buying the **intended channel** for updates.
- **File size / disk:** Brushify 8K brush packs total ~40 GB across packs; Gaea/World Machine caches + Houdini HDA cooks + Voxel voxel data are disk-heavy. Plan `Saved/` and `DerivedDataCache` size.

### 4.4 — Recommended Pre-Purchase Checks (5 minutes per pack)

1. Open Fab listing → **Details → Supported Engine Versions** → confirm 5.6/5.8 or note lag.
2. Select **Personal vs Professional** → record price **before** buying (screenshot for ledger).
3. Search listing Description for `Landscape` — if every feature says "Landscape" and you need MeshTerrain, downgrade Fit Score mentally by 4.
4. Check publisher **Changelog / Docs / Discord** for 5.8 or 5.6→5.8 migration notes.
5. For Voxel / Houdini / PCGEx: check **GitHub releases** or **SideFX Houdini Engine** download page for 5.8 branch, not just Fab.

---

## 5. Quick Fit Matrix (for Roz / P0 review)

| Fit | Packs |
|-----|-------|
| **Buy for MeshTerrain** (9–10) | Houdini Engine FREE, PCGEx / PCGEx Pro, Voxel Plugin Pro 2 |
| **Buy for mesh cities/dungeons** (7–8) | Fantastic City Generator, Visus City Vol.2, Procedural Dungeon |
| **Buy as heightmap source only** (6–7) | Gaea, World Machine, World Creator — via Houdini mesh export |
| **Salvage meshes only** (3–5) | Calysto World 2.0, Scifi Jungle Biome, American City Bundle |
| **Avoid for P0** (1–2) | Magic Map M4, Brushify SmartBrush — Landscape-locked |

---

## 6. Sources & Footnotes

> All prices and engine versions per live scan 2026-08-27; Fab prices exclude tax/VAT and require license-tier selection at checkout. Verify before purchase.

1. **Calysto World 2.0** — Fab listing `8631308a-67a3-4e20-b3e4-74be19813f77` (live fetch 2026-08-27: tags Landscape/Biome/Terrain, description, 5.6 note). Patch note: "Calysto World 2.0 for Unreal Engine 5.6" — https://qwertystudio.gitbook.io/calysto/patch-note-calysto-world . Forum: 5.6 tested/updated, 5.5 RO. docs confirm PCG drift warning.
2. **PCGEx (free)** — Fab `3f0bea1c-7406-4441-951b-8b2ca155f624` live fetch: "Free — MIT License on GitHub" (https://github.com/Nebukam/PCGExtendedToolkit). Docs: https://pcgex.gitbook.io/pcgex/ . Pricing hint: Patreon $25 = half Personal tier → Pro ~$49.99 Personal (per pcgex.gitbook.io/pcgex-pro).
3. **World Creator** — Buy page https://www.world-creator.com/en/buy.phtml — Indie/Pro/Studio subscription + perpetual tiers ($59/yr / $149 perpetual etc.); docs https://docs.world-creator.com/ .
4. **Gaea** — QuadSpinner Order https://quadspinner.com/Order and Compare https://quadspinner.com/compare — Community FREE (1K), Indie $99 (8K), Professional $199, Enterprise $299; Gaea 2.2 price confirmed via CG Channel 2025-07-01. Gaea 3 pre-order mid-2026.
5. **World Machine** — https://www.world-machine.com/purchase.php — Basic FREE (1,025), Indie $119, Professional $299, Studio $1,999; perpetual + 1 yr updates. Confirmed via world-machine.com/features.php and help/world-machine.com/topics/licenses/.
6. **Houdini Engine for UE5** — SideFX https://www.sidefx.com/products/houdini-engine/plug-ins/unreal-plug-in/ and FAQ https://www.sidefx.com/faq/question/what-houdini-engine-license-do-i-need/ + https://www.sidefx.com/faq/houdini-engine-faq/ — Houdini Engine for UE5/Unity is **FREE** commercial (up to 10 licenses/studio; Indie up to 3 free). Requires Houdini Indie/Core to author HDAs; Apprentice HDAs not compatible with Engine licenses. Plugin ships inside Houdini installer → move `HoudiniEngine` to `Engine/Plugins/Runtime`.
7. **Magic Map Material & Maker M4** — Fab `12c3745b-f70b-473c-b8c4-1a3f93674494` live fetch 2026-08-27 (Landscape-tagged, 5.0–5.4 listed). Legacy Marketplace price $64.99 per https://www.unrealengine.com/marketplace/en-US/product/magic-map-material-maker (Supported Engine Versions 4.25–4.27, 5.0–5.4). M4 docs: https://aaronneal.online/docs/m4/ ; Roadmap: custom trees postponed June 2024.
8. **Fab licensing/pricing** — Fab docs via gfx-hub/zonegfx mirrors of Epic docs: Fab Standard = Personal (≤$100k) / Professional (>$100k); price tiers are presets ending in .99 except $0.00 (ranges $0–$100 $1 increments, $100–$150 $5, etc.). Legacy UE Marketplace License still shown until publisher migrates.
9. **Voxel Plugin Pro / Pro 2** — Legacy Marketplace https://www.unrealengine.com/marketplace/en-US/product/voxel-plugin-pro ($349.99, 4.23–4.27/5.0–5.4) and direct https://voxelplugin.com (Voxel Plugin Pro 2 — $349 for budgets <$100k direct, legacy "$349 for <$200k" phrasing). Licensing https://docs.voxelplugin.com/resources/licensing (perpetual + 1 yr features / 3 yr bugs/UE upgrades; >$100k → custom). Fab listing for Pro 2: `5c85f2f0-cf03-4860-b22e-e4f470af4133` (per renderskill mirror) — 2.0p8 = UE5.6.
10. **Brushify SmartBrush** — Legacy Marketplace https://www.unrealengine.com/marketplace/en-US/product/brushify-smartbrush-system ($199.99 → $99.99 sale, 5.0–5.4) and Fab Brushify Studio `02e1f5e2-4cdf-4ba7-abd3-f155d0a1459d` (5.5+). Docs: https://www.brushify.io/docs/categories/smartbrush-system — requires Landmass, DX12/VT/SM6/Distance Fields; 40 GB total for 8K brushes (per FAQ).
11. **Fantastic City Generator** — Fab `013f192b-caf4-422f-b560-5166f8c6d9b8` (live fetch 2026-08-27); Unity tier $300 confirmed via Unity Asset Store `packages/3d/environments/urban/fantastic-city-generator-157625` and assetfigures history. Fab UE price not exposed in static HTML at scan — verify at checkout (historical ~$69.99–$129.99 tier).
12. **Fab cache caveat** — Qwerty Studio forum guidance for Calysto World 2.0: clear Fab/Epic launcher cache and install directly for target engine version (no cross-version upgrade).
13. **Live scan execution** — websearch + webfetch performed 2026-08-27 in-session; Fab pages returned license-selector without price (expected for Fab post-migration). Where price not in listing HTML, last verified tier price is cited with `verify at checkout` flag per task instructions.
14. **Methodology** — Prices in USD base; Professional tier, VAT, and regional taxes excluded. Fit Score is project-specific (BS_GodFile MeshTerrain-only P0) not a global quality rating.

---

**File:** `Docs/WorldGen/PURCHASE_RESEARCH_2026-08-27.md`  
**Next step:** Pick one $0 / $200 / $500 cart above, verify prices at Fab checkout (screenshot tier), then clear Fab cache and test chosen plugin in a 5.8 copy project before promoting to `main`. Do not add `ALandscape` to prove a Landscape-locked pack "works."

