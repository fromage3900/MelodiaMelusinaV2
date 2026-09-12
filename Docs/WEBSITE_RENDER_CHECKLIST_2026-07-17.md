# Website Render Checklist — 2026-07-17 (Webfront audit)

Site: `BS_GodFile/my-site-clean` (Wix) → live at `https://fromage3900.github.io/my-site/` (GitHub Pages, all key assets 200 OK as of today).

## Audit method
- All 30 slots in `content/site-plates.json` resolve to existing, non-tiny files — plates healthy.
- All `wix/*.js` texture manifests (`melodia-game-ui`, 51 files) present.
- All 13 material-loops + 4 landscape-loops `.webm` present.
- Full image-content scan (547 images): flagged near-uniform (blank) files.
- Cross-checked every `generated/*.json` manifest for referenced-but-missing files.

## FILLED today (no UE needed)
- [x] 12 material-loop posters `generated/assets/material-loops/MI_*.png` (extracted mid-loop frame from each webm)
- [x] 4 landscape posters `generated/assets/landscape-loops/WP_*_terrain.png` (same method)

## UE render batch — DONE 2026-07-17 (evening session, Monolith + L_MaterialPreview_Studio)
All captured at 1600×2000 in the material-preview studio (3-point warm/cool/pink rig, ivory toon `M_SakuraPetal` where SDF instances read too dark), EXR → Reinhard+gamma PNG.
- [x] `ornaments/column_capital_komikaze_macro.png` — SM_Orn_ColumnCapital + MI_SDF_IvoryScrollwork, below-front profile
- [x] `ornaments/vault_ribs_komikaze_macro.png` — SM_Orn_VaultRibs, ivory toon
- [x] `props/magical_wand_komikaze_macro.png` — SM_Retopo_wand, ivory toon, diagonal
- [x] `props/sakura_petal_komikaze_macro.png` — SM_SakuraPetal (812-tri import), ivory toon
- [x] `signature/lissajous_komikaze_macro.png` — GeometryScript-baked SM_Math_LissajousRail_3_2_1 (baked today via generate_math_structures.build_structure)
- [x] `signature/trefoil_komikaze_macro.png` — GeometryScript-baked SM_Math_TrefoilKnot
- [x] `character/fromage_art_cockatiel_mark.png` — composited from healthy `brand/fromage_art_cockatiel.png` (was fully black)
- [x] Verified already-healthy (no work needed): all 5 cross komikaze slots, all 7 sculpt melodytoken slots, corbel macro, wireframe greys

## OPEN — needs UE renders (editor)
(none remaining from the original list)

## OPEN — decisions for owner
- `renders_config.json`: 28 refs to `Saved/Portfolio/Renders/*.png` that do not exist on disk (stale or never rendered). Regenerate the hero/breakdown level renders in UE, or prune the config?
- `blender_portfolio_intake.json`: 78 komikaze slots total missing — Blender EEVEE pipeline territory; UE can cover the ornament/prop subset, character sculpts stay Blender.
- `local_asset_inventory.json`: 42 `_AssetLibrary` texture refs missing — library index, not site-visible; likely moved during F: backup.
- `geometry_nodes_pipelines.json`: `pcg-heatmap.png` exists at `generated/assets/portfolio-scan/pcg-heatmap.png` — path fix only.
- Deploy: `_github_deploy` is EMPTY and `deploy/sync_site_to_github.ps1` is deleted in the working tree — the live site is stale since ~07-13. Restore the sync script and republish after renders land.

## Not broken (verified today, don't re-fix)
- Sakura Niagara suite: `M_SakuraPetal` procedural toon material + `SM_SakuraPetal` mesh healthy; NS_SakuraPetals_v2 renderer mesh-true (artist-loop).
- All 30 site plates, all UI atlas textures, all loop videos.
