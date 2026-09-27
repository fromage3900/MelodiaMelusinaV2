# Melusina Regalia: lookdev v2 → v5, UE import, eyebrow + Kawaii earring prep (2026-09-26)

Status as of 2026-09-26 20:00 ET. This is a factual record of the work. Numbers come from the build receipts listed in §10.

## 1. Goals
- Give Melusina a matched regalia set: **circlet, tiara, earrings and necklace**. The pieces are gold with aquamarine stones (circlet and tiara) and "Void Orchid" purple stones (earrings and necklace).
- Fit the pieces to *her* head (a chibi head, roughly 2.23× a 150 mm adult head) rather than to a generic head. There are two variants: **bald** (on the skull) and **hair** (on her water hair).
- Bring the pieces into UE 5.8 attached to her skeleton (`head_x` / `spine_03_x`), with a test level and a capture pass.
- Follow-ups: diagnose her eyebrows in UE, and prepare physics-driven earrings with KawaiiPhysics.

## 2. History (what changed and why)
| Version | What changed | Why |
|---|---|---|
| v1 (Sept 25–26) | Contract / baroque builds: `melusina_regalia_circlet.py`, `regalia_baroque_*`, `regalia_earring_*`, `regalia_necklace_*`, `regalia_stone*` | First pass on the stones, earrings and necklace. Established the stone palette (`regalia_stone_palette.json`). |
| v2 / v2b | Full set rebuilt as one house package (`regalia_v2_build.py`, `regalia_v2b_build.py`). v2b: non-gem objects have `visible_transmission=False` | Stones were picking up gold bounce light. |
| v2c / v2d | Re-fit to a *new* head size. Head changed from 397×445×505 mm to 150×200×225 mm. Circlet inner size changed from 324×347 to 156×206 mm. Earrings moved to the new ears. | The old head measurements were wrong. Gold was scaled non-uniformly to the head and the stones uniformly. |
| v3 / v3_final | Fitted on Melusina herself (`v3_extract_melusina.py` → `regalia_v3_build.py`). Head factor **k = 2.231** (section at brow+40 mm = 334.6×435.1 mm). Circlet scaled ×2.55/2.38/2.46 and tiara ×2.73/2.19/2.46 relative to v2d, with 0 penetrating verts. Overhang compression applied. Earrings seated on the lobes; necklace ×1.373 settled on the neck at z = 1.40 m. | The pieces needed to sit on her actual head. Hair was appended but hidden (the main hair mass rises 51 mm above the scalp and the bangs cover the forehead). |
| v4 (`regalia_v4_it2`) | Circlet and tiara **rebuilt as head-conforming sweeps** on paths traced over her skin (§3). Slim gold profile with rails, filigree loops projected onto the surface, front collet stone (circlet), front spire with a pear stone (tiara). Hair variant: band sits on the skull + 3 mm clearance + 3 mm hair layer, and copies of the hair are pinched under the band. | The v3 ring headpieces floated and did not follow the skull. Cost: circlet **174,330** tris and tiara **120,498** tris at export. |
| v5 (`regalia_v5`) | **Filigree plate band with fixed topology.** All topology is decided in nominal motif space (`motif2d.py`: circlet L = 1240 mm, H = 15 mm; tiara L = 720 mm, H = 12 mm), then mapped onto the v4 conforming path by arc length. Parts: plate (CDT with motif footprints as holes), half-round wires with rounded caps, beads. Front: collet ellipse, a crown of 9 beads, scroll wires with spiral eyes. Sides: motif A (paired teardrops) and motif B (lyre scroll). | To cut triangle counts, make the topology independent of the fit, and make the filigree read as jewellery. Result: circlet **30,858** tris, tiara **19,894** (earrings 21,048 and necklace 99,166 unchanged). |

### v5 stability proof
The circlet and tiara were rebuilt at three different fits:
- **A:** defaults.
- **B:** `c_tilt .06, c_clear .0045, c_fab .013, c_h .0135`.
- **C:** `c_tilt .09, c_clear .0025, c_h .0165, t_tilt 18, t_h .013`.

All three produce **identical** vertex, face and triangle counts and topology hashes:

| Piece | Verts | Faces | Tris | Topology hash |
|---|---|---|---|---|
| Circlet | 15,366 | 18,292 | 30,732 | `78a2b1a5d5460062` |
| Tiara | 8,534 | 10,071 | 17,064 | `584b55a261dfb566` |

The tris above are band only; the export counts in the table in §2 include the stones and spire.

