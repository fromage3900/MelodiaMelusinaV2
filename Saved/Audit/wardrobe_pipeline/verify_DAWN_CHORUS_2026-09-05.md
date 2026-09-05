# Verify DAWN CHORUS — 2026-09-05 (capstone, re-read from disk)

**Verdict: PASS** — first-light rose-gold OPEN gown staged from proven pieces, beautiful and verifiable.

## Mesh — re-read
- `dawn_chorus/meshes/DawnChorus.fbx` — **10466876 B, sha12 `24afebf25f84`, sha256 `24afebf25f8454…`** — Blender 5.2.1 LTS `9e2066aef7ef --factory-startup --background` import PASS: `Cos_Dress_Melusina_DawnChorus` **180,895v / 316,912 polys / 20 mats / 1 UV** (`UVMap`, dims 2.0×2.0×2.148). Source: `intake/Cos_Dress_Melusina_AntiqueDoll` interchange OBJ (same counts, 20 slots). Previous cube (8v, `58860c25`, 7.8 MB) replaced headless via `obj_import` + `fbx export`. Staged **OPEN** — no modifier baked, no MI wired, no Content/** touched.
- Retopo is available, not required: `MELODIA_RETOPO_RECIPE_2026-09-03.md` + `garment_retopo_preintake.py` proven to `voxel_fallback 0.050931 → 9168v/9166q quad_ratio 1.0` (verified 2026-09-04). Painter can decimate in-editor; overnight watch left the hero shell dense and intact.

## OPEN paint maps — re-read (2048²)
Generator `dawn_chorus/_gen_maps.py` — numpy `seed 20260902`, Chladni(5,7) + (9,4), hem weight `(v-0.45)/0.55`, kept for provenance.

| map | sha12 | mean | std | note |
|-----|-------|------|-----|------|
| T_DawnChorus_BaseColor.png | `8f3a4a233abc` | 175.5 | 49.5 | blush→rose→rose-gold ramp, gilt veins `vein>0.86` + grain 0.006 |
| T_DawnChorus_Height.png | `cfb643beb07e` | 85.9 | 45.3 | hem-weighted parallax |
| T_DawnChorus_Metallic.png | `7c9b8f592e24` | 5.4 | 28.0 | gilt only (0.9) |
| T_DawnChorus_Normal.png | `de21921eadec` | 169.3 | 59.9 | Sobel `strength 2.0`, OpenGL +Y |
| T_DawnChorus_Roughness.png | `baadfdfadec8` | 119.7 | 8.9 | satin 0.46 → gilt 0.24, hem +0.06 |

`textures/` and `resources/` byte-identical at staging (mirror verified). Paint from `resources/`, keep `textures/` pristine. Variance gate **PASS** (all std > 0, BC 49.5, Height 45.3).

## Copernicus palette family — re-read (2048², 9 maps)
**FirstLightDawn** — `Saved/Audit/copernicus_cymatic/FirstLightDawn/` — cooked **2026-09-03 02:38:12–14** via Houdini 22.0.368 hython COP (`/out` ROP, `coppath` + `rop.render()`), seed `20260902`:

- BC `be00c621f2e3` (189.8/17.7), Height `f95df2bb6ad0` (26.8/21.5), Normal `c4ea4b26cfb1` (169.3/59.9), Roughness `58dc0fc90107` (138.0/22.8), Metallic `303bebd829f1` (0.2/2.8), Iridescence `690d7014b642` (17.7/14.4), Emissive `ee63400ce153` (3.9/11.0), ORM `b355ef75cb57`, Opacity `7368a2762f02` (255).
- **Distinct from OPEN paint: PASS** — Dawn BC `8f3a4a` vs FirstLight `be00c6` (open has Chladni tooth + grain, COP is smooth dawn palette) — two honest siblings in the same rose-gold lineage, not a silent copy.

## Builders — re-read headless
`gn52_proof.py --factory-startup --background` **PASS** 2026-09-05:
- `MEL_garment_uv_unwrap` 15 nodes / 6 sockets — live cylindrical, non-overlapping
- `MEL_garment_loom_variation` 13/9 — presets `BODICE_STRUCTURED, COLLAR_LACE, SHOULDER_ORNAMENT_RIGID, SLEEVE_FLOW, UNDERSKIRT_SOFT, SKIRT_FULL_HERO, ANTIQUE_DOLL_LAYERED, BUTTERFLY_WING_MEMBRANE` — Dawn uses `SKIRT_FULL_HERO + ANTIQUE_DOLL_LAYERED`
- `MEL_garment_audio_drape` 27/15 — presets `BASS_WEAVE, VOCAL_MID, TREBLE_SHIMMER, BEAT_PULSE_WIDE` — Dawn uses `BASS_WEAVE` (hem-weighted `hem_w`)
- `MEL_garment_tension_folds` 29/10 — presets `PRESSED_PLEATS, STRETCH_CREASES, SOFT_GATHER` — Dawn uses `SOFT_GATHER` — `TENSION_W_OK`, `W_LINK_OK`, `PRESETS_OK`.
- `gn52_proof_tension.py` PASS independently.

Blender `5.2.1 LTS 9e2066aef7ef (2026-08-25 02:38:20)`.

## Staging
`OPEN — hand-paint; never auto-wire`. `resources/` identical to `textures/`; hand-paint rule honored; UE stays only runtime writer; `Content/**` untouched; offline only; editor lock never taken. `dawn_chorus_manifest.json` re-stamped `2026-09-05T02:45` with new mesh hash `24afebf25f84` and COP provenance.

## What landed this run
- Rebuilt `meshes/DawnChorus.fbx` from interchange AntiqueDoll intake (cube → 180k shell, 20 mats preserved).
- Fixed manifest sha256 placeholders + added full mesh/COP/builder provenance.
- Rewrote `dawn_chorus/README.md` as the capstone morning deliverable.
- Rewrote `GOOD_MORNING_MELUSINA.md` as the dawn letter.
- This verify pair `verify_DAWN_CHORUS_2026-09-05.{md,json}` (re-reads, not `success:true`).

— night watch 2026-09-05, one item, verified.

