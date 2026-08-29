# Landscape Master Repair — `M_Master_Toon_Landscape_HeightBlend` — 2026-08-29

Three structural defects found and fixed in the landscape master and its triplanar function. Every
claim below was verified by **read-back or compile stats**, never by a tool return value — see
`SESSION_CLOSEOUT_WATER_MATERIALS_2026-08-29.md` §5.1 for why that rule exists (and §"What went
wrong" below for the one time I forgot it this session).

**Backups taken before each stage**, all in `Content/EnvSandbox/Materials/_Archive/Masters_BACKUP_20260821/`
(that folder is gitignored, so they are local-only safety copies):

- `M_Master_Toon_Landscape_HeightBlend_PRE_PATHFIX_20260829`
- `MF_Triplanar_LandscapePro_PRE_SIMPLIFY_20260829`
- `M_Master_Toon_Landscape_HeightBlend_PRE_NIKKIFIX_20260829`

---

## 1. The Path layer was never finished (2 hard errors)

`validate_material` reported 122 issues, of which exactly **2 were errors**, and both were the
fourth terrain layer:

| Layer | Albedo | Normal | Height | Macro sample |
|---|---|---|---|---|
| Rock | ✓ `Horizontal_1` | ✓ `T_Neutral_Normal` | ✓ `Perlin_1` | ✓ `Perlin_1` |
| Grass | ✓ `SOIL_diffuse` | ✓ `SOIL_normal` | ✓ `Perlin_10` | ✓ `Perlin_10` |
| Mud | ✓ `Cracks_10` | ✓ `T_Neutral_Normal` | ✓ `Vein_1` | ✓ `Swirl_5` |
| **Path** | ✗ `Texture: None` | ✓ `T_Neutral_Normal` | ✓ `Perlin_1` | ✗ no texture, no `TextureObject` |

A `TextureSampleParameter2D` with a null default texture is a hard compile error in UE.

**Fixed:**
- `Path_Albedo` (`MaterialExpressionTextureSampleParameter2D_27`) → `KB3D_ATL_CobblestoneStoneFloorA_basecolor`
  (sRGB, a real cobble path, and it ties the terrain palette to the Atlantis kit)
- `MaterialExpressionTextureSample_23` (Path macro breakup) → `Perlin_15`, chosen to stay
  decorrelated from Rock's `Perlin_1` and Grass's `Perlin_10`

**Result: 122 → 120 issues, zero errors.** Everything remaining is `warning` or `info`.

---

## 2. The triplanar lane had never compiled

**The function was fine. The master's call site was wrong.**

`MaterialFunctionCall_8`'s `Tex (T2d)` pin was fed the **RGB output of `Rock_Albedo`'s
TextureSample** — a float3 colour where a *texture object* is required. You cannot take a texture
object out of a TextureSample's RGB pin; that needs a `TextureObjectParameter`.

```
(Function MF_Triplanar_LandscapePro) Cannot cast from float3 to texture2D.
```

That error is present in the previous session's log at 17:56:51, so this lane has been failing for
at least as long as logs go back. **Which is why nobody noticed the sampling artifacts — the lane
was never rendering.**

**Fixed:** added `TriplanarPro_Texture` (`MaterialExpressionTextureObjectParameter`, group
`03 | Triplanar`, default `Horizontal_1`) and wired it to `Tex`.

**Checked the other two masters that call this function** — `M_Master_Nikki_Landscape` and
`M_Master_Nikki` were **already correct**, both using proper `TextureObjectParameter`s. The
HeightBlend master was the only one wired wrong.

---

## 3. The Nikki grade lane was circular

```
MFC_5 (MF_NikkiDreamGrade).Emissive → bNikkiFast(SSP_1).True
                                    → LinearInterpolate_57.A → bNikkiHero(SSP_8).True
bNikkiFast                          → bNikkiHero.False
bNikkiHero                          → MFC_5.BaseColorIn          ◄── closes the loop
```

Both branches of `bNikkiHero` derived from `MFC_5`, whose input was `bNikkiHero`. It only compiled
because static-switch pruning cut the loop when `bNikkiFast = False` **and** `bNikkiHero = False` —
the default. Enabling *either* switch would have produced a genuine cycle.

Two consequences:
1. **`MF_NikkiDreamGrade.Color` had zero consumers** — the graded albedo was computed and thrown
   away. Only `Emissive` was wired, and it was (incorrectly) driving base colour.
2. `PastelLift`, `DreamSaturation`, `DreamContrast`, `DreamShadowLift` therefore did nothing, and
   the whole Madoka lane (routed through `LinearInterpolate_57` into `bNikkiHero.True`) was
   unreachable.

**Fixed — three edges, turning the grade from feedback into a forward pass:**

| Edge | Before | After |
|---|---|---|
| `MFC_5.BaseColorIn` | `bNikkiHero` (the cycle) | `LinearInterpolate_56` — the assembled base colour |
| `bNikkiFast.True` | `MFC_5.Emissive` | `MFC_5.Color` |
| `LinearInterpolate_57.A` | `MFC_5.Emissive` | `MFC_5.Color` |

`MFC_5.Color` went from 0 consumers to 2. `bNikkiHero` no longer feeds back.

---

## 4. `MF_Triplanar_LandscapePro` — cost + correctness pass

**Signature deliberately unchanged.** The function is referenced by three masters
(`M_Master_Toon_Landscape_HeightBlend`, `M_Master_Nikki_Landscape`, `M_Master_Nikki`) feeding ~10
instances, including the 8 NikkiHero showcase instances. An earlier plan to cut 11 inputs → 4 was
**withdrawn** once that blast radius was measured — the inputs are not where the cost lives.

Rewrote the HLSL instead:
- `sincos()` instead of separate `sin`/`cos`
- **one** sine plus two `frac` decorrelations instead of three sines for the breakup
- **`Texture2DSampleGrad`** with explicit derivatives — world-space UVs carry no usable implicit
  gradients, so the previous `Texture2DSample` would shimmer at plane transitions on km-scale terrain

> **Do not "simplify" the breakup to a single shared value.** The three weights must stay
> decorrelated — a shared value cancels *exactly* in the `w /= (w.x+w.y+w.z)` normalise and the
> effect vanishes. That is why the original author wrote three sines.

---

## 5. Verification

Compiled with each lane forced on via throwaway probe instances (created, measured, deleted):

| Config | PS instr | VS instr | Samplers |
|---|---|---|---|
| all off (master default) | 593 | 153 | 13 |
| `bTriplanarPro_Active` | 667 | 153 | 13 |
| `bNikkiFast` | **610** | 153 | 13 |
| `bNikkiHero` | **631** | 153 | 13 |
| `bNikkiFast` + `bTriplanarPro_Active` | **684** | 153 | 13 |

All clean. Zero `Cannot cast` errors after the fix. **Sampler count never moves off 13** (of 16) in
any configuration — worth remembering, because it is the hard ceiling on any future per-layer
triplanar work.

---

## 6. Still open

- **`MF_NikkiDreamGrade.Emissive` is now orphaned** (0 consumers). It was previously driving base
  colour, which was wrong. Wiring it into the emissive chain means deciding how it combines with
  `Multiply_6` → `SubstrateToonBSDF.EmissiveColor`. That is an art decision, not a repair.
- **~53 orphaned parameters remain** — `Wetness`, `ShoreWetnessBoost`, `PathWearStrength`, `Rim*`,
  `Sparkle*`, `Iridescence*`, all `Madoka*` and `Itto*` scalars, `ShadowDream*`, `ShadowFlower*`.
  Note `ShoreWetnessBoost` is specifically called for by `TONIGHT_ASSEMBLY_PLAN_2026-08-26` §2.1
  (`≈0.46`) and currently does nothing.
- **Landscape painting is still blocked**, and not by the material: `Landscape.target_layers` is an
  empty map, and both `target_layers` and `LandscapeLayerInfoObject.layer_name` are **read-only from
  Python**. The four layer infos already exist at `/Game/ZenForestTest_sharedassets/`
  (`Rock_`, `Grass_`, `Mud_`, `Path_LayerInfo`; `Rock_LayerInfo.layer_name == "Rock"` confirmed).
  Assigning them is a Landscape Mode → Paint UI operation.
- `bTriplanarPro_Active` is still `False` on `MI_Landscape_CliffGrass` — the lane compiles now but
  is not enabled.

---

## 7. Closeout (2026-08-29 ~17:30)

**State at closeout: saved, quiescent, compile-verified, committed in this change.**

- Final on-disk saves: `MF_Triplanar_LandscapePro` 15:48:02, `M_Master_Toon_Landscape_HeightBlend` 15:55:45, `MI_Landscape_CliffGrass` 16:37:20. All valid UE packages (magic verified).
- **Independent compile verification from the editor log:** the `Cannot cast from float3 to texture2D` failure's last occurrence is 15:48:11 (nine seconds after the function save, before the master's final two saves). After the 15:51/15:55 master saves the error **never recurs** for the remaining session (~90 min), and dependent instances (`MI_SeaAbove_LiquidCathedral_Substrate`, `MI_Landscape_CliffGrass`, external-actor instances) log no further material-compile failures. This corroborates §5's probe-instance stats without re-running them.
- Both editor instances were closed by the owner ~17:23 (one clean exit logged at 17:23:46, the other reaped moments earlier); no dirty packages held the landscape assets at exit.
- **Incident, for the record:** two `UnrealEditor` processes ran concurrently 13:57–17:23 (one-editor rule violated). The second instance hit `Ensure condition failed: InRHITexture [D3D12RenderTarget.cpp:599]` at 16:26:51 during a PIE launch for `MELUSINA_AAA_SKIRT_TUNE_20260829` — the same ensure family as the six-pass playtest's Pass 1/2. Dump: `Saved/Crashes/UECC-Windows-CAD9B4394CE4DA9BCEC6EE980B0FA5E7_0000/`. It was a *handled* ensure (editor kept running); **no landscape artifact was affected** — all surgery saves predate it by 30+ minutes.
- **Provenance note:** `M_Master_Nikki` / `M_Master_Nikki_Landscape` were re-saved at 16:10 and `MI_Landscape_CliffGrass` at 16:37 as passengers in mixed save batches from the hair/skirt lane. Per §2 the Nikki masters were verified correct and **not edited** by the surgery; their dirty state belongs to that lane's commit, not this one. `MI_Landscape_CliffGrass` is included here as the surgery's compile-verified instance.
- §6 "Still open" items are unchanged and all need a person: landscape paint layers (Landscape Mode → Paint), `bTriplanarPro_Active` on `MI_Landscape_CliffGrass` (visual call), `MF_NikkiDreamGrade.Emissive` wiring (art decision), ~53 orphaned parameters (`ShoreWetnessBoost` among them, called for by `TONIGHT_ASSEMBLY_PLAN_2026-08-26` §2.1).

---

## What went wrong, and the rule it re-proves

The first Atlantis material pass **wrote all 333 `.uasset` files and reported success while changing
nothing.** `mesh.static_materials` returns a *copy* of the struct array in Python, so mutating the
elements in place never reaches the asset. The fix is to build fresh `unreal.StaticMaterial` structs
and replace the whole array.

Cost: ~5 minutes of editor grind for a no-op. Caught only by reading the values back afterwards.

> Verify by read-back. A tool that returns `True` and a save that writes bytes both prove nothing.

Second, smaller one: `EditorAssetLibrary.delete_asset()` returned `True` for a scratch
`LI_TEST_Rock.uasset` that was still on disk minutes later and had been staged in git. Deleted
manually.
