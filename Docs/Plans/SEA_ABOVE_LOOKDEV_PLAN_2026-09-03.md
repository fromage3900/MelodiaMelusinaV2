# Sea Above — UPDATED Lookdev Plan (2026-09-03, post-crash)

**Status: ALL MUTATIONS SAVED TO DISK. No live editor to verify visually.**
Restart `Launch_Editor.bat`, then execute this plan top-to-bottom.

## Disk-verified state (from 19:42 save)

- `LV_SeaAbove_Prototype.umap` mtime 19:42 (saved)
- 299 external actor files on disk (136 SA_HM + 83 PCG ribbon + 27 PCG garden + 55 SM_ATL + triggers)
- Expected in-level on restart:
  - `PPV_NikkiDream` (PostProcessVolume, unbounded)
  - `Key_TwilightPink` (DirectionalLight, warm, upper-left)
  - `Rim_CoolBlue` (DirectionalLight, cool, back-right)
  - `Fog_SeaDepth` (ExponentialHeightFog, density 0.02)
  - `Cam_GoldenSpiral_00..03` (CineCameraActor x4, golden spiral path)
  - `PCG_Ribbon_XylophoneTrail` + `PCG_Ribbon_GardenBeat_BellTree`
  - 24x PCGHeroMusicNode (2 tiers: -45.3k, -14.6k)

## Step 1 — Restart & Verify (editor lane)

```
Launch_Editor.bat
-> Window > World Outliner -> search: PPV, Key, Rim, Fog, Cam, SA_HM, PCG
-> Confirm all actors present
```

## Step 2 — PPV Blendables (UI — cannot be set via Python)

Select `PPV_NikkiDream` > Settings > Blendables > Add:
| Material | Weight |
|---|---|
| `MI_MelodiaInk_PortfolioHero` | 1.0 |
| `MI_MeluColorGrade_PortfolioHero` | 0.69 |
| `MI_StarryNight_Hero` | 1.0 |

Save level.

## Step 3 — Lighting Polish (editor lane)

- `Key_TwilightPink`: intensity 3.5, color (255,180,200), rotation (-45,30,0)
- `Rim_CoolBlue`: intensity 2.0, color (150,180,255), rotation (-30,-150,0)
- `Fog_SeaDepth`: density 0.02, tint (0.4,0.5,0.7) — set in UI if Python default stuck
- Verify the twilight rim separates Melusina's silhouette from the blue background

## Step 4 — Demo Reel Capture (headless)

```batch
set PORTFOLIO_CAPTURE_LEVEL=/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/LV_SeaAbove_Prototype
"C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe" ^
  "C:\EnvironmentPortfolio\BS_GodFile\BS_GodFile.uproject" ^
  -ExecutePythonScript="C:\EnvironmentPortfolio\BS_GodFile\Content\Python\run_portfolio_capture.py" -NoUI
```

Output: `Saved/Audit/portfolio_capture.json` + renders in `Products/Portfolio/2026-09-03/`

For cinematic footage, use **Movie Render Queue** on a Level Sequence with the 4 golden spiral cams.

## Step 5 — Melusina EEVEE Upgrades (Blender, parallel)

Run in Blender 5.2 Text Editor:
```python
exec(open(r"G:\EnvironmentPortfolio\BS_GodFile\Tools\render_melusina_beauty_still.py").read())
```

Fixes needed:
- Beauty (7/10): add ground contact shadow plane, replace skybox with twilight env, remove UI orbs -> target 8.5/10
- Glam (8.5/10): denoise skin (keep hexagonal hair pattern), add subtle env reflection in rim light -> target 9/10

Output: `my-site-clean/generated/assets/character/`

## Step 6 — Foliage & Island Ring (after editor restart)

Apply manifests (build apply harnesses from `apply_sea_above_heatmap_dress.py` pattern):
- `specs/water_veil/sea_above_foliage.v1.json` (86 pts, Megascans palms/ferns on islands)
- `specs/water_veil/sea_above_island_ring.v1.json` (22 pts, silhouette cards at golden radii 5k-55k)

Apply order: IslandFoliage first (safe raycast to island land), then BalconyFlora + MooringDress with waterline-snap mode (snap Z to 13455 + clearance, NOT raycast to canyon floor).

## Step 7 — P0 Gates (after all placement lands)

- `static_gates`: `python Tools/echo_run.py run static_gates`
- `package_build`: verify your earlier cook produced `Products/P0_Itch_Release/*.exe`
- Record ledger rows for: `sea_above_foliage`, `sea_above_exploration`, `sea_above_demo_capture`
- Re-run P0 golden run so packaged evidence reflects the dressed map.

## Authority & Safety
- No new material masters (AAA tier only)
- Single writer: one editor :9316
- Height-aware (CanonicalLandscape only)
- Evidence: each shot = Movie Pipeline output + gate ledger row