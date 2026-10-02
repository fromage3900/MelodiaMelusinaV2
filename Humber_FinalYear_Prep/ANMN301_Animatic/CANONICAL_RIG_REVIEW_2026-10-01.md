# Canonical rig review — why the animatic renders grey (2026-10-01)

Owner question: *"Why couldn't we just import the canonical rig from the G: drive?
It has full shaders and its rig already properly staged. I think we need to take a
step back and review what we are actually doing."*

The question was correct. This is the answer, with the evidence.

## 1. The repo already names that file as the canonical rig

`Tools/melodia_stage_paths.py:39`

```python
MELUSINA_RIG_BLEND = Path(r"G:\MelodiaMelusina\MelusinaFinalRig\FinalUERig43.blend")
```

G: is the portable drive (also referenced at line 20 as `G:\EnvironmentPortfolio\BS_GodFile`).
It is **not mounted on the laptop** — the laptop has C:, D:, P: only.

But D: carries the identical tree:

```
D:\MelodiaMelusina\MelusinaFinalRig\FinalUERig43.blend    851 MB, 2026-08-11
```

So the canonical rig was reachable from the laptop the whole time. Nothing blocked it.

## 2. What the animatic actually used

```
proxy/SHOREWAKE_proxy_v02_storyboard.blend
  MelusinaRig           464 bones
  EXPORT_Body           18,891 verts
  EXPORT_Shirt/Skirt/Boots
  16 node materials
   0 image textures      <- the defect
```

## 3. What the canonical rig is

```
D:\MelodiaMelusina\MelusinaFinalRig\FinalUERig43.blend
  character_rig         759 bones, 234 deform
  377 mesh objects      67 image textures   66 node materials
  4096x4096 BaseColor + Normal maps
  hair strand armatures (40 / 20 / 300 bones)
```

25 of those 377 meshes deform off `character_rig` (89,240 verts). The other 352
are props, environment, and other figures.

## 4. The root cause of the grey character

Not the rig. Not the binding. **The source had no textures.**

`SHOREWAKE_OUTFIT_PLAN_v04.md` verified vertex counts and material *names* —
both pass. `EXPORT_Body` matches canonical `mesh_035` at 18,891 verts exactly,
and the material slots carry the right names (`SBW_MELUSINA`, `SKIRT.003`,
Halftone, Gradient Radial). But matching names on slots with no images is not a
textured character. `image textures: 0` was one probe away from that table and
was never checked.

## 5. Texture portability — important

In `FinalUERig43`, all 67 image paths point at `C:\Users\froma\...` and
`G:\MelodiaMelusina\...`. **Every one of those 67 files is missing on this
machine** — `froma` is a different user account, and G: is not mounted.

The character renders anyway because **53 of 67 images are packed into the
blend**. Packing is the only reason the source renders correctly. Any extraction
must preserve packed images; it cannot rely on the file paths.

14 images could not be packed during extraction because their source files are
gone in the source too (`bow_*`, `SHAWL_*`, `DPM2.004_BaseColor`,
`Material.020_*`). They were already broken upstream.

## 6. What was built and proven

```
proxy/MELUSINA_CHARACTER_rig43.blend    706 MB
  character_rig + 28 meshes + 4 rigs (incl. hair strands)
  extracted from 851 MB / 387 objects -> 706 MB / 32 objects
  pixel-faithful: 31 of 1,036,800 pixels differ (0.003%), max delta 15 = TAA jitter

proxy/SHOREWAKE_swap_test.blend         533 MB
  grey character removed, canonical appended and aligned
  target volume  lo=(-0.094,-0.966,0.797) hi=(0.371,0.966,2.786)  h=1.9881
  achieved       lo=(-0.090,-0.950,0.797) hi=(0.367,0.950,2.786)  h=1.988
  alignment: rotate 90 deg Z, scale 0.98311, snap feet to z=0.797
```

Proof renders in `proof/`:

```
00_BEFORE_grey_shot11.png           the current grey character
01_canonical_rig43_character.png    canonical rig, full textures
02_extracted_character.png          after extraction, identical
03_swapped_into_animatic_shot11.png canonical in the animatic scene
```

In `03`, the character is **textured** — blue/purple outfit, lace patterns,
chain detail, brown skin. The swap works.

## 7. What is NOT done

- **Framing.** `CAM_Intimate` was aimed at a seated grey figure. The canonical
  character does not occupy the same volume, so shots need re-aiming. This is
  the remaining work, not a defect.
- **Floating props.** `03` shows clipped/floating objects in the animatic scene.
  These exist independently of the character swap and were not investigated.
- **Pose direction** on the new rig is untested — the canonical rig has different
  bone names (`root.x`, `foot.l`, `toes_01.l` — dot notation) than the export
  (`head_x`, `c_neck_x`). Any pose table must be rewritten for it.
- **The submitted MP4 is unchanged.** `ShepherdBrennan_AnimaticCreation_2026-10-09_v04.mp4`
  is spec-compliant and untouched. Re-sourcing is a change with deadline risk.

## 8. The honest summary

Every hour spent on `c_*` bones, deform-bone discovery, and pose tables was
spent fixing symptoms on an asset that could only ever render grey. The pose fix
is real and correct, but it is correct on the wrong mesh.

The correct sequence was: find the canonical rig first, then animate.