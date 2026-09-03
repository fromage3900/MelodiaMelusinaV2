# Shorewake Dress — Copernicus AO/Normal Wiring + Hair Rebind Spec

**Date:** 2026-09-02 · **Editor gate:** Monolith 9316 (currently DOWN — apply when a real MCP editor opens)
**Why:** The dress's bake-of-record is the stale Aug-30/31 `SM_ShorewakeDress_48MAT_v2_*` set.
The updated copernicus AO/normals are baked and now staged in `CanonicalOutfit.spp`. This spec
wires them onto the dress MIs in-editor, and rebinds Melusina's hair (found present on disk,
currently unbound — only `BP_KawaiiPhysicsPlacementProbe` references it).

---

## Part A — Copernicus AO / Normal wiring for the Shorewake dress

### Source maps (baked, verified, in the staged project)
| Channel | Map | Convention | Notes |
|---|---|---|---|
| AO+RM | `T_Cymatic_ShorewakeTidepool_ORM.png` | R=AO, G=Rough, B=Metal | 2048, eigenmode Chladni relief |
| Normal | `T_Cymatic_ShorewakeTidepool_Normal.png` | **OpenGL Y+** → flip G on UE import | eigenmode crystal plate (2,2)+(2,3) |
| Height | `T_Cymatic_ShorewakeTidepool_Height.png` | escaped black→white | parallax relief |
| BaseColor | `T_Cymatic_ShorewakeTidepool_BaseColor.png` | sRGB | ocean→tide→foam |

### Dress MI targets (the 9 clean fabric sets; apply to the garment layer MIs)
`MI_Melusina_Dress_Shorewake` + the 10 garment-layer MIs on the small family
(`M_Master_Nikki` / `M_Universal_Enhanced_Fabric` / `M_Master_Toon_Universal_Alpha`).

### In-editor steps (Monolith, when 9316 is up)
1. **Verify single editor + MCP** (curl :9316 initialize returns).
2. Query the parent master's REAL texture-param names (Toon master exposes `Albedo/NormalMap/
   HeightMap/ORM/RoughnessMap/MetallicMap`, NOT `BaseColor/Normal`). Use
   `get_texture_parameter_names`.
3. Import the 4 ShorewakeTidepool PNGs as textures (sRGB on BaseColor; normal/ORM/height linear).
4. Per dress MI: set `Albedo`←Tidepool_BaseColor, `NormalMap`←Tidepool_Normal (flip G OpenGL→UE),
   `HeightMap`←Tidepool_Height, `ORM`←Tidepool_ORM.
5. Save each; re-read via `get_cdo_properties` to confirm (success ≠ saved; re-verify).

**Gate:** `universal_garment_s4_per_garment_mi` — maps + ledger row, never prose.

---

## Part B — Melusina Hair rebind

### Recovered (verified present, NOT lost)
| Asset | Path |
|---|---|
| Hair skeletal mesh | `Content/Melodia/Characters/Melusina/Hair/SK_MelusinaHair.uasset` (10.4 MB) |
| Hair skeleton | `Content/Melodia/Characters/Melusina/Hair/SK_Melusina_Hair_Skeleton.uasset` |
| Two anim BPs | `Hair/ABP_Melusina_Hair.uasset`, `Hair/ABP_Melusina_WaterHair.uasset` |
| Boneless backup | `Hair/SK_MelusinaHair.uasset.boneless_20260730.bak` (9.8 MB) |
| Recovered FBX | `Content/00_Archive/RepoRoot_2026-08-31/SK_Melusina_FIXED_Hair.fbx` |
| Cinematic flip | `Content/Cinematics/MelusinaWaterHair/GC_MelusinaHairFlip_v22.uasset` |

### Current defect
The canonical outfit USDZ **does** contain hair (`FF_MelusinaHair_Domain`, `Hair_Strand_001/003/
005/008` — 317 total objs), but my merged `SM_CanonicalShorewake.obj` (28 mats / 9 fabric) **did
not export it** (0 hair refs in OBJ/MTL). And in Content, only `BP_KawaiiPhysicsPlacementProbe`
references `SK_MelusinaHair` — the character pawn is not bound to it.

### In-editor steps (Interchange, when 9316 up)
1. On the Melusina pawn (`BP_MelusinaJRPGCharacter` / `BP_Melusina`) add a Skeletal Mesh
   component or re-point `CharacterMesh0`'s hair slot to `SK_MelusinaHair`.
2. Assign `ABP_Melusina_WaterHair` (water-reactive) or `ABP_Melusina_Hair` (default) as the
   anim class on the hair component.
3. **Do NOT pick the `.boneless_20260730.bak`** as the live mesh — it is the pre-bone state kept
   for rollback. The live mesh is `SK_MelusinaHair.uasset`.
4. Verify attach parent is `CharacterMesh0`, mesh matches `SK_MelusinaHair`, ABP resolves.
   (Mirror the existing `audit_melusina_water_hair.py` contract from the 09-02 audit.)
5. Save; re-read to confirm.

**Hair into the Substance canonical:** optionally re-export the hair strands (Blender 5.2) as an
OBJ and re-run `canonical_outfit_builder.py` with a `HAIR_MESH` arg so Substance stages hair as
an open set too — its SBW/stylization mat is `M_Master_Toon_Universal_Alpha`.

---

## Part C — Trim unnecessary assets (when editor up)
- Delete stale `CanonicalOutfit_autosave_0.spp` (196 MB, pre-bling autosave) — frees ~200 MB.
- The 19 shader-cruft materials are already skipped at bake source (never created as sets).
- Orphan `MI_*` trim + the 259 read-only `.uasset` (`attrib -R`) — editor/git work, guard-listed.

*Nothing here mutates Content/** via script. All editor writes go through the single 9316
holder with before/after Monolith reads + a `record_gate.py` row per the echo contract.*