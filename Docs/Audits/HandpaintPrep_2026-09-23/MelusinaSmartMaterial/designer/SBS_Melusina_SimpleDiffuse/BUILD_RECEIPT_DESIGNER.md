# BUILD_RECEIPT_DESIGNER — SBS_Melusina_SimpleDiffuse (M1 Nikki deepen)

**When:** 2026-09-24 ~02:35 ET (America/Toronto)  
**Machine:** fromage `6402dab1-6635-4abb-8220-27a07354b444`  
**Milestone:** **M1** (GOAL_V2_GO + GOAL_INFINITY_NIKKI_BAR)  
**Naming:** Melodia / Melusina only. Real `sbscooker` exit **0**. Magic `37 7A BC AF`.

---

## Before / after sizes

| Artifact | v1 scaffold | **M1 v2** | Delta |
|---|---:|---:|---:|
| `.sbs` source | 72,026 B | **130,164 B** | +58,138 |
| `.sbsar` cooked | **2,456 B** | **3,740 B** | **+1,284 (~+52%)** |
| Painter shelf SBSAR | 2,456 B | **3,740 B** | refreshed |
| Ref: SimpleDiffuse_V2.sbsar | — | 25,667 B | Melusina still leaner (see honesty) |
| `build_sbs.py` | 29,690 B | **50,060 B** | denser generator |

---

## Delivered paths

| Artifact | Path |
|---|---|
| Folder | `C:\EnvironmentPortfolio\BS_GodFile\Saved\KimiWork\HandpaintPrep_2026-09-23\MelusinaSmartMaterial\designer\SBS_Melusina_SimpleDiffuse\` |
| Goals | `GOAL_V2_GO.md`, `GOAL_INFINITY_NIKKI_BAR.md` |
| GRAPH_SPEC | `...\GRAPH_SPEC.md` (Implemented in v2) |
| Generator | `...\build_sbs.py` |
| **Openable SBS** | `...\SBS_Melusina_SimpleDiffuse.sbs` (**130,164 B**) |
| **Cooked SBSAR** | `...\exports\SBS_Melusina_SimpleDiffuse.sbsar` (**3,740 B**) |
| Painter shelf | `C:\Users\froma\OneDrive\Documents\Adobe\Adobe Substance 3D Painter\assets\materials\SBS_Melusina_SimpleDiffuse.sbsar` |
| Cymatic bitmaps (connectable) | `...\resources\T_Cymatic_FrozenFracture_*.png` |

---

## Cook log (exit 0)

```bat
cd /d ...\SBS_Melusina_SimpleDiffuse
python build_sbs.py --cook
```

```
[INFO][SBSCooker]Substance Cooker 10.1.0 ...
[INFO][SBSCooker]Loading... Flattening... Front End... Back End...
[INFO][SBSCooker]Writing file '.../exports/SBS_Melusina_SimpleDiffuse.sbsar'...
[INFO][SBSCooker]Nb files processed: 1/1 (100%)
[cook] exit 0
[cook-size] 3740
```

Designer 12.2.1 · `sbscooker.exe` · graph openable.

---

## Graph density (M1)

- **~93 compNodes** (v1 was ~40-ish lean scaffold)
- Atomic filters: blend×32, levels×7, blur×4, sharpen×3, distance, warp, directionalwarp, normal, grayscaleconversion×4, uniform×16
- Package instances (flattened): `gaussian_spots_1`, `shape`, `histogram_scan`, `blur_hq_grayscale`
- All Melusina lookdev knobs dynamically wired (ShadowSpread, GouacheDepth, CurvatureOpacity, CymaticIntensity, BeatBoost, BrushStrokeIntensity, MetallicAccent, NormalStrength)

### What beats SimpleDiffuse_V2 (Melusina-only)

| Capability | SD_V2 | Melusina M1 |
|---|---|---|
| Soft diffuse / AO / curv / rim / strokes | ✓ | ✓ (denser fashion color stack) |
| Gouache Normal From Curvature (+ stroke + HQ blur) | — | **✓** |
| Moonglow cymatic Height/Emissive/Mask (procedural ± FrozenFracture) | — | **✓** |
| vcol_melodia mask outs (Wear/Decoration/Beat/Cymatic) | — | **✓** |
| BeatBoost × vcol.B stage-makeup emissive | — | **✓** |
| ORM pack + Melodia/Melusina shelf category | — | **✓** |

---

## Honesty

| Fact | Detail |
|---|---|
| 3740 B >> 2456 B | Valid cooked archive; real filters + instances. |
| Still < SD_V2 ~25 KB | Nhance product carries denser authored node/preset payload. Melusina M1 keeps **connectable inputs only** (no embedded cymatic PNG payloads) so artists bind MeshAO/Curvature/vcol/FrozenFracture in Painter — SBSAR stays lean bytecode. Embedding `T_Cymatic_*.png` would balloon size into 100KB–MB range without improving knob clarity. |
| Openable + cookable | Yes — Designer 12.2.1 XML + sbscooker exit 0. |
| ZenLantern defaults | Primary `#F5ECD7` · Secondary `#8B5E3C` · Accent `#FFC978` · Shadow cool grey-lavender |
| Not done | Fake SBSAR, Nhance IP clone, GrokBot naming, M2 SMS bind |