Mesh checks on every fit: 0 non-manifold edges, 0 boundary edges, 0 zero-area faces, 0 loose verts, 0 self-intersecting face pairs, 1 shell. The full build on fromage matched the box test build exactly. Receipts: `Tools/LookDev/Regalia/receipts/regalia_v5_stab_fit{A,B,C}_build_receipt.json`.

## 3. Fit method
- **Her scale:** head factor k = 2.231 relative to a 150 mm adult head. Brow top z = 1.6257 m, head top z = 1.8356 m, ear top z = 1.5938 m (Blender units are metres).
- **Circlet path:** a closed loop traced by casting rays inward onto her skin (BVH of the body) around a tilted axis. Settings: tilt 0.075, front edge 10 mm above the brow, 3 mm clearance, smoothed with a circular Gaussian plus a median filter. Hair variant: +3 mm hair layer (`hair_lift`).
- **Tiara path:** an open arc over the crown at z0 = max(1.60, ear_top + 12 mm), tilted 22° with a 96° span.
- **Frames:** tangent / normal / up frames along each path. v5 maps (s, u, a) in motif space to world space as path(s·ks) + U·u·ku + N·a. ks and ku are about 1.0 at the default fit.
- The front peak of the circlet conforms to the skin by a raycast for u > 4.7 mm.
- **Hair pinch (hair variant):** hair copies are pushed inward under the bands using the per-sample band half-heights. The originals are hidden, never edited. v5 moves 45,823 of 85,266 verts for the circlet alone (max 61 mm), versus 78,847 of 116,924 (max 121 mm) in v4.

## 4. Blender → UE mapping and solve
- **Exports:** static FBX in Blender rest-pose world space, 1 BU = 100 UE units, UE = (x, −y, z)·100 ("blender-cm"). The bust was posed (archer pose, frame 11), so each piece is corrected from posed to rest with its bone: `head.x` for the head pieces and earrings, `spine_03.x` for the necklace.
- **Solve** (`solve_v4_attach.py`): a similarity transform between the Blender `character_rig` rest bones and UE `SK_Melusina_Skeleton` component space.
  - 230 bone pairs matched, 219 kept after outlier rejection.
  - Scale 1.000005, rotation ≈ identity, t = (0, −0.065, 0.003) cm.
  - Median residual **0.015 cm**, max 0.65 cm.
  - Conclusion: blender-cm space is UE component space.
- **Attach transforms** (`ue_attach_v4.json`): relative transforms to `head_x` / `spine_03_x`. For the head pieces this is the inverse of the `head_x` bind pose, the same convention `MelodiaHairComponent` uses for the hair.

## 5. UE assets created (all new, all under one folder)
`/Game/Melodia/Characters/Melusina/Regalia_v4/`
- `SM_Regalia_v4_Circlet`, `SM_Regalia_v4_Tiara`, `SM_Regalia_v4_Earrings`, `SM_Regalia_v4_Necklace`. Imported via FBX; bounds match the sidecar within 0.0005 cm.
- `M_Regalia_v4_Gold`, `M_Regalia_v4_GemAqua`, `M_Regalia_v4_GemPurple`, `M_Regalia_v4_Pearl`: standalone materials, not instances of any master.

Material slots:

| Mesh | Slot → material |
|---|---|
| Circlet, Tiara | `MS_Gold` → Gold, `MS_GemAqua` → GemAqua |
| Earrings, Necklace | `MS_Gold` → Gold, `MS_GemPurple` → GemPurple |

Material values:

| Material | Base colour | Metallic | Roughness | Specular / emissive |
|---|---|---|---|---|
| Gold | (1.0, 0.72, 0.33) | 1 | 0.22 | — |
| GemAqua | (0.42, 0.78, 0.86) | 0 | 0.04 | spec 1.0, emissive 0.06 |
| GemPurple | (0.42, 0.10, 0.72) | 0 | 0.05 | spec 1.0, emissive 0.06 |
| Pearl | (0.93, 0.90, 0.86) | 0 | 0.30 | spec 0.6 |

The v5 meshes have **not** been imported into UE yet. The FBX files are ready (§10).

## 6. Eyebrows: diagnosis and fix plan
**Diagnosis** (read-only):
- In `/Game/Characters/Melusina/BP_Melusina`, `L_Eyebrow`, `R_Eyebrow` and `R_Eyelash` are StaticMeshComponents at the **root level** of the Blueprint. They have no attach parent and no socket, and sit at location 0 with scale 10.
- The meshes are `Staging_20260923/Melusina_Brows_Export_20260922_{L,R}_Eyebrow`, from `harp_bow_pipeline/Melusina_Brows_Export_20260922.fbx`, which was authored at 1/10 scale.
- Result: the brows ride on the actor root (the capsule), not the head. They cannot follow head or face animation, and they only line up with the face when the body mesh sits at the actor origin.
- The brow geometry itself is correct. Scaled ×10 it lands in rest-pose component space, within about 2 mm of the rest-corrected brow proxies in `regalia_v3_final.blend`.
- The DollBall, Sheep* and Hoof* accessories in the same Blueprint use the same root-level pattern.
- The UE skeleton has `head_x` and `DEF-brow_T/B_*` bones. There is no skeletal brow mesh.

**Fix (prepared, not run):**
- `SM_Melusina_Brows_v1`: both brows merged at true size, 340 verts / 672 tris, slot `MS_Brows`. It reuses `MI_Melusina_Brows_Dark` without modifying it.
- It attaches to `head_x` with the same relative transform as the regalia.
- Stage `eyebrows_import` imports it into `/Game/Melodia/Characters/Melusina/Eyebrows_v1/`. Stage `attach_level` places it in the test level.
- `BP_Melusina` itself is not modified (the change is owner-gated). The recommended fix there is to parent the brow and lash components to the character mesh at the `head_x` socket with the same relative transform.

## 7. KawaiiPhysics earring rig
- **Plugin:** `Plugins/KawaiiPhysics` v1.21.0 (EngineVersion 5.8.0), enabled.
- **Mesh:** `SK_Regalia_v4_Earrings.fbx`, one skinned mesh (10,540 verts / 21,048 tris), slots `MS_Gold` and `MS_GemPurple`. Rigid weights, one bone per part. Corrected to rest pose with `head.x`.
- **Skeleton (9 bones):** `earrings_root` (origin) → `ear_{L,R}_root` (stud) → `ear_{L,R}_dangle_01` (ring1, round stone, bezel, loops) → `_02` (ring2) → `_03` (cap and drop stone).
- **Verification:** a round-trip re-import gives bone heads within 0.0001 cm of the sidecar, and the mesh bounds match the static `SM_Regalia_v4_Earrings` exactly.
- **ABP `ABP_Regalia_Earrings_v4`** (stage `earrings_abp`, not run): LocalToComponentSpace → KawaiiPhysics (RootBone `ear_L_root`) → KawaiiPhysics (RootBone `ear_R_root`) → ComponentToLocalSpace → Output.
  - PhysicsSettings: Damping 0.6, Stiffness 0.15, WorldDampingLocation 0.8, WorldDampingRotation 0.8, Radius 0.3 cm, LimitAngle 50°.
  - Gravity (0, 0, −981), world-space gravity on. No colliders in v1.
- **Attachment:** the SkeletalMeshComponent attaches to `head_x` with the regalia relative transform. The static earrings are hidden, not deleted.

