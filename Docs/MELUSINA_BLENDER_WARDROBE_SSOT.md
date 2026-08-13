# Melusina Blender — Wardrobe + Stage SSOT

**Updated:** 2026-08-12  
**Start here:** [`Docs/BLENDER_MELODIA_COCKPIT.md`](BLENDER_MELODIA_COCKPIT.md) — live stage, ports, Studio Health, do-not-save.  
**Purpose:** One page that answers “which blend / which lane?” and how Melusina is actually shaded and dressed on the live portfolio stage — without polluting ornament buses.

**Live portfolio stage (pin):** `G:\EnvironmentPortfolio\BS_GodFile\Melodia_Portfolio_Stage_v22_ZenRebuild_WIP.blend`  
Historical: `KitbashExport/Melodia_Portfolio_Stage_v10.blend` (retired as the Lane A pin). v4 plate scripts are historical. After restart: **N → BlenderMCP → Connect** (port **9876**). Do not save the live stage without `MELODIA_ALLOW_STAGE_SAVE=1`.

## Four lanes (do not mix)

| Lane | Canonical artifact | Purpose | Not for |
|------|-------------------|---------|---------|
| **A — Portfolio stage** | `G:\EnvironmentPortfolio\BS_GodFile\Melodia_Portfolio_Stage_v22_ZenRebuild_WIP.blend` + cockpit. Historical: `KitbashExport/Melodia_Portfolio_Stage_v10.blend` + `STAGE_README_v4.md` | Melusina beauty/cine stills, FX tiers, passports, site plates | Game mesh SKU export |
| **B — Ornament factory** | `KitbashExport/OrnamentalMeshes/SM_Orn_*.fbx` | Procedural ornaments → UE `/Game/EnvSandbox/Meshes/Ornament/` | Character clothes |
| **C — Live Link** | `Docs/BLENDER_LIVELINK.md` (port **9876**) | Interactive scene sync → `/Game/LiveLink/` | Ornament SKU or wardrobe SSOT |
| **D — Character / wardrobe** | External `G:\MelodiaMelusina\MelusinaFinalRig\` + this doc | Rig/skin; stage **links** Melusina; new outfits → `Wardrobe_*` + `Exports/MelusinaClothes/` | Live Link dumps, `SM_Orn_*` |

Cockpit (start-here): [`Docs/BLENDER_MELODIA_COCKPIT.md`](BLENDER_MELODIA_COCKPIT.md).

## Pins (do not silently swap)

| Pin | Value | Notes |
|-----|-------|-------|
| Stage file | **`Melodia_Portfolio_Stage_v22_ZenRebuild_WIP.blend`** | Live pin. v10 (soft physics + LiquiFeel tip drip restore) and v4–v9 are historical — do not silently swap back |
| Rig source (stage link) | **`G:\MelodiaMelusina\MelusinaFinalRig\FinalUERig43.blend`** | Keep until `SKM_character_rig.fbx` is proven to supersede |
| UE body | `/Game/Melodia/Characters/Melusina/SK_Melusina` | Clothes today = **material slots on one mesh**, not modular outfits |
| UE hair | `/Game/Melodia/Characters/Melusina/Hair/SK_MelusinaHair` | Separate import path |
| Hair material | **`Water (Advance).001`** | Keep this material identity. It **already embeds Komikaze** (`Noise Texture (Komikaze)`, `Linear Gradient (Halftone)`, PBR/Fresnel). Do **not** replace strands with FLIP/LiquiFeel meshes. Do **not** full-append a catalog NPR mat over hair. |
| Clothes / body NPR | **Hybrid PBR + Komikaze** | Principled + maps + Komikaze NPR group (`Linear Gradient (Halftone)` / Gradual Shading family) → Shader to RGB → Mix ~0.5. SSOT example: **`SHAWL.001`**. |
| Floor / Ground | **`Studio_FloorCard`** world Z ≈ **-0.2935** | **Never move.** Large boots intentionally sit into / through the floor for Infold-style grounded contact. |
| FLIP | `Melusina_WaterFX` | Splash only — not hair replacement; beauty default off; cache **1–240** |
| LiquiFeel | Elixir glass + tip drip proxies | Glass: `melusina_ElixirGlass`. Hair drip: `Melusina_HairDrip` tip proxies only — **never** replace strands or put under `FX_Hero` |
| Stage world | **`W_Melodia_FadeDayNight`** (Fade Day↔Night mix) | Rebuild: `Tools/setup_melusina_fade_daynight_sky.py`; fallback `W_MelodiaStudio_Fade` |
| Eyes | Both `R_Iris.001` + `R_Iris.002` → **`Material.020_*`** | UV-matched Blender set. `M_Iris_front/Back_*` = UE only. See `Docs/MELUSINA_IRIS_POSTMORTEM_2026-07-13.md` |
| MCP vs Live Link | MCP **9876** (N → BlenderMCP → Connect) · Live Link **9876** (Studio **Live Bridge → Start Server** — different button) | Same port, different Studio buttons. **9877 / 9317** are legacy — do not use |

Live inventory of hybrid mats: [`Saved/Audit/melusina_komikaze_hybrid_inventory.json`](../Saved/Audit/melusina_komikaze_hybrid_inventory.json).

## Melusina shading lanes (Komikaze)

Two different workflows — do not confuse them.

### Lane A — Character hybrid (how Melusina actually looks)

Used on **hair, body, shawl, skirt, sleeves, boots, hat, etc.**

1. Keep Principled (or Water Advance shell) + authored textures.  
2. Feed albedo / look info into a **Komikaze NPR group** (live: `Linear Gradient (Halftone).*`).  
3. NPR → **Shader to RGB** → **Mix Shader ~0.5** with the PBR/water branch.  
4. Reference clothes: **`SHAWL.001`**. Reference hair: **`Water (Advance).001`** (Komikaze groups inside the water stack + outline slots on some strands).

**Mimic for later outfit mats:** clone this graph. Do **not** run set-look full material replace on Melusina.

### Lane B — Set / prop full NPR

Used on **`Studio_FloorCard`**, backdrop (when visible), `Set_Diorama`, kitbash prop plates.

- Append whole Komikaze catalog materials via [`Tools/komikaze_stage_looks.py`](../Tools/komikaze_stage_looks.py) / [`Tools/batch_eevee_komikaze_portfolio.py`](../Tools/batch_eevee_komikaze_portfolio.py).  
- Scripts **skip** Melusina objects so they do not wipe Lane A hybrids. That skip is “don’t full-replace character,” not “character has no Komikaze.”

## Naming contracts

| Prefix / collection | Use |
|---------------------|-----|
| `Asset_melusina` | Hero body + `character_rig` + hair (linked) |
| `Wardrobe_Base` | Current on-body outfit meshes (inventory / review; hide render unless reviewing) |
| `Wardrobe_<OutfitId>` | New clothes pack under `Review_Queue` (camera toggle) |
| `Wardrobe_Accessories` | Hat / wings / boots when reintroduced |
| `outfit_<id>_*` | New clothing mesh objects |
| `M_Outfit_<id>_*` | Outfit materials — prefer Lane A hybrid; never destroy `Water (Advance).001` hair |
| `FX_Hero` | Stage dressing only (veil / sparkles / ribbon) — **not** wardrobe meshes |
| `Studio` / `Studio_FloorCard` | Cyclorama floor — **transform locked** (boot contact) |
| `Exports/MelusinaClothes/<OutfitId>/` | Skinned FBX + sidecar JSON |
| `KitbashExport/OrnamentalMeshes/` | Ornaments only |
| `/Game/LiveLink/` | Scratch only |

## What is on the rig today (clothes reality)

**Inventory** (`Saved/Audit/melusina_stage_mesh_inventory.json`): `Asset_melusina` has linked rig meshes; `Wardrobe_*` for new packs; `FX_Hero` stage dressing.

| Class | Notes |
|-------|-------|
| body | `Melusina` + `SBW_MELUSINA.*` with Linear Gradient (Halftone) hybrids |
| hair | `Hair Strand.*` **MESH** (not Curves) — `Water (Advance).001` with Komikaze groups inside; soft wind via companion `SHP_Armature (Hair Strand.*)` + Swingy (`bUseWind`). SHP curve Dynamics UI does not apply to these mesh strands. |
| clothes | Named wardrobe meshes (`Melusina_Shawl` / `Melusina_Skirt` / panels / sleeve / bow / gloves) with hybrid mats (`SHAWL.001`, `SKIRT.003`, …) |
| boots | `Retopo_boot 2.*` — large contact into `Studio_FloorCard`; do not raise floor |

**Rule:** do **not** re-parent baked dress / `Melusina_Skirt` into `Wardrobe_Base`. New pieces → `Wardrobe_<OutfitId>`.

## Operator recipes

Headless commands below still name `KitbashExport/Melodia_Portfolio_Stage_v4.blend` (historical). Live portfolio stage is **v22** — retarget beauty/inventory to v22 in a live 5.2 session; do not treat v4 as the pin. Stage save still requires `MELODIA_ALLOW_STAGE_SAVE=1`.

### Inventory (read-only)

```text
blender KitbashExport/Melodia_Portfolio_Stage_v4.blend -b -P Tools/inventory_melusina_stage_meshes.py -- --ensure-wardrobe --save
```

### Stage still (Melusina)

```text
blender KitbashExport/Melodia_Portfolio_Stage_v4.blend -b -P Tools/melodia_stage_shot.py -- --preset beauty --lights nikki --subject melusina
```

Uses whatever render engine/samples are saved in the `.blend` (EEVEE on live stage). Scripts must not rewrite engine settings.

### Stage still (outfit review)

```text
blender KitbashExport/Melodia_Portfolio_Stage_v4.blend -b -P Tools/melodia_stage_shot.py -- --preset beauty --lights nikki --subject outfit:<OutfitId>
```

### Import outfit pack onto stage

```text
blender KitbashExport/Melodia_Portfolio_Stage_v4.blend -b -P Tools/populate_stage_review_queue.py -- --outfit <path_to.fbx_or.blend> --outfit-id <OutfitId>
```

### Export wardrobe for UE

```text
blender KitbashExport/Melodia_Portfolio_Stage_v4.blend -b -P Tools/export_melusina_wardrobe.py -- --outfit-id <OutfitId>
```

Writes `Exports/MelusinaClothes/<OutfitId>/SK_Melusina_<OutfitId>.fbx` + sidecar JSON.

### UE landing

`/Game/Melodia/Characters/Melusina/Outfits/<OutfitId>/` — separate from ornament `import_ornament_fbx.py`. Body-slot textures stay on [`import_melusina_textures.py`](../Content/Python/import_melusina_textures.py).

## Related docs

- Stage toggles: [`KitbashExport/STAGE_README_v4.md`](../KitbashExport/STAGE_README_v4.md)
- Cockpit: [`BLENDER_MELODIA_COCKPIT.md`](BLENDER_MELODIA_COCKPIT.md)
- Pipeline gaps: [`BLENDER_PIPELINE_REVIEW_2026-07-11.md`](BLENDER_PIPELINE_REVIEW_2026-07-11.md)
- Textures: [`MELUSINA_TEXTURE_IMPORT_PLAN.md`](MELUSINA_TEXTURE_IMPORT_PLAN.md)
- Live Link: [`BLENDER_LIVELINK.md`](BLENDER_LIVELINK.md)