---

## ZenLantern plug map (showcase)

| Input | Bind |
|---|---|
| MeshAO | mesh AO bake |
| Curvature | curvature bake |
| vcol_melodia | Melodia vertex-color bake (R wear / G deco / B beat / A emissive) |
| CymaticHeight / CymaticOpacity | `resources\T_Cymatic_FrozenFracture_Height.png` + Opacity (optional; procedural rings already run) |
| BrushStrokeMap | optional NPR stroke |
| WorldNormal | optional light combine into gouache normal |

Dial: ShadowSpread, GouacheDepth, CurvatureOpacity, CymaticIntensity 0→hero, BeatBoost, NormalStrength.

---

## v3 deepen — 2026-10-05

| Artifact | v2 M1 | **v3** |
|---|---:|---:|
| `.sbs` source | 130,164 B | **149,484 B** |
| `.sbsar` cooked | 3,740 B | **4,410 B** |
| Painter shelf SBSAR | 3,740 B | **4,410 B** (refreshed 2026-10-05) |

Cook exit 0. New dynamically-wired params (gouache lookdev, cymatic rings, curvature tools):
`GouacheStrokeBreakup`, `GouacheBlur`, `GouacheSharpen`, `RingDistance`, `RingWarp`,
`RingSwirl`, `RingAngle`, `RingBandTightness`, `HistogramPosition`,
`CurvatureEdgeLight`, `CurvatureEmissive`.

Gouache height now tunable end-to-end (stroke breakup -> blur -> sharpen -> NormalStrength).
Curvature lane split into albedo edge-light + emissive edge-sparkle in addition to the
existing decoration/wear/gouache-height uses. Cymatic rings are fully characterable
(distance, warp, swirl, angle, band tightness, histogram scan).

**Brennan — pick up the v3 shelf SBSAR:** reload Painter resources (or restart), then
re-assign **Melusina Simple Diffuse** on Mr. Sheep's fill layer to expose the new knobs.

## Brennan — next open step

1. **Open** `SBS_Melusina_SimpleDiffuse.sbs` in Designer 12.2.1 — confirm graph, tweak ring Pattern/Tiling if desired, File → Publish .sbsar (or re-run `python build_sbs.py --cook`).  
2. **Reload** Painter shelf → drop Melusina Simple Diffuse on ZenLantern V2 Showcase → run GOAL §3 acceptance (thumbnail / close-up gouache / cymatic whisper / beat glance).  
3. **M2:** wire as fill engine in `SMS_Melusina_Handpaint` per `PAINTER_WIRE.md`.