## 8. Scripts and how to run each stage
Repo copies are in `Tools/LookDev/Regalia/scripts/`. The working copies live in `C:\EnvironmentPortfolio\_lookdev_work\regalia_v2\scripts\`, and the scripts use absolute paths into `_lookdev_work`.

Blender runs always use `blender -b --factory-startup --disable-autoexec <src.blend> --python <script> -- <args>`, and the scripts refuse to overwrite existing outputs.

| Stage | Command / source |
|---|---|
| v4 build | `regalia_v4_build.py` on `regalia_v3_final.blend` (`run_v4.ps1`) |
| v4 renders | `regalia_v4_render.py` |
| v5 build | `regalia_v5_build.py` on `regalia_v3_final.blend` → `regalia_v5.blend` plus receipt. `-- --stability --tag _fitX [--c_tilt …]` writes a receipt only. `motif2d.py` must sit next to the script (or set `REGV5_MOTIF`). |
| v5 renders | `regalia_v5_render.py` on `regalia_v5.blend` `-- [shots] --samples N --res N`. Shots: hero, hero_c, front, profile, circlet, tiara, topo, tiaratopo. Output dir from `REGV5_OUT`. |
| Rig / pose dumps | `v4ue_dump_rig.py`, `v4ue_dump_pose.py` (read-only on the R09 source) |
| FBX export | `v4ue_export_fbx_rest.py` (v4), `v5ue_export_fbx_rest.py` (v5) |
| Attach solve | `solve_v4_attach.py` (plain Python) → `ue_attach_v4.json` |
| Earring rig | `earrings_rig_build.py` on `regalia_v4_it2.blend` |
| Brows | `brows_v1_export.py -- <brows fbx> <outdir>` |
| UE (regalia) | `python ue_v4_run.py probe\|import\|materials\|level\|assemble\|capture`. Goes through Monolith (`Tools/Audio/monolith_client.py`, port 9316) and runs `ue_v4_build_write.py` in the editor. **Done:** probe, import, materials. **Not run:** level, assemble, capture. |
| UE (extras) | `python ue_v4_extra_run.py eyebrows_import\|earrings_import\|earrings_abp\|attach_level\|check`. Runs `ue_v4_extra_write.py` and Monolith animation actions. **None run yet.** `attach_level` needs `level` + `assemble` done first. |

Safety built into the UE scripts:
- Saves are allow-listed to `Regalia_v4/` and `Eyebrows_v1/`, and existing assets are never replaced.
- `level` refuses to switch maps while the current map has unsaved changes.
- Only one agent writes in the editor at a time.

## 9. Renders
**v5** (1200 px, Cycles CPU, 64 samples): `C:\Users\froma\Documents\lookdev_regalia_v2\v5\`
- `v5_{bald,hair}_hero_threequarter_both.png`
- `v5_{bald,hair}_hero_threequarter_circlet_only.png`
- `v5_{bald,hair}_front_both.png`, `v5_{bald,hair}_profile_both.png`
- `v5_{bald,hair}_circlet_closeup.png`, `v5_{bald,hair}_tiara_closeup.png`
- `v5_bald_circlet_topology_motifA.png`, `v5_bald_circlet_topology_front.png`
- Contact sheet: `_sheet.jpg`

**v4** (same shot names with a `v4_` prefix, no topology shots): `...\lookdev_regalia_v2\v4\`

**Earlier:** `...\v2b\`, `\v2c\`, `\v2d\`, `\v3\`

| v4 bald hero | v5 bald hero | v5 circlet close-up |
|---|---|---|
| ![](img/regalia_v4_bald_hero.jpg) | ![](img/regalia_v5_bald_hero.jpg) | ![](img/regalia_v5_circlet_closeup.jpg) |

| v5 topology (motif A, clay + wire) | v5 hair variant |
|---|---|
| ![](img/regalia_v5_topology_motifA.jpg) | ![](img/regalia_v5_hair_front.jpg) |

## 10. File locations (not committed to git unless noted)
- **Blends:** `C:\EnvironmentPortfolio\_lookdev_work\regalia_v2\`
  - `regalia_v2.blend`, `v2b`, `v2d`, `v3`, `v3_it1`, `v3_it2`, `v3_final`, `v4_it0`, `v4_it1`, `v4_it2` (final v4, 28 MB), `regalia_v5.blend` (22 MB)
  - `scripts\regalia_contract.blend`
- **FBX:**
  - `...\ue_export_v4\restpose\SM_Regalia_v4_*.fbx` (plus `_BaldFit`)
  - `...\ue_export_v5\restpose\SM_Regalia_v5_*.fbx` (plus `_BaldFit`)
  - `...\ue_export_v4\earrings_physics\SK_Regalia_v4_Earrings.fbx`
  - `...\ue_export_v4\eyebrows\SM_Melusina_Brows_v1.fbx`
  - Blends and FBX together: 33 files, about 143 MB.
- **Receipts, sidecars and solve JSONs:** committed to `Tools/LookDev/Regalia/receipts/` and `Tools/LookDev/Regalia/ue/`.
- **Renders:** `C:\Users\froma\Documents\lookdev_regalia_v2\{v2b,v2c,v2d,v3,v4,v5}\`. Only the 5 preview JPGs are committed (`Docs/LookDev/img/`).
- **UE .uasset:** `Content/Melodia/Characters/Melusina/Regalia_v4/*.uasset` (8 files).

## 11. Open issues
1. **Plate topology:** the v5 plate between motifs is a CDT fan of long thin triangles. It shades cleanly (flat plate, subsurf render level 1), but it's not clean quads under wireframe inspection.
2. **Hair variant:** her bangs and water droplets cover most of the circlet. The hair pinch is gentler than v4's, but the hair shots undersell the piece.
3. **Tiara skin dips:** 1–5 of 4,621 sampled tiara verts sit up to 0.5 mm inside the skin, depending on the fit.
4. **Filigree at distance:** the filigree reads in close-ups but is subtle at bust distance.
5. **UE stages not run:** `level` (blocked: the editor was on `/Game/ZenForestTest` with unsaved changes from an automation run), `assemble`, `capture`, `eyebrows_import`, `earrings_import`, `earrings_abp`, `attach_level`. The v5 FBX files are not imported.
6. **`BP_Melusina`:** its accessory components (brows, lash, DollBall, Sheep*) are root-level and don't follow bones. This needs an owner-approved Blueprint change.
7. **Earring ABP:** the KawaiiPhysics pin and property names follow plugin conventions but haven't been verified live.
