# System Organization Plan — 2026-06-25

## EXECUTED (2026-06-25)
- Cleared Epic Vault Cache (74 GB), UE5.7 shader DDC (22 GB), Temp (8 GB) → **C: free space: 6.4 GB → 110.8 GB**.
- Extracted and moved 10 asset packs from Downloads into `G:\EnvironmentPortfolio\_AssetLibrary\_Incoming\`: Brushes_5PackVfxmed, Brushes_AlphasStylized, Brushes_BlenderStylized, Brushes_GrutComplete, Brushes_InletMSK, Brushes_LandscapeBundle2020, Brushes_SubstancePainterStylized, Brushes_ZBrushOrb_Blender, Meshes_RockForms, Tool_FloorGenerator3. Source zips/rars deleted from Downloads.
- Still open from this plan: MooaToon engine build decision, UE 5.6/5.7 uninstall decision, legacy MelodiaMelusina texture pull, Quixel Bridge install (not present on this machine).


## 0. Headline problem
**C: has only 6.4 GB free out of 952 GB.** This is almost certainly the root cause of "PC feels bloated" — UE/Adobe/Blender all stage temp + shader-cache + DDC writes on C:, and at <1% free, Windows itself slows down (no room for paging, defrag, update staging). Everything below is organized around fixing this first.

---

## 1. Immediate, safe wins on C: (no creative work at risk)

| Action | Path | Recovers | Risk |
|---|---|---|---|
| Clear Epic Games **Vault Cache** | `C:\ProgramData\Epic\EpicGamesLauncher\VaultCache` | **~74 GB** | None — these are leftover install-chunk caches for projects you *already have installed* on G:\ueprojects (ElectricDreamsEnv, MagiciansLibraryEnvironm, LyraStarterGame all match 1:1, byte-for-byte, with the cache entries). Clear via Epic Games Launcher → Settings → "Manage" → Clean up Vault Cache, or delete the folder directly while the launcher is closed. |
| Delete UE 5.7 **Shader/DerivedDataCache** | `C:\Users\froma\AppData\Local\UnrealEngine\5.7` | **~22 GB** | None — regenerates automatically on next shader compile. Close the editor first. |
| Empty **Temp** | `C:\Users\froma\AppData\Local\Temp` | ~8 GB | Low — close running apps first, a few files may be locked (skip those). |
| **Decide on duplicate engine installs** | `C:\Program Files\Epic Games\UE_5.6`, `UE_5.7` | up to **~61 GB** | Medium — only safe once you confirm no project still targets 5.6/5.7. Your portfolio is UE 5.8 per memory; check `G:\Melodia\Melodia.uproject` and any others for `EngineAssociation` before uninstalling via Epic Launcher (not by deleting the folder). |

**Run these four and you go from 6.4 GB free to roughly 165 GB free on C: without touching a single asset.**

## 2. Likely-unrelated-to-portfolio, large, and probably worth uninstalling

| Item | Size | Notes |
|---|---|---|
| `C:\Program Files\InfinityNikkiGlobal Launcher` | 83.6 GB | A game client, not an asset source. Uninstall via Windows Settings if you're not actively playing it. |
| `C:\Program Files\Epic Games\DuetNightAbyss` | 4.1 GB | Same — game, not engine/assets. |
| `C:\Users\froma\.ollama` | 38.6 GB | Local LLM model weights — keep if you use local models regularly, otherwise prune unused models (`ollama list` / `ollama rm`). |
| `G:\SteamLibrary` | 30 GB | Games on G:, not blocking C: — leave alone unless you want the space back. |

## 3. C: drive items that are install-bound (not deletable, but explains "bloat")

These are normal install footprints, not waste, but they're why Program Files is 380 GB combined: Adobe (42 GB), Autodesk (8 + 24 GB across two locations), Visual Studio (16 GB), Houdini/Side Effects (8 GB), Blender (5 GB), 3DCoat ×2 (5.8 GB), Cinema 4D, SpeedTree, Marvelous Designer, BorisFX, Red Giant. No action needed unless you want to uninstall tools you no longer use for the portfolio pivot (e.g., Maxon/SpeedTree/Marvelous if not part of the UE5.8 toon-environment workflow).

## 4. Needs your judgment call (active or legacy creative projects — I did not touch these)

| Path | Size | Last touched | Read |
|---|---|---|---|
| `G:\MelodiaMelusina` | **313 GB** | 2026-06-23 (Substance Painter files edited 2 days ago) | Still being actively worked — character rig/texture project (Melusina), separate from the environment portfolio pivot. Not stale, don't archive without asking. |
| `G:\Melodia` | 33.7 GB | 2026-06-25 (today) | **Currently live** — UE project + Blender addon suite, edited today. Its `DerivedDataCache`, `LocalDerivedDataCache`, `Intermediate`, `Saved`, `Binaries` subfolders (likely 5-15 GB combined) are safe to delete any time and regenerate on next editor launch — same rule as any UE project. |
| `G:\MooaToon-main` | 41.7 GB | 2026-02-26 (4 months stale) | Per memory, the custom MooaToon engine was abandoned in favor of stock UE5.8 + Monolith. Likely archivable. |
| `C:\UE_Builds\MooaToon` | **44.3 GB** | 2026-05-22 | Same engine build, but sitting on your nearly-full **C: drive**. If `G:\MooaToon-main` is the source and this is just a compiled build you're not actively running, this is your single best non-Epic-cache candidate to delete or move to G:. **Confirm before I delete this** — it's a full custom engine build with a build/crash history per memory, and I want to be sure nothing currently points at it. |

I'm flagging these rather than acting — they're tens to hundreds of GB of creative work and an engine build with real history, not cache. Say the word on any row and I'll execute it.

---

## 5. Asset inventory for the environment-design portfolio

### Already organized and in active use
`G:\EnvironmentPortfolio\_AssetLibrary\` (26.8 GB project total) — this is your curated, ready-to-use library:
- `Surfaces_CC0\` — 17 CC0 PBR material sets (Bricks051/066, Carpet013, Fabric045, Ground037, Marble006/012, Metal007/027/032, PavingStones070/092, Plaster001/003, Tiles074/093/101, WoodFloor043), each with full PBR maps + `.blend`/`.usdc`/`.mtlx` variants.
- `Greybox_Kit\` — 8 modular blockout meshes (blocks, columns, walls, steps, pillars) for level layout.
- `Stylization\` — 11 toon-shading utility textures (dither, hatch, flow, ramps, noise) — these directly back the `M_Master_Toon_Universal` material system.
- `Sakura\`, `Magical\`, `Alphas_Sparkles\` — themed VFX/decal textures matching your Sakura level + magical-girl aesthetic work.
- `LICENSES.md` already tracks attribution — good, keep using it for every new asset you add.

### Unextracted, sitting in Downloads — useful but not yet usable
~14 GB of asset packs downloaded but never unpacked into the library:
- `Blender-Brushes-Stylized-3-1.zip` (3.0 GB), `Alphas-Brushes-Stylized.zip` (2.9 GB), `Substance-Painter-Brushes-Stylized.zip` (2.4 GB) — stylized sculpt/paint brush sets, directly relevant to your toon material work.
- `Floor Generator 3.0 - Full Version_vfxMed.rar` (1.0 GB) — procedural floor generator tool.
- `5+brushes+pack+vfxmed.com.zip`, `Photoshop Brushes - Landscape Bundle_2020 vfxmed.rar`, `GrutBrushes.Art.Brushes.Complete vfxmed.zip` — more brush libraries (landscape-focused — good for terrain/foliage texturing).
- `All RockForms.zip` (418 MB) — rock formation meshes/brushes, useful for environment dressing.
- `86419_Zbrush_Orb_Brushes_pack_for_Blender_3D.zip` — sculpting brushes.
- `material_maker_1_6_windows.zip` — standalone procedural material tool.

**Recommendation:** extract these into a new `_AssetLibrary\_Incoming\` subfolder (or directly merge into `Stylization`/`Surfaces_CC0` as appropriate), then delete the zips from Downloads. Want me to do this extraction pass now?

### Reusable assets likely buried in legacy projects (not yet pulled into the portfolio)
- `G:\MelodiaMelusina\ACTUALCOMPILEDMELUSINATEXTURES`, `MELUSINATILEABLE TEXTURES`, `MelusinaFoliage` — tileable textures and foliage assets that may be style-compatible with the toon environment work, worth a manual pass to extract anything generic (non-character-specific).
- `G:\Melodia\Content` (live UE project) — per memory this already has `MF_InkAccumulation`, macro-variation work, and the Blender geometry-nodes addon suite (brutalist/kawaii/Islamic procedural generators) — these generator addons could feed environment dressing directly.
- No Quixel Megascans / Bridge library and no Fab marketplace downloads were found on this machine (`FabLibrary` cache is empty) — if you want photoreal-adjacent source material (rocks, foliage, terrain scans) beyond the hand-built CC0 set, Quixel Bridge is free and integrates directly with UE5.8.

### Tooling available and portfolio-relevant
Houdini 20.5 (procedural terrain/foliage), Blender 4.4, 3DCoat ×2 (sculpting/texturing), SpeedTree (foliage authoring), Substance ecosystem (no local Substance 3D Assets library detected — only the connector apps) — all installed and ready; no setup needed.

---

## Suggested order of operations
1. Clear Epic Vault Cache + UE5.7 DDC + Temp → frees ~104 GB on C: today, zero risk.
2. You confirm: keep or pull `C:\UE_Builds\MooaToon` (44 GB) off the nearly-full C: drive.
3. You confirm: uninstall UE 5.6/5.7 engine installs if nothing still targets them.
4. I extract the Downloads brush/asset packs into `_AssetLibrary`, then clear the zips.
5. Optional: pull generic (non-character) tileable textures out of `MelodiaMelusina` into the portfolio library.
