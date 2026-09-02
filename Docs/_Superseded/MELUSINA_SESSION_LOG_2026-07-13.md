# Melusina session log — 2026-07-13

**Canonical stage:** `KitbashExport/Melodia_Portfolio_Stage_v10.blend`  
**Render runbook:** [`MELUSINA_RENDER_SESSION_2026-07-13.md`](MELUSINA_RENDER_SESSION_2026-07-13.md)

## Stage v9 note (2026-07-14)

- Old hair restored for soft physics (`Hair Strand.002/.004/.007` + SHP).
- **FX_Hero** = dressing only (sparkles/veil/jewelry/ribbon) — quiet for beauty (`hide_render` / `beauty_clean`).
- Hair tip drip: **LiquiFeel** proxies in `Melusina_HairDrip` via `Tools/setup_melusina_liquifeel_hair_drip.py` (not under FX_Hero; elixir glass untouched; FLIP `Melusina_WaterFX` paused).
- Inventory: `Saved/Audit/stage_v9_fx_hero_hair_inventory.json`

## Changes today

### FLIP / WaterFX
- Reset + rebake Melusina hair domain cache at res **80**
- Extended custom range to frames **1–240** (resume from existing 1–24)
- Cache: `KitbashExport/flip_cache_melusina_waterhair/` — 240 finished markers *(disk later emptied — 0 `.bobj` as of 2026-07-14)*

### FLIP / LiquiFeel deep review (2026-07-14) — little hair drip
- **Lanes:** hair look = `Water (Advance).001` on `Hair Strand.*`; FLIP = `Melusina_WaterFX` droplets near tips; LiquiFeel = `Asset_melusina_elixir` glass only (GN on `melusina_ElixirGlass`, **not** hair).
- **Why sim “didn’t work on hair”:** domain bbox sat at world Z ~**2.7–4.8** while tips are ~**0.7–1.9**; drip emitter was **outside** the domain; WaterFX `hide_render=True`; cache had **0** `.bobj` frames; drip was `TYPE_FLUID` without `is_inflow`.
- **Tune tool:** `Tools/tune_melusina_hair_drip.py` — shifts domain onto hair, tiny `TYPE_INFLOW` at `Hair Strand.002` tip, disables sheet, WaterFX visible, bake window 1–96 @ res 72.
- Audit: `Saved/Audit/melusina_flip_liquifeel_review_2026-07-14.json` + `melusina_hair_drip_tune.json`
- Sidecar (tuned, not yet canonical): `Saved/Audit/Melodia_Stage_v7_hair_drip_tuned.blend` — **rebake still required** on live Stage v7 after running the tool in GUI.

### Eyes / iris

**Live at close (do not reinterpret):**

| Mesh | Mat | Maps |
|------|-----|------|
| `R_Iris.001` | `Material.022` | **`M_Iris_Back_*`** |
| `R_Iris.002` | `Material.023` + `Iris.002` | **`Material.020_*`** |

- `Material.020_*` = Blender-UV front set. `M_Iris_Back_*` = back disc only. Never put `M_Iris_front_*` as primary on these meshes.
- Scene4 harvest of `L_IrisBack`/`R_IrisFront` was undone (user request).
- Agent repeatedly global-rewired both discs by collapsing “UV match” vs “iris back” into one rule — see postmortem [`MELUSINA_IRIS_POSTMORTEM_2026-07-13.md`](MELUSINA_IRIS_POSTMORTEM_2026-07-13.md).

### Grease Pencil (Scene4 harvest)
- Source: Scene4 `GREASE` (`GPencil`–`.007`, `Pencil` stubs)
- Keepers (strokes > 0) → `FX_Grease_Scene4` / `FX_GP_Scene4_GP*`
- Empty Pencil stubs + `GPencil.005` removed
- Collection **render off by default** (opt-in flourish)
- Parasitic append deps purged (duplicate `character_rig.001`, Scene4 WGT/cs widgets, Starlight Sun)
- Audit: `Saved/Audit/workingmelusinascene4_harvest_2026-07-13.json`
- User Library sync earlier: `Assets/GreasePencil/` + Melodia GP library

### Soft physics / hair
- Cloth on wardrobe: Pin ~top 42%, gravity weight **0.25** *(superseded by stable_wardrobe below)*
- Swingy tip sway + SHP wind restored on `SHP_Armature (Hair Strand.*)`
- **Hair Strand.004:** assigned 1344 unweighted verts to nearest `DEF_hair_bbone.*` → **0 unweighted**

### Stable wardrobe cloth (Nikki-simple pass)
- Removed `SimplyCollision` from `Melusina_Shawl` (cloth + self-collider burst)
- `Melusina_Skirt`: dual-island Pin — main ~23k island top rim + 616-island attach (**1426** pinned / ~6%)
- Soft low gravity (~0.18–0.2), no self-collision; body `Melusina` sole collider (outer 0.012)
- `Melusina_FrontPanel` Pin trimmed ~30%; panels/bow soft cloth
- Accordion Cloth muted (`show_viewport`/`show_render` off) while object stays hidden
- Caches freed; settle scrub frames 1–24; stage saved
- Tool default preset `stable_wardrobe`: `Tools/setup_melusina_clothes_soft_physics.py`
- Audit: `Saved/Audit/melusina_cloth_stable_2026-07-13.json`

### Textures / paths
- Exported packed hat/boot maps to `Imports/MelusinaTextures/`
- Cleared `ACTUALCOMPILED…` path remotes (relink + pack)
- Scene4 IRISFRONT/IRISBACK leftover images remapped to MelusinaTextures

### World / sky
- No prebuilt Day+Night Mix world in Scene4/FinalUERig (only `Sky Night` datablock; Day+Night **Skydome** groups present)
- Built **`W_Melodia_FadeDayNight`**: Fade `Day Skydome` ↔ `Night Skydome`, **Night Mix** default 0.72
- Fallback datablock kept: `W_MelodiaStudio_Fade`
- Tool: `Tools/setup_melusina_fade_daynight_sky.py`

### Cleanup for render
- Disabled broken Faceit/null armature mods on brows + `Melusina_Bow.001`
- Hidden legacy accordion skirt viewport+render
- Floor pin verified: `Studio_FloorCard` Z ≈ -0.2935

### Goo scan
- No Blender 5.1 Goo Physics addon; incomplete Goo Engine 4.4 fork only — see `Saved/Audit/goo_physics_scan_2026-07-13.json`

## Site remount queue (later — do not wire tonight)

Status after Melusina fine-tune + tonight’s plates:

1. **Do not remount** solid mauve blanks: `melusina_beauty_nikki_001`, `melusina_beauty_jewelry_001`, `melusina_low_nikki_001`, `melusina_water_splash_001`, `melusina_glam_audvis_001` as heroes.
2. Keep bangs / hero SSOT on `melusina_beauty_void_iri.png` / established nikki refs until real dated plates land.
3. After shoot: write dated files into `my-site-clean/generated/assets/character/` then update passport + `melodia-stage-character.html` / editorial refs.
4. Refresh `generated/passports/melusina_passport.*` via `Tools/melodia_asset_passport.py` when plates exist.
5. PostToFigma still gated on `FIGMA_API_TOKEN`.
6. Landscape / material loop remounts are a separate track (already interim on site).

### Site prep done (ready for post-nap beauty plates)

- Passport JSON/HTML → **Stage v7 · EEVEE**; Capture still interim void/iri until dated beauty lands
- Stage / home / hub copy: no false “bangs” claim; Stage label **v7**
- Stage strip: deduped Front · Nikki; silhouette added once
- Melusina `heroLeadImage` locked so intake cannot swap to cross plate
- Remount scout: `Tools/remount_melusina_plates.py --scan` / `--apply` / `--passport`
- Render runbook polished: cloth settle 1–24, supply checklist, remount path
- After F12: drop `melusina_beauty_nikki_20260713_01.png` into `generated/assets/character/` then `--apply --passport`

### Sir Melodious rig restored on stage

- Was mesh-only (7 unweighted props); now **`SirMelodious_rig`** (408 bones) + Retopo skins from `sirmelodiousalmostdone07.blend`
- Collection `Asset_sirmelodious` under `Characters` — **viewport on / render off** (companion opt-in)
- CS widgets in `Asset_sirmelodious_cs` (hidden); pose smoke OK on `c_root_master.x`
- Tool: `Tools/append_sirmelodious_rig_stage.py`
- Audit: `Saved/Audit/sirmelodious_rig_stage_v7_2026-07-13.json`
- Melusina `character_rig` intact; FloorCard untouched

### Sir Melodious ARP → UE (in progress)

- Deep review OK: ARP 4.x updated, 11 skinned export meshes, feathers present, x100 units for UE
- Export tool: `Tools/export_sirmelodious_arp_ue.py` (Unreal / UNIVERSAL / rename OFF)
- Target FBX: `Exports/SirMelodious/SK_SirMelodious.fbx` — **not written yet** (ARP export hung automated session)
- UE importer updated to prefer that FBX: `Content/Python/import_sirmelodious.py`
- **Do this in live Stage v7 GUI:** select bird rig → run export script (or ARP Export flash) → then UE `import_sirmelodious.py`

## Audits written today

| File | Purpose |
|------|---------|
| `Saved/Audit/portfolio_shoot_2026-07-13.json` | Earlier shoot |
| `Saved/Audit/melusina_iris_relink_2026-07-13.json` | Iris path fix |
| `Saved/Audit/melusina_iris_sim_fix_2026-07-13.json` | Sim + iris |
| `Saved/Audit/melusina_finalize_review_2026-07-13.json` | Pre-render review |
| `Saved/Audit/melusina_fade_daynight_sky_2026-07-13.json` | Day/night world |
| `Saved/Audit/workingmelusinascene4_harvest_2026-07-13.json` | Scene4 GP/iris harvest |
| `Saved/Audit/goo_physics_scan_2026-07-13.json` | Goo scan |
| `Saved/Audit/melusina_cloth_stable_2026-07-13.json` | Stable wardrobe cloth / dual-island Pin |

## Out of scope completed / deferred

- Site HTML remount — **deferred** (queue above)
- WorkingMelusinaScene5 diff — deferred
- UE iris re-export — deferred
