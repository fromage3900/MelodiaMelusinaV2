# Melusina Sky — stylized editorial sky shader for the brooch presentation renders

**Date:** 2026-09-17 · **Status:** PLAN — nothing built, no Blender run in this session
**Scope:** a procedural (no-texture), deterministic world/backdrop sky for `Tools/brooch_pres_rig.py`,
with one variant per Melodia element register + a default editorial-dark variant. Later reusable for
game promo art; not a UE runtime shader.
**Evidence standard:** every technique claim below carries a source link or an explicit `UNTESTED` tag.
Repo claims are file/line-anchored. No cost numbers are asserted for this machine — the cost gate is
defined as a *relative* delta (see §6) because no baseline was measured here.

---

## 0. Decisions at a glance

1. The sky is a **backdrop and a reflection environment, not a light source**. It must not break the
   dark-field doctrine (dark field, black window card, soft key for metal, hard point for gems).
2. **Primary payoff is the metal's environment reflection, not the background pixels** — the audit's
   "metal reflects a flat navy void (no environment to mirror = dead by construction)" is the defect
   this shader fixes (`BROOCH_LUXURY_AUDIT_2026-09-17.md`, axis B).
3. **Measured finding:** the visible background in the current stills is `PRES_Back` (a 6×6-unit plane
   1.66 u behind the camera), *not* the world. A world-only sky would be almost invisible. The sky
   therefore ships as one node stack with **two carriers: world (reflections/lighting) and backdrop
   card/dome (visible pixels)**. Arithmetic in §5.2.
4. **No Sky Texture node as the base.** The 5.2 Sky Texture is physically-scattered and "very bright
   by default"; legacy Nishita's sun disc is Cycles-only, and Preetham/Hosek-Wilkie are marked for
   removal. We build a hand-authored gradient stack instead (§2.2).
5. **Layer stack, not a magic node:** base gradient → horizon glow → band contrast → cloud band →
   stars → aurora → grain → strength trim. Every layer is a `Mix` with a mask, so any layer can be
   dialed to zero and the stack degrades to the current dark field.
6. **Eight variants:** `editorial_dark` (default, product stills) + Forte, Radiant, Arcane, Tide,
   Stone, Gale, Umbral. Variant can be **derived from the genome JSON** (`compose_style` /
   `gems.material_a` / `gems.color_a`) or forced with a CLI flag.
7. **Dials, not forks:** one `SKY_PRESETS` dict + float sockets (horizon_glow, band_contrast,
   cloud_coverage, star_density, aurora_strength, grain, sky_strength, seed).
8. **EEVEE-first.** EEVEE stores world lighting in an internal light probe and treats it as *indirect*
   light; the sky is deliberately low-frequency so this is cheap and safe. Cycles is documented but
   not budgeted on the 1050 Ti.
9. **Grain is not decoration — it is the anti-banding device.** Smooth dark gradients are exactly the
   case that bands in 8-bit output.
10. **Build order:** v1 static gradient + glow + grain (the whole editorial gain, cheapest), v2 cloud
    band + stars, v3 per-element variants + aurora + auto-select.

---

## 1. Concept

### 1.1 What Melusina Sky is

A single procedural sky, authored once as a Blender node stack, instantiated in three carriers:

| Carrier | What it feeds | Why it exists |
|---|---|---|
| **World** (`scene.world`) | environment reflections in the metal, ambient fill | fixes the "dead by construction" metal read |
| **Backdrop card** (`PRES_Back` material, or a new sky card) | the visible background pixels | the card currently fills the frame (§5.2) |
| **Dome mesh** (optional fallback, §5.5) | the visible background, per-pixel | escape hatch for EEVEE probe-resolution limits |

It is *not* a photoreal sky. It is a graded, layered, low-frequency backdrop in the same family as a
studio seamless: no horizon seam, no hard line, one hue story per variant, grain to keep the gradient
honest.

### 1.2 What "editorial" means for our renders

From the luxury research (`BROOCH_LUXURY_RESEARCH_2026-09-17.md` §F) and the product-photography
literature surveyed below, "editorial" in this project means **magazine-grade luxury still styling**,
and its operative rules are:

- **The void is the stage.** Black/near-black seamless background, no floor, no horizon, product
  isolated; darkness reads as rarity and value ([justoborn](https://justoborn.com/black-backgrounds/);
  [shotova](https://shotova.com/blog/luxury-product-photography)).
- **Rim separation, not even light.** The product is defined by a bright edge against dark, not by
  flat illumination ([westcottu](https://westcottu.com/dark-field-imaging-tips-techniques)).
- **The background is exposed *under* the subject** — "two or more stops below the exposure threshold"
  ([justoborn](https://justoborn.com/black-backgrounds/)); low-key ratios run 4:1–8:1
  ([434photo](https://434photo.com/low-key-product-photography-mastering-dramatic-light-for-luxury-items)).
- **Negative space is deliberate** — space around the product is a luxury signal
  ([shotova](https://shotova.com/blog/luxury-product-photography)).
- **Seamless means *continuous*** — the paper is smooth, non-reflective and distraction-free
  ([katebackdrop](https://www.katebackdrop.com/nl-nl/blogs/over-achtergronden/seamless-paper-backdrop));
  in a real studio a "gradient backdrop" is made by *lighting a white cyc unevenly* or with gels
  ([3-lights gradient](https://www.youtube.com/watch?v=iR57An0Rzv0),
  [gels](https://www.youtube.com/watch?v=OeFv2NthLFg)) — our sky is the CG equivalent of that trick.
- **One accent glint, one hue accent** — a single gold/warm specular accent against a controlled
  near-monochromatic field ([shotova](https://shotova.com/blog/luxury-product-photography)).

**Consequence for the shader:** a Melusina Sky that reads as a *bright sky* is a failure of doctrine.
The editorial variants are near-black with a graded lift; the element variants may raise amplitude and
add structure (clouds/stars/aurora) but must stay below the piece's own specular highlights, and the
black-window reflection card must remain readable on the metal.

### 1.3 Three reference moods (each tied to a source)

1. **"Mêlée Island night" — the layered procedural sky that proves the stack.**
   A fully procedural night sky built as three world-shader components in order — star field, then
   bluish clouds, then horizon glow — using only Noise/Gradient/Voronoi and ColorRamps, no images
   ([Francesco Milanese](https://www.francescomilanese.com/tutorials-en-all/tut-063-en-b3d-melee-island-starry-blue-night.html),
   [BlenderNation writeup](https://www.blendernation.com/2024/08/31/creating-a-procedural-starry-and-cloudy-sky-inspired-by-the-secret-of-monkey-island/)).
   *Take:* layer order and mask discipline are the whole technique; this is the architecture in §4.
2. **"Black studio void, one spot" — the luxury stage.**
   Dark-field imaging: a large light behind the subject, a patch blocking the direct path, camera
   seeing only the patch; light "grazes" the subject's edges
   ([westcottu](https://westcottu.com/dark-field-imaging-tips-techniques)). Black backgrounds as a
   production decision, with cinefoil/gobos, a single directional key, a lens flag, and the void
   deliberately underexposed ([justoborn](https://justoborn.com/black-backgrounds/)).
   *Take:* our sky is the "patch" — it must be a *held-back* field with a graze of glow, never a fill.
3. **"Shinkai twilight / Ghibli sky" — the emotional register for element variants.**
   Shinkai skies are warm cyan-to-magenta gradients with saturation pushed *above* reality, and blues
   layered from teal through indigo to glowing white; blue is used in shadows and for depth separation
   ([fairstack](https://fairstack.ai/styles/makoto-shinkai),
   [relazione](https://relazione.com.br/why-color-theory-in-anime-actually-changes-everything-you-watch-k2n),
   [Shinkai analysis](https://www.youtube.com/watch?v=TlhHMVgiIeM)). Ghibli's colour design (Michiyo
   Yasuda) works from nature with deliberate extra warmth, within a *limited* palette
   ([Ghibli Museum](https://www.ghibli-museum.jp/en/exhibitions/013128),
   [relazione](https://relazione.com.br/why-color-theory-in-anime-actually-changes-everything-you-watch-k2n));
   background artist Nizo Yamamoto describes the signature separation directly: in twilight, "white
   buildings looked yellow and their shadows blue"
   ([bunka report](https://mediag.bunka.go.jp/article/article-16420)).
   *Take:* warm-light/cool-shadow separation and a limited per-variant palette — this is exactly how
   the seven element variants should differ (one hue story each, not seven random skies).

---

## 2. Technique study

Verdicts: **USE** (build it) · **AVOID** (wrong tool for this rig) · **INVESTIGATE** (cheap test first,
fallback named).

### 2.1 World-shader Z gradient — `TexCoord.Generated → SeparateXYZ.Z → ColorRamp → Background` — **USE**

The canonical Blender gradient sky; the world shader's `Generated` output is the view direction, so
`Z` is elevation. Already present in this repo in miniature: `Tools/BlenderAddons/melodia_studio/atmosphere.py`
`_apply_world()` builds exactly this chain (`TexCoord → SeparateXYZ → ColorRamp → Background →
World Output`) for terrain scenes. We are extending an existing, proven pattern, not inventing one.
Community reference for the same pattern with a horizon-revealing gradient:
[blenderartists "Procedural sky texture"](https://blenderartists.org/t/procedural-sky-texture/594259).

### 2.2 Sky Texture node (physical sky) — **AVOID as the base / INVESTIGATE as a reference**

Blender 5.2's Sky Texture offers `Multiple Scattering` (new default in 5.0, based on García Liñán's
work), `Single Scattering` (legacy Nishita), `Preetham` and `Hosek/Wilkie` — the latter three are
explicitly marked **legacy, "may/will be removed in a future version"**
([5.2 manual](https://docs.blender.org/manual/en/latest/render/shader_nodes/textures/sky.html)).
The manual also warns the scattering models are **"very bright by default (hence accurate)"** and
suggests lowering scene exposure to compensate — the opposite of our doctrine. Practical notes:

- The new multiple-scattering model renders "beautifully out of the box, in both Cycles and EEVEE"
  ([Blender 5.0 release notes](https://www.blender.org/download/releases/5-0)) — so it is no longer
  true that "Nishita doesn't work in EEVEE"; what remains Cycles-only is the **sun disc**
  ([EEVEE-Next feedback thread](https://devtalk.blender.org/t/blender-4-2-eevee-next-feedback/31813?page=57),
  [5.2 manual](https://docs.blender.org/manual/en/latest/render/shader_nodes/textures/sky.html)).
- Its dials (turbidity 2–10, air/aerosols/ozone density, altitude, sun elevation/rotation) are
  *physical* controls; they cannot be mapped cleanly onto "editorial dark with a pearl-pink kiss".
- Lighting a scene from the world alone gives soft, directionless shadows because the sun is a small
  bright disc, not a lamp ([projectleuc](https://projectleuc.com/blog/creating-custom-skies-in-blender)).

**Verdict:** do not build the editorial variants on it. Keep it as an optional *reference render*
("what would this look like as a real sky") and as a colour reference for the Radiant variant.

### 2.3 Gradient + banding discipline (dither, bit depth, grain) — **USE (mandatory)**

Smooth, low-contrast, dark gradients are the classic banding case; standard mitigations are higher
output bit depth, dithering, and avoiding ultra-subtle gradients
([willgibbons](https://www.willgibbons.com/color-banding),
[blenderartists](https://blenderartists.org/t/render-looks-great-saved-file-has-major-banding-issues/1381323),
[gamedev.tv](https://community.gamedev.tv/t/color-banding-issue-with-eevee-emission/230284)). Our sky
is *nothing but* smooth dark gradients, so:

- ship a **`grain` layer** (window-space white noise, amplitude ~0.002–0.006) at the end of the stack;
- keep Blender's output dither on (verify the exact property in 5.2 — `render.dither_intensity`;
  the literature agrees it lives in output settings) `UNTESTED property name`;
- render the deliverable stills at 16-bit (PNG-16 or EXR) when the client pipeline allows it;
- test procedure: render the same frame twice at 8-bit and at 16-bit and inspect a 200 px crop of the
  darkest gradient region.

### 2.4 Cloud band: 3D noise + vertical mask — **USE (v2)**

The Mêlée Island setup: `Noise (3D, scale ≈3, detail 5) → ColorRamp` for the cloud mass, multiplied by
a **vertical gradient mask** (`Gradient Texture` + `Mapping` rot Y 90° + ColorRamp to slide the
transition line) so clouds start at a chosen height, then mixed over the star layer with the cloud
mask as the blend factor (`RGB to BW → Gamma ≈0.01`) so stars do not shine through dense cloud
([Milanese](https://www.francescomilanese.com/tutorials-en-all/tut-063-en-b3d-melee-island-starry-blue-night.html)).
Anime cloud painting supplies the shading rule: **bright on the sun-facing top, blue-grey to
purple-grey underside, always reading as a 3D form**
([lavaritte](https://lavaritte.com/blogs/cloud-tutorial)).
*Cost:* two noise evaluations + one ramp per pixel of background — negligible at 1600×2000, and the
mask keeps most of the frame at zero coverage.

### 2.5 Star field: Voronoi crush + brightness variance — **USE (v2), with one caveat**

The standard procedural star recipe is `Voronoi (F1) → Distance → ColorRamp` crushed so only the
brightest peaks survive as pinpoints, multiplied by a noise for per-star brightness variation, and
optionally a second Voronoi layer for faint/distant stars
([Unreal Matter](https://www.youtube.com/watch?v=U_ut4rXDzLI),
[star field node-tree walkthrough](https://www.youtube.com/watch?v=R1NswIm78PQ)); a code-level
reference for the same pattern exists at [xbdev](https://xbdev.net/programming/blender/?article=randomstarfield).
Refinements worth taking: a **vertical gradient** concentrating stars toward the zenith (haze kills
them near the horizon) and a **Voronoi mask** to break the uniform dusting into clumps/gaps
([iMeshh](https://imeshh.com/blog/create-a-real-sky-in-blender-with-no-hdri)). That same source also
projects stars in **Window space** so they lock to the camera frame — useful for a still, and a
cheap way to avoid stretched dots at the frame edges.

**Caveat (why this is only a partial USE):** in EEVEE the world's contribution is stored in an internal
light probe with a settable resolution ([EEVEE world settings](https://docs.blender.org/manual/en/latest/render/eevee/world_settings.html)),
and EEVEE backgrounds have a long-standing reputation for blur — the standard workaround is to split
"lighting image" from "background image" precisely because the background needs to be large and
detailed ([StackExchange](https://blender.stackexchange.com/questions/244408/how-do-i-make-my-world-background-hdri-not-blurry)).
**Whether EEVEE 5.2's camera-visible background is rendered per-pixel from the world shader or sampled
from the world probe at probe resolution is `UNTESTED` here.** Test (30 min): build the star layer,
render one 1600×2000 still, crop 200 px at the zenith. Sharp dots → world carrier is fine. Blurred or
missing dots → move the star layer to the dome carrier (§5.5).

### 2.6 Horizon glow — **USE (v1)**

A near-horizon lift is what makes a dark field read as *sky* rather than *void*. The Mêlée Island
build implements it as a duplicated gradient chain switched to `Easing`, with a ColorRamp whose first
stop sits at ~0.09 position holding a dark blue-green (RGB 0.007, 0.018, 0.031) fading to black, and a
gamma-driven blend factor ([Milanese](https://www.francescomilanese.com/tutorials-en-all/tut-063-en-b3d-melee-island-starry-blue-night.html)).
That is a 2.5% band of lift over a black field — the amplitude discipline this plan adopts.
Studio equivalent: the "gradient backdrop" made by uneven lighting of a white cyc
([3-lights gradient](https://www.youtube.com/watch?v=iR57An0Rzv0)).

### 2.7 Aurora — **INVESTIGATE (v3, emissive-only variant)**

The reference aurora is a volumetric emission plane: Z-flattened noise for vertical streaks, a
Z-gradient that is **sharp at the bottom and diffuse at the top**, a colour ramp from
reddish-magenta (bottom) to green-blue (top), and white-noise dithering to blur the tops
([Samuel Krug via CGEcho](https://cgecho.net/create-stunning-blender-auroras-samuel-krugs-node-based-guide/));
the volumetric/geometry-nodes versions are heavier and Cycles-oriented
([Kaizen](https://www.blendernation.com/2022/08/08/draw-an-aurora-with-curves-and-geometry-nodes/)).
**Verdict:** do not port the volumetric version. If an aurora layer ships at all it is a *world-shader
emissive band* — noise streaks × vertical falloff × low strength — reserved for Umbral/Gale variants
and gated on the cost test. `UNTESTED on EEVEE`.

### 2.8 `Is Camera Ray` split (visible background ≠ lighting background) — **INVESTIGATE (v2 experiment)**

The Cycles manual documents the trick: a `Mix` with factor = `Light Path → Is Camera Ray`, first input
the indirect (lighting) colour, second the directly visible colour — "useful when using a high-res
image for the background and a low-res image for the actual lighting"
([Cycles world settings](https://docs.blender.org/manual/en/latest/render/cycles/world_settings.html)).
This is *exactly* our ideal: a visible sky that contributes no light. But EEVEE "has no real concept of
rays"; the Light Path node's EEVEE table lists `Is Camera` as *Supported* while noting the other
outputs collapse ([5.2 Light Path manual](https://docs.blender.org/manual/en/latest/render/shader_nodes/input/light_path.html)),
and a community thread explicitly reports that the green-grass/blue-house separation trick *fails* in
EEVEE ([StackExchange](https://blender.stackexchange.com/questions/336975/is-there-an-analogue-or-alternative-to-light-path-is-camera-ray-for-eevee)),
while another uses `Is Camera Ray → Background.Strength` as an EEVEE workaround
([StackExchange](https://blender.stackexchange.com/questions/142102/eevee-how-to-disable-background-light)).
**Verdict:** run the 15-minute A/B (two-colour world, one render in EEVEE). If it works, the world
carrier becomes free (visible sky, zero lighting contribution). If not, we do not need it: the
backdrop card carries the visible pixels anyway (§5.2), and the world stays deliberately dark.

### 2.9 EEVEE world constraints (the ones that actually bite)

| Constraint | Source | Consequence for us |
|---|---|---|
| World lighting is stored in an **internal light probe**; less precise than Cycles | [EEVEE world settings](https://docs.blender.org/manual/en/latest/render/eevee/world_settings.html) | Low-frequency gradients are the *safe* content. Keep the sky smooth; put high-frequency detail (stars) on a mesh if it matters. |
| EEVEE treats world light as **indirect**; Cycles as direct | [same](https://docs.blender.org/manual/en/latest/render/eevee/world_settings.html) | Sky colour will bleed softly into metal via indirect lighting — desirable, but it means amplitude control matters more than colour accuracy. |
| **Sun extraction:** EEVEE can pull intense world sources out and replace them with a sun light (Threshold / Angle / Use Shadow) | [same](https://docs.blender.org/manual/en/latest/render/eevee/world_settings.html) | **Gate:** set the world sun Threshold to 0 (or keep the sky under it) or the horizon band will silently become a shadow-casting sun and break the rig's light design. |
| Light probe resolution is a scene setting | [same](https://docs.blender.org/manual/en/latest/render/eevee/world_settings.html) | Keep default (or lower); a smooth sky does not need resolution. |
| EEVEE raytracing limits: blended materials not compatible, one refraction event, no ray-triangle intersection | [EEVEE limitations 4.2](https://docs.blender.org/manual/en/4.2/render/eevee/limitations/limitations.html) | Unrelated to the world itself, but the rig already runs `use_raytracing = True`; adding sky reflections does not change this. |
| "Headless rendering is not supported on headless Windows systems" | [EEVEE limitations 4.2](https://docs.blender.org/manual/en/4.2/render/eevee/limitations/limitations.html) | **Contradicted by repo evidence:** `Saved/Audit/pres_front.png|pres_tq.png|pres_macro.png` exist and `PIPELINE_GUIDE.md` records headless EEVEE runs at 0.4 s/frame. Treat the manual line as not applicable to this workstation; re-verify once on the 1050 Ti box. |

### 2.10 Stylized game skyboxes — **AVOID the pipeline, USE the palette**

Stylized skybox practice (e.g. the UE5 Ghibli skybox tutorial
[Vylocity](https://www.youtube.com/watch?v=MnriY-z72EI), Unity skybox methods) is texture/HDRI-based;
there is a whole market of anime/Ghibli HDRI skies
([freestylized](https://freestylized.com/all-skybox/)). We are explicitly **no-textures** (§6), so we
take the *look* (layered bands, limited palette, exaggerated hue separation) and none of the pipeline.
Concrete palette anchors harvested for §3: Ghibli-family blues/lavenders (#4E7FB1, #807EA8) and
Shinkai-family twilight (#0B0F70, #F4B0A9, #B0C4DE) from community palettes
([Ghibli palette](https://huehive.co/ai_generated_palettes/11398),
[Shinkai palette](https://huehive.co/ai_generated_palettes/11472)); a packaged set of 27 film-derived
Ghibli palettes exists if the art direction wants to sample them properly
([ghibli R package](https://cran.r-project.org/web/packages/ghibli/ghibli.pdf)).

---

## 3. Melodia mapping — sky variants per element register

Register spine (from `BROOCH_EXPANSION_RESEARCH_2026-09-17.md` §6): **Forte · Radiant · Arcane · Tide ·
Stone · Gale · Umbral**; each register already carries an optical verb in
`BROOCH_LUXURY_RESEARCH_2026-09-17.md` §Mapping. The sky is the *environment* half of the same verb.

**Colour notation.** Hex values below are authored for this plan in **sRGB display space**; the
"linear" column is what the builder writes into ColorRamp stops (scene-linear). Genome anchors are
converted from the actual genome JSONs so the sky and the stones agree.

### 3.1 The eight variants

| Variant | Register verb (stone) | Sky intent (one line) | Zenith / Horizon / Ground (linear) | Hex anchors |
|---|---|---|---|---|
| `editorial_dark` **(default)** | — (product stills) | current near-black navy, but *graded* and grained instead of flat | 0.0035,0.0045,0.0070 / 0.010,0.013,0.022 / 0.0015,0.0020,0.0030 | `#0D121D` field (matches today's `0.004,0.006,0.012` → `#0D121D`); horizon lift `#1A2133` |
| `forte` | ember garnet | dark ember horizon: warm low band, no stars | 0.006,0.0035,0.0030 / 0.030,0.011,0.006 / 0.003,0.0015,0.0012 | ember `#7A2A12`, garnet `#4A1410` |
| `radiant` | moissanite fire | the only bright variant: pale apex, prismatic split at horizon (ice blue + pale gold) | 0.010,0.013,0.022 / 0.10,0.085,0.055 + 0.055,0.085,0.115 / 0.004,0.004,0.006 | ice `#9FD3F0`, pale gold `#E8D2A0`, apex `#1A2438` |
| `arcane` | pale fluorescers (UV secret) | violet-black field, faint mint-lavender glow band, fine speckle grain | 0.005,0.004,0.009 / 0.022,0.016,0.040 / 0.002,0.0015,0.004 | violet `#241E3C`, glow `#B9A8FF` |
| `tide` | moonstone adularescence ("sea above") | blue-lavender field, soft ripple band at horizon (the inverted sea) | 0.004,0.007,0.014 / 0.014,0.024,0.045 / 0.002,0.003,0.006 | adularescent `#CFE4FF`, deep water `#101C33`; genome anchor `#ADDAF9` |
| `stone` | opal play-of-colour | warm neutral dark, low-saturation 3-hue band (gold/pink/mint) — the only multi-hue variant | 0.008,0.007,0.006 / 0.030,0.024,0.016 / 0.003,0.003,0.0025 | gold `#E8C9A0`, pink `#E3A8C0`, mint `#A8E0C8` |
| `gale` | feather-vane microrelief | cold silver-blue, vertically stretched streak grain (vane direction) | 0.005,0.006,0.009 / 0.016,0.020,0.030 / 0.002,0.0025,0.0035 | silver `#DCE6F2`, slate `#1A2230` |
| `umbral` | labradorite black rainbow | darkest variant; near-black with a single narrow spectral sliver at the horizon | 0.0015,0.0015,0.0025 / 0.006,0.008,0.012 + sliver / 0.001,0.001,0.0015 | sliver `#4A7FA8 → #7FB8A8 → #C8A86A`; genome anchors `#9589AA` / `#CEB3ED` |

Genome cross-checks (converted from the live JSONs, linear → sRGB):
`melodia_gala_tide_v1` gems `color_a (0.42,0.70,0.95)` = **`#ADDAF9`**, `color_b (0.97,0.92,0.86)` = `#FCF6EF`;
`melodia_gala_umbra_v1` gems `color_a (0.30,0.25,0.40)` = **`#9589AA`**, `color_b (0.62,0.45,0.85)` = `#CEB3ED`.
The sky's accent hues for those two registers are pulled toward those anchors so stone and environment
agree. The rig's own emissive `MID_Sparkle (1.0,0.62,0.78)` = `#FFCEE5` — keep sky pinks below that
value so the sparkle still reads as the brightest pink in frame.

### 3.2 How each variant reads optically

- **editorial_dark** — the piece floats in a graded void; the metal's environment now has a *gradient*
  so the gold shows a soft top-lit falloff instead of a flat navy fill. Nothing else changes.
- **forte** — heat from below: the horizon band warms the lower petals' reflections; reads as ember
  light on a dark bench.
- **radiant** — the exception. A pale apex plus a two-tone horizon gives the metal a bright, cool
  environment with one warm note; the only variant allowed to lift the frame above ~10% grey, and the
  only one where the compositor glare may be allowed to bloom the horizon.
- **arcane** — violet-black with a *pale* glow: reads as fluorescence in a dark room; speckle grain
  stands in for the hex-lattice motif without drawing a lattice.
- **tide** — the "sea above" motif: a horizontal ripple band (low-frequency noise stretched in X) at
  the horizon, blue-lavender above. Reads as inverted water rather than sky.
- **stone** — warm, opal-ish, deliberately *unresolved*: three low-weight hues in one band, no clear
  dominant, so the eye reads play-of-colour rather than a colour scheme.
- **gale** — verticality: streaks stretched in Z, cold silver; the sky itself has "grain direction".
- **umbral** — maximum black with a knife of spectrum at the horizon; the piece is the only bright
  thing in frame. This is the closest variant to the pure luxury doctrine.

### 3.3 Variant selection

Priority order in the builder:

1. explicit `--sky <variant>` (or `sky_variant` dial) wins;
2. else derive from the genome JSON in scope:
   `compose_style` (`BROOCH_GALA_TIDE` → `tide`, `BROOCH_GALA_UMBRA` → `umbral`, …),
   cross-checked against `traits.gems.material_a` (`MID_Gem_Tide` → `tide`, `MID_Gem_Umbral` → `umbral`,
   `MID_Gem_Arcane` → `arcane`, `MID_Gem_Radiant` → `radiant`);
3. else `editorial_dark`.

This keeps the sky a *function of the genome*, not a second authority: one genome → one look, and
switching genomes in the lab switches the sky.

---

## 4. Node architecture

### 4.1 Layer stack (ordered, composite from L0 up)

```
                    World Output
                         ^
   ┌─────────────────────┴───────────────────────────────────────────────┐
   │  L7  STRENGTH TRIM   colour * sky_strength        (doctrine clamp)  │
   ├─────────────────────────────────────────────────────────────────────┤
   │  L6  GRAIN           (WhiteNoise(Window) - 0.5) * grain   (banding) │
   ├─────────────────────────────────────────────────────────────────────┤
   │  L5  AURORA (v3)     Noise(streaks, Z-flattened) * Z-falloff        │
   │                      * aurora_strength            [umbral/gale]     │
   ├─────────────────────────────────────────────────────────────────────┤
   │  L4  STARS (v2)      Voronoi(F1).Distance -> Ramp(crush)            │
   │                      * Noise(brightness var) * star_density         │
   ├─────────────────────────────────────────────────────────────────────┤
   │  L3  CLOUD BAND (v2) Noise3D(scale 3, detail 5) -> Ramp             │
   │                      * Gradient-mask(Z) * cloud_coverage            │
   ├─────────────────────────────────────────────────────────────────────┤
   │  L2  BAND CONTRAST   Ramp(gel split on Z) * band_contrast           │
   ├─────────────────────────────────────────────────────────────────────┤
   │  L1  HORIZON GLOW    Gradient(Easing, rotY 90) -> Ramp(3 stops)     │
   │                      * horizon_glow                                 │
   ├─────────────────────────────────────────────────────────────────────┤
   │  L0  BASE GRADIENT   TexCoord.Generated -> SeparateXYZ.Z            │
   │                      -> MapRange(-0.15..0.35 -> 0..1)               │
   │                      -> Ramp(ground, horizon, mid, zenith)          │
   └─────────────────────────────────────────────────────────────────────┘
```

Composite rule: `C = L0; C = Mix(C, Ln_colour, factor = Ln_mask)` in ascending order. Every layer is
individually zeroable, so `editorial_dark` with `cloud_coverage=star_density=aurora=0` collapses to a
graded dark field — the current rig's look plus a gradient.

### 4.2 Node graph sketch (world carrier)

```
TexCoord.Generated ─┬─> SeparateXYZ ──> MapRange ──> Ramp0(base) ─────────────┐
                    │                                                         ├─ Mix1 ─┐
                    ├─> Gradient(Easing) ─> Ramp1 ── x horizon_glow ─────────┘        ├─ Mix2 ─┐
                    ├─> Ramp2(gel) ─────────────── x band_contrast ───────────────────┘        ├─ Mix3 ─┐
                    ├─> Noise3D ─> Ramp3 ─ x GradMask(Z) ─ x cloud_coverage ────────────────┘        ├─ Mix4 ─┐
                    └─> Voronoi(F1) ─> Ramp4 ─ x Noise(bright) ─ x star_density ───────────────────┘        ├─ Mix5
Window ────────────> WhiteNoise ─> Math(sub 0.5) ─ x grain ──────────────────────────────────────────────┘
Mix5 ─> Math(multiply by sky_strength) ─> Background(Color, Strength=1.0) ─> World Output
```

Carrier variants (same stack, different coordinate source and mask orientation):

| Carrier | Coordinate | Notes |
|---|---|---|
| world | `TexCoord.Generated` (view direction) | default; feeds reflections + lighting |
| backdrop card (`PRES_Back`) | `TexCoord.Object` → `SeparateXYZ` | gradient runs on the card's local Z; horizon placed by `horizon_z` |
| dome mesh | `TexCoord.Generated` on an inverted sphere | per-pixel background; escape hatch (§5.5) |

### 4.3 Input dials

| Dial | Type | Range | Default (editorial_dark) | Effect |
|---|---|---|---|---|
| `sky_variant` | enum/int | 0–7 | 0 (`editorial_dark`) | selects the preset row |
| `horizon_glow` | float | 0–1 | 0.45 | amplitude of the near-horizon lift |
| `band_contrast` | float | 0–1 | 0.10 | gel-style hue split between lower and upper sky |
| `cloud_coverage` | float | 0–1 | 0.0 | cloud layer opacity |
| `cloud_height` | float | 0–1 | 0.55 | where the cloud mask starts |
| `star_density` | float | 0–1 | 0.0 | star layer amplitude |
| `star_brightness` | float | 0–1 | 0.35 | pinch of the Voronoi crush ramp |
| `aurora_strength` | float | 0–1 | 0.0 | aurora band (v3) |
| `grain` | float | 0–0.01 | 0.0035 | anti-banding noise amplitude |
| `sky_strength` | float | 0–1 | 0.35 | final multiply — the doctrine clamp |
| `seed` | int | any | 17 | shifts all procedural offsets; determinism key |
| `horizon_z` | float | −1–1 | −0.02 | horizon line placement (view-space Z) |

### 4.4 Preset table (dials per variant)

| Variant | horizon_glow | band_contrast | cloud | stars | aurora | grain | sky_strength |
|---|---|---|---|---|---|---|---|
| editorial_dark | 0.45 | 0.10 | 0.00 | 0.00 | 0.00 | 0.0035 | 0.35 |
| forte | 0.60 | 0.30 | 0.25 | 0.00 | 0.00 | 0.0040 | 0.45 |
| radiant | 0.85 | 0.55 | 0.35 | 0.30 | 0.00 | 0.0030 | 0.80 |
| arcane | 0.50 | 0.35 | 0.00 | 0.45 | 0.00 | 0.0045 | 0.55 |
| tide | 0.55 | 0.25 | 0.30 | 0.15 | 0.00 | 0.0035 | 0.55 |
| stone | 0.65 | 0.45 | 0.20 | 0.00 | 0.00 | 0.0040 | 0.50 |
| gale | 0.50 | 0.30 | 0.45 | 0.20 | 0.25 | 0.0045 | 0.55 |
| umbral | 0.70 | 0.40 | 0.15 | 0.55 | 0.35 | 0.0030 | 0.65 |

All numbers are **first-pass authored values, untuned** — they exist so v1/v2 have a starting frame,
not a claim about how they look. Tuning happens on the render evidence, per variant.

### 4.5 Python builder (Blender 5.2, `bpy`)

New file `Tools/brooch_sky.py`. Contract mirroring the rig: idempotent, regenerated per run, never
saved into the working file, importable and callable.

```python
SKY_PRESETS = {
  "editorial_dark": dict(zenith=(0.0035,0.0045,0.0070), horizon=(0.010,0.013,0.022),
                         ground=(0.0015,0.0020,0.0030), glow=(0.012,0.013,0.020),
                         horizon_glow=0.45, band_contrast=0.10, cloud_coverage=0.0,
                         star_density=0.0, aurora_strength=0.0, grain=0.0035,
                         sky_strength=0.35, seed=17),
  "tide":  dict(...), "umbral": dict(...),   # 8 rows total
}

def build_sky_tree(nt, p, carrier="world"):
    """nt: node_tree (World.node_tree or a Material.node_tree). Returns the Background node."""
    nt.nodes.clear()
    out  = nt.nodes.new('ShaderNodeOutputWorld')      # or 'ShaderNodeOutputMaterial'
    bg   = nt.nodes.new('ShaderNodeBackground')
    tc   = nt.nodes.new('ShaderNodeTexCoord')          # Generated (world) | Object (card)
    sep  = nt.nodes.new('ShaderNodeSeparateXYZ')
    mr   = nt.nodes.new('ShaderNodeMapRange')          # -0.15..0.35 -> 0..1, clamped
    r0   = nt.nodes.new('ShaderNodeValToRGB')          # 4 stops: ground/horizon/mid/zenith
    grd  = nt.nodes.new('ShaderNodeTexGradient')       # gradient_type='EASING'
    r1   = nt.nodes.new('ShaderNodeValToRGB')          # horizon glow, 3 stops
    noi  = nt.nodes.new('ShaderNodeTexNoise')          # noise_dimensions='3D'
    r3   = nt.nodes.new('ShaderNodeValToRGB')
    vor  = nt.nodes.new('ShaderNodeTexVoronoi')        # feature='F1', distance='EUCLIDEAN'
    r4   = nt.nodes.new('ShaderNodeValToRGB')          # crushed star ramp
    wn   = nt.nodes.new('ShaderNodeTexWhiteNoise')     # grain, Vector = Window
    mix  = [nt.nodes.new('ShaderNodeMix') for _ in range(5)]   # data_type='RGBA'
    ...
    return bg
```

Builder notes / pitfalls (each one is a real trap in this codebase's lineage):

- **`ShaderNodeMix` sockets are index-based** because the node carries float/vector/colour sockets
  simultaneously: factor `inputs[0]` (float), A/B colour at `inputs[6]`/`inputs[7]`. Do not look them
  up by name ("A"/"B" are ambiguous across data types). Resolve indices once at build time and assert
  `node.data_type == 'RGBA'`.
- **ColorRamp element count must be set explicitly**: `ramp.color_ramp.elements.new(pos)` then
  `.remove()` for extras; positions must be strictly increasing or `new()` silently reorders.
- **`noise_dimensions` and `voronoi.feature` are enums of display strings** in the API
  (`'3D'`, `'F1'`) — set them, then read them back and assert (the `PIPELINE_GUIDE` §6 lesson about
  UV-Unwrap enums applies verbatim here).
- **Determinism:** all randomness comes from the `seed` dial, applied as a `Mapping` offset + noise
  `W` on the procedural textures. **No `SceneTime` in the world tree** — the still must be identical
  across runs (and `SceneTime` in a stack means a re-cook per frame; the C1/C2 motion-split work in
  `PIPELINE_GUIDE.md` is the precedent).
- **Idempotency:** find-or-create the world datablock by name (`SKY_Melusina`), then clear and rebuild
  its node tree. Re-running the builder must not stack duplicate worlds or leak nodes.
- **Node budget:** ≤ ~60 nodes for the world tree (v2 stack). It is a per-pixel evaluation of a
  full-frame background, so it is the cheapest place to be wasteful — but not free.
- **No texture nodes:** assert no `TEX_IMAGE` / `TEX_ENVIRONMENT` in the tree (gate §6).

---

## 5. Integration

### 5.1 Where it plugs in

| File | Change | Constraint |
|---|---|---|
| `Tools/brooch_sky.py` (new) | `SKY_PRESETS`, `build_sky_tree()`, `apply_sky(scene, variant=None, carrier=..., **dials)`, `sky_for_genome(path)` | idempotent; no file I/O beyond reading a genome JSON; importable without side effects |
| `Tools/brooch_pres_rig.py` | replace the current world block (lines 121–133: find/create world, `use_nodes`, set Background colour `(0.004,0.006,0.012)` + strength 1.0) with `sky.apply_sky(scene, variant=ARG_SKY)`; add a `sky_variant` line to the "PRES_RIG ready" print | the rig stays regenerated-per-run and never saved into the file (`PIPELINE_GUIDE.md`, "The rig is NOT saved into the working file") |
| `Tools/brooch_pres_shot.py` | accept `--sky <variant>` from `sys.argv` after `--`; write evidence to `Saved/Audit/sky_<variant>_<shot>.png` when a sky variant is set, else keep the existing `pres_*.png` names | existing default output paths must not change (other lanes reference `pres_front.png`) |
| `Saved/Accessories/brooch_lab/genome/*.json` | read-only: `compose_style`, `traits.gems.material_a`, `traits.gems.color_a` drive variant selection | no genome writes |

Run shape (unchanged for the operator):

```
blender -b FlowerBrooch.blend --python Tools/brooch_pres_rig.py \
        --python Tools/brooch_pres_shot.py -- --sky tide
```

### 5.2 The backdrop-occlusion finding (measured from the rig's own geometry)

`brooch_pres_rig.py` places `PRES_Back` as a plane of scale `(3.0, 3.0)` at `y = +0.85`. The shot
script puts the front camera at `y = −D` with `D = size × 1.35 = 0.81 u` (60 mm hero at 1 u = 100 mm),
lens 60 mm, sensor 36 mm, portrait 1600×2000 (AUTO sensor fit → 36 mm maps to the long axis).

- camera → back plane distance = 1.660 u
- frame height at the plane = **0.996 u**, width = **0.797 u**
- the plane spans 6 × 6 u

**The plane covers the entire frame.** Therefore, in every current still, the visible background is
`PRES_Back` (a matte near-black `0.006,0.008,0.014` = `#12161F`), not the world. Consequences:

1. A world-only sky would be **invisible in the frame** and would only change the metal's reflections
   and the ambient fill. That alone is worth doing (it is the audit's axis-B defect), but it is not
   "a sky backdrop".
2. The v1 deliverable must therefore be **two carriers**: world (reflection/lighting) + backdrop card
   (visible pixels). Cheapest implementation: give `PRES_Back` the same stack with `carrier="card"`,
   using `TexCoord.Object` so the gradient is stable under camera moves.
3. The floor plane (`PRES_Floor` at z = −0.55) should stay matte black; a graded floor would create a
   horizon line, which violates the "seamless" rule (§1.2).
4. Alternative for a bigger change: delete `PRES_Back` and use the dome (§5.5) so the sky *is* the
   background; keep this as the v2/v3 option and A/B it against the card.

### 5.3 Keeping the black reflection card doctrine intact

The luxury tell is the **black window** in the metal (`brooch_pres_rig.py` line 112,
`PRES_Card_Black_R`; `PIPELINE_GUIDE.md`: "the black window is the luxury tell"). A brighter
environment directly attacks it. Enforcement:

- `sky_strength` clamp in the builder: `editorial_dark ≤ 0.35`, all element variants ≤ 0.80 (radiant),
  and never 1.0 by default;
- the sky's brightest pixel (before the compositor) must stay **below** the `Melodia_Presentation`
  glare threshold (`threshold 1.0–1.2` in `PIPELINE_GUIDE.md` §7) except for `radiant`, where a
  blooming horizon is intentional;
- **gate:** in the front still, the black card's reflection must still show as a distinctly darker
  region on the metal than the surrounding environment. Verify by sampling two 20×20 px patches on the
  metal in the render (one on the card reflection, one off it) and asserting a value ratio ≥ 2:1.
  `UNTESTED` — this is the acceptance test, not a measured result.

### 5.4 Cycles vs EEVEE

- **EEVEE-first (as shipped).** World lighting comes from the internal light probe; our sky is
  low-frequency, so the probe captures it faithfully and cheaply. Watch the **sun-extraction** setting
  (§2.9) — set world sun Threshold to 0 in the rig so a bright horizon band never becomes a lamp.
- **Cycles (documented, not budgeted).** Cycles gives true camera-ray separation (`Is Camera Ray`),
  no probe blur, and correct environment reflections, at a cost the 1050 Ti cannot absorb at 1600×2000
  with this sample count. Keep Cycles as the "reference/hero" option for one-off frames; do not make
  the stills pipeline depend on it.
- Shared: no change to `scn.eevee.taa_render_samples = 96`, `use_raytracing = True`, or
  `view_settings.look = 'AgX - Medium High Contrast'`. AgX compresses highlights, which helps the
  bright variants survive; it also *deepens* the darks, which is why the horizon lift must be authored
  slightly higher than it looks in a linear preview.

### 5.5 Dome fallback (escape hatch)

If the EEVEE background turns out to be probe-limited (stars blur, §2.5) or `Is Camera Ray` does not
work (§2.8), the sky moves to a **mesh carrier**:

- inverted UV sphere, radius ~4 u (outside the reflection cards at 0.42–0.62 u and the back plane at
  0.85 u), normals flipped, in the `PRES_RIG` collection so it is rebuilt per run;
- the same node stack in a **material** (`carrier="dome"`), surface = Emission (colour = sky colour,
  strength 1.0) so it is view-independent;
- keep its emission low (`sky_strength`) so it does not become a scene light; disable shadow casting
  (`ob.visible_shadow = False`) and consider `visible_diffuse/glossy = False` in Cycles so it is
  camera-only;
- cost: 1 mesh + 1 material, one extra draw call — negligible. Benefit: per-pixel detail regardless of
  probe resolution, and it works identically in EEVEE and Cycles.
- Optional extra: a **backdrop card variant** of the same material for the macro shot, where a dome
  behind the camera would be wasted.

---

## 6. Gates + acceptance criteria

| # | Gate | Test | Pass condition |
|---|---|---|---|
| G1 | **Cost** | time `blender -b FlowerBrooch.blend --python Tools/brooch_pres_rig.py --python Tools/brooch_pres_shot.py` 3× without sky, take median; repeat with sky on, same machine (GTX 1050 Ti 4GB, EEVEE 96 spp, 1600×2000, 3 stills) | sky run ≤ **+10–15 %** median wall-clock. No absolute baseline asserted here (no Blender run was permitted in this session). |
| G2 | **Determinism** | render the same shot twice with identical dials/seed; hash outputs (or hash the EXR float buffer if PNG metadata differs) | identical hashes. No `SceneTime`, no unseeded `Random Value` in the tree. |
| G3 | **No textures** | walk the world + card + dome node trees | no `TEX_IMAGE`, no `TEX_ENVIRONMENT`, no external file paths. |
| G4 | **Headless** | run the full 3-shot set via `blender -b … --python …` on a clean shell, no GUI | exits 0, all three PNGs written, no manual steps. (Manual claims headless EEVEE is unsupported on headless Windows; repo evidence contradicts it — re-verify once on the 1050 Ti box.) |
| G5 | **Dark-field doctrine** | sample two 20×20 px patches on the metal in `pres_front.png` (card reflection vs environment) | card region ≥ 2× darker. Black card still readable. |
| G6 | **No sun extraction** | inspect EEVEE world sun Threshold after rig build; render a variant with a bright horizon | Threshold = 0 (or sky stays under it); no unexpected shadow direction change. |
| G7 | **No banding** | 200 px crop of the darkest gradient region at 8-bit and 16-bit | no visible steps at 16-bit; at 8-bit the grain keeps steps below perception. |
| G8 | **Layer isolation** | set every optional dial to 0 | result is a graded dark field ≈ current look (no regression in the existing stills). |
| G9 | **Node budget** | count nodes in the world tree | ≤ 60 nodes (v2 stack); document any overflow. |
| G10 | **Variant coverage** | build + render all 8 variants | 8 × 3 stills exist under `Saved/Audit/sky_<variant>_*.png`; no crash, no variant identical to another (hash-compare the 8 front stills — at least the 7 element variants must differ). |
| G11 | **Evidence discipline** | every claim about the sky in a session note is backed by a script + a render path (house standard, `PIPELINE_GUIDE.md` §5) | no prose-only claims. |

---

## 7. Build order

### v1 — static editorial gradient + grain (effort ≈ 0.5–1 day)

Scope: `Tools/brooch_sky.py` with `SKY_PRESETS["editorial_dark"]` only fully tuned; layers L0, L1, L6,
L7; carriers: world + `PRES_Back` card; `--sky` plumbing in the shot script.
Verify: G1, G2, G3, G4, G5, G8, G11; visual check that the metal's environment is no longer flat.
Deliverable evidence: `Saved/Audit/sky_editorial_dark_{front,tq,macro}.png` next to the existing
`pres_*.png` for A/B.

### v2 — cloud band + stars + carrier decision (effort ≈ 1–2 days)

Scope: L3 (noise + height mask) and L4 (Voronoi crush + brightness variance + zenith gradient);
the two decisive experiments — **EEVEE background sharpness test** (§2.5) and **`Is Camera Ray` A/B**
(§2.8) — and the dome carrier (§5.5) if either fails.
Verify: G6, G7, G9, plus the star-sharpness crop test; re-run G1 (this is where the cost delta is real).

### v3 — element variants + aurora + auto-select (effort ≈ 1–2 days)

Scope: the remaining 7 preset rows, aurora layer (emissive-only, gated), `sky_for_genome()` derivation
from `compose_style` / `gems.material_a`, and a variant contact sheet for review.
Verify: G10; per-variant doctrine check (G5) for the bright ones (`radiant`); a side-by-side sheet
`Saved/Audit/sky_variants_sheet.png`.
Optional stretch: a `--sky photo` mode that instantiates the 5.2 Sky Texture multiple-scattering model
for reference comparisons only (§2.2) — never the shipping path.

---

## 8. Open questions for the owner

1. **Carrier policy:** do you want the visible background to stay the flat `PRES_Back` card (sky only in
   reflections, minimal risk) or should v2 replace it with a dome so the frame *is* sky? (§5.2)
2. **Amplitude ceiling:** is `sky_strength ≤ 0.35` for the default editorial variant the right
   restraint, or should the default stills show a visible sky wash?
3. **Radiant exception:** may the `radiant` variant be visibly brighter (it will be the only still set
   where the background is not near-black)? That is a brand decision, not a technical one.
4. **Promo-art reuse:** is the target later "the same sky, animated" (needs a time dial and a motion
   budget) or stills-only forever?
5. **Game-side parity:** should the seven variants be authored so the same numbers can be ported to a
   UE material/sky for promo art, or is Blender-only acceptable (i.e. do we care about a shared
   parameter contract now)?
6. **Naming:** do the variant names follow the register names (`tide`, `umbral`, …) or the jewel names
   (`tide_reliquary`, `umbral_bloom` — the genome `lore.name`s)?
7. **Evidence path:** are `Saved/Audit/sky_<variant>_*.png` acceptable, or does the still set need to
   live under `Saved/Portfolio/Intake/<AssetId>/` for consistency with the intake lane?
8. **Aurora:** keep it (Umbral/Gale only) or drop it as scope creep? It is the one layer with a real
   cost risk on the 1050 Ti.
9. **Sun extraction:** is setting the EEVEE world sun Threshold to 0 in the rig acceptable, or does any
   other lane depend on world sun extraction?
10. **`--sky` default:** should the default remain `editorial_dark` (reproducible `pres_*.png`) until
    you approve a variant for the hero genome, or should the hero auto-select `tide` immediately?

---

## Sources

**Blender technique — sky/world**
- [Sky Texture Node — Blender 5.2 LTS Manual](https://docs.blender.org/manual/en/latest/render/shader_nodes/textures/sky.html) — Multiple Scattering is the new default; Single Scattering/Preetham/Hosek-Wilkie are legacy and slated for removal; scattering skies are "very bright by default"; sun disc is Cycles-only.
- [Blender 5.0 release notes](https://www.blender.org/download/releases/5-0) — the new sky model "works great for accurate reflections indoor too" and is "beautiful out of the box, in both Cycles and EEVEE"; faster light-probe volume baking.
- [EEVEE World Settings — Blender 5.2 Manual](https://docs.blender.org/manual/en/latest/render/eevee/world_settings.html) — world lighting is stored in an internal light probe (less precise than Cycles), treated as *indirect* light; probe resolution is a setting; EEVEE can extract intense world sources into a sun light (Threshold/Angle/Use Shadow).
- [EEVEE Limitations — Blender 4.2 Manual](https://docs.blender.org/manual/en/4.2/render/eevee/limitations/limitations.html) — raytracing/blended-material limits, light-probe caps, and the "headless rendering is not supported on headless Windows systems" caveat our repo evidence contradicts.
- [Light Path Node — Blender 5.2 Manual](https://docs.blender.org/manual/en/latest/render/shader_nodes/input/light_path.html) — EEVEE support table: `Is Camera` supported, but EEVEE has no real rays; the other outputs collapse to `Is Glossy`.
- [Cycles World Settings — Blender Manual](https://docs.blender.org/manual/en/latest/render/cycles/world_settings.html) — the `Is Camera Ray` Mix trick: separate the directly visible background from the lighting background.
- [StackExchange: EEVEE, disable background light](https://blender.stackexchange.com/questions/142102/eevee-how-to-disable-background-light) — the community workaround: `Is Camera Ray` into the Background strength.
- [StackExchange: is there an EEVEE analogue to Is Camera Ray?](https://blender.stackexchange.com/questions/336975/is-there-an-analogue-or-alternative-to-light-path-is-camera-ray-for-eevee) — reported failure of the trick in EEVEE; "you just have to use Cycles" for that control.
- [StackExchange: why is my EEVEE world background blurry?](https://blender.stackexchange.com/questions/244408/how-do-i-make-my-world-background-hdri-not-blurry) — backgrounds need to be large/detailed; the standard fix is splitting the lighting image from the background image.

**Blender technique — procedural sky construction**
- [Francesco Milanese — procedural starry/cloudy night sky (Mêlée Island)](https://www.francescomilanese.com/tutorials-en-all/tut-063-en-b3d-melee-island-starry-blue-night.html) — the reference three-layer world: stars (noise scale 200 + brightness/contrast), clouds (noise 3D scale 3 detail 5 + gradient mask), horizon glow (Easing gradient, ColorRamp stop at 0.09, dark blue-green 0.007/0.018/0.031), gamma-driven blend factors.
- [BlenderNation writeup of the same](https://www.blendernation.com/2024/08/31/creating-a-procedural-starry-and-cloudy-sky-inspired-by-the-secret-of-monkey-island/) — confirms the "no images, only procedural Noise and Gradient textures" constraint we are adopting.
- [iMeshh — real sky without HDRI](https://imeshh.com/blog/create-a-real-sky-in-blender-with-no-hdri) — Voronoi-masked star field, zenith-concentrating vertical gradient, window-space star projection, sky-as-mesh-sphere, sun-disc subtraction.
- [Unreal Matter — procedural starfields](https://www.youtube.com/watch?v=U_ut4rXDzLI) — Voronoi distance → crushed ColorRamp, per-star colour/brightness variance via noise, bloom for glow.
- [xbdev — Python starfield snippet](https://xbdev.net/programming/blender/?article=randomstarfield) — code-level reference for the Voronoi star node chain (node names, ramp positions).
- [blenderartists — procedural sky texture thread](https://blenderartists.org/t/procedural-sky-texture/594259) — gradient texture used to reveal clouds near the horizon.
- [CGEcho — Samuel Krug's aurora node guide](https://cgecho.net/create-stunning-blender-auroras-samuel-krugs-node-based-guide/) — aurora construction: Z-flattened noise streaks, sharp-bottom/diffuse-top gradient, magenta→green-blue ramp, white-noise dithering; volumetric, Cycles-oriented.
- [BlenderNation — aurora with curves + geometry nodes](https://www.blendernation.com/2022/08/08/draw-an-aurora-with-curves-and-geometry-nodes/) — the heavier volumetric/HDRI route we are deliberately not taking.
- [projectleuc — custom skies in Blender](https://projectleuc.com/blog/creating-custom-skies-in-blender) — Nishita controls and the warning that world-only lighting gives soft directionless shadows (hence a real sun lamp); stylized-sky addons exist for reference.
- [artisticrender — skybox from the sky texture](http://artisticrender.com/setup-a-skybox-using-the-sky-texture-in-blender) — practical Nishita vs Hosek/Preetham setup notes.
- [Blender devtalk — EEVEE-Next feedback](https://devtalk.blender.org/t/blender-4-2-eevee-next-feedback/31813?page=57) — "Sun disc not available in EEVEE" persists; EEVEE does shadow-cast from HDRIs in World.

**Banding / output discipline**
- [Will Gibbons — colour banding in 3D renders](https://www.willgibbons.com/color-banding) — causes and mitigations: avoid low-contrast subtle gradients, raise bit depth, minimise.
- [blenderartists — saved file has major banding](https://blenderartists.org/t/render-looks-great-saved-file-has-major-banding-issues/1381323) — 16-bit output removes most banding; dither only helps 8-bit.
- [gamedev.tv — EEVEE emission banding](https://community.gamedev.tv/t/color-banding-issue-with-eevee-emission/230284) — dither lives in the output settings.

**Editorial / luxury photography doctrine**
- [Westcott University — dark field imaging](https://westcottu.com/dark-field-imaging-tips-techniques) — the patch-and-graze principle: block the direct path, let spill define the edges; flags control spill.
- [Black Studio Sessions — luxury product photography](https://justoborn.com/black-backgrounds/) — the black-background production doctrine: cinefoil/gobos, single directional key, lens flag, void underexposed two stops or more, rim separation as the luxury tell.
- [434photo — low-key product photography](https://434photo.com/low-key-product-photography-mastering-dramatic-light-for-luxury-items) — chiaroscuro, 4:1–8:1 contrast, negative fill, accent catch light, blacks driven to zero, dark neutral backgrounds.
- [Shotova — luxury product photography](https://shotova.com/blog/luxury-product-photography) — dark backgrounds + deliberate negative space + one gold/warm accent; near-monochromatic palette.
- [katebackdrop — seamless paper backdrops](https://www.katebackdrop.com/nl-nl/blogs/over-achtergronden/seamless-paper-backdrop) — seamless = smooth, non-reflective, distraction-free (no horizon).
- [3 lights + white backdrop = gradient portraits](https://www.youtube.com/watch?v=iR57An0Rzv0) — the studio gradient-backdrop trick (uneven light on a white cyc) we are emulating procedurally.
- [Colour gels = gradient backgrounds](https://www.youtube.com/watch?v=OeFv2NthLFg) — hue-split backdrops from gels; the model for the `band_contrast` dial.
- [slrlounge — coloured seamless backgrounds](https://www.slrlounge.com/how-why-to-shoot-on-colored-seamless-backgrounds-improving-your-portraits/) — backdrop colour choice and colour theory in the studio.

**Anime / film sky palettes**
- [FairStack — Makoto Shinkai style guide](https://fairstack.ai/styles/makoto-shinkai) — "warm cyan-to-magenta sky gradients", photographic-painterly layered backgrounds, saturation above reality.
- [Relazione — colour theory in anime](https://relazione.com.br/why-color-theory-in-anime-actually-changes-everything-you-watch-k2n) — Shinkai blues layered with teals/indigos/glowing whites; Ghibli (Yasuda) works from nature with added warmth inside a limited palette.
- [Shinkai art analysis](https://www.youtube.com/watch?v=TlhHMVgiIeM) — triadic colour continuity; blue used in shadows and to create depth separation.
- [bunka — Nizo Yamamoto on painting clouds and skies](https://mediag.bunka.go.jp/article/article-16420) — hand-painted sky craft; twilight where "white buildings looked yellow and their shadows blue" (warm light / cool shadow separation).
- [lavaritte — how to draw anime clouds](https://lavaritte.com/blogs/cloud-tutorial) — cloud shading rule: bright sun-facing tops, blue-grey to purple-grey undersides, read as solid 3D forms.
- [Ghibli Museum — "Painting the Colors of Our Films"](https://www.ghibli-museum.jp/en/exhibitions/013128) — limited palettes chosen for texture and feel (Michiyo Yasuda's craft).
- [HueHive — Ghibli palette](https://huehive.co/ai_generated_palettes/11398) — concrete anchors: Ghibli blue #4E7FB1, Laputa lavender #807EA8, Spirited gold #F1C40F.
- [HueHive — Shinkai palette](https://huehive.co/ai_generated_palettes/11472) — twilight blue #0B0F70, cherry-blossom pink #F4B0A9, cloudy-sky blue #B0C4DE.
- [ghibli R package (CRAN)](https://cran.r-project.org/web/packages/ghibli/ghibli.pdf) — 27 film-derived Ghibli palettes, 7 colours each, if the art direction wants to sample properly.
- [UE5 stylized Ghibli skybox tutorial](https://www.youtube.com/watch?v=MnriY-z72EI) — the texture-based game approach; we take the look, not the pipeline.
- [freestylized — stylized skybox collections](https://freestylized.com/all-skybox/) — evidence that the game industry solves this with HDRIs; our no-texture gate is a deliberate divergence.

**Repo evidence (local, no web)**
- `Tools/brooch_pres_rig.py` — PRES_RIG: dark field planes, white/black reflection cards, soft key + hard gem point + rim + kick, EEVEE 96 spp + raytracing, AgX Medium-High, world `(0.004,0.006,0.012)` at strength 1.0 (the block Melusina Sky replaces).
- `Tools/brooch_pres_shot.py` — bbox-framed front/three-quarter/macro stills at 1600×2000, lens 60/60/70 mm, toon outline forced off and restored.
- `Saved/Accessories/brooch_lab/BROOCH_LUXURY_RESEARCH_2026-09-17.md` — §F "the stage" doctrine; §Mapping element→optical verb; the studio-tent/hard-source split.
- `Saved/Accessories/brooch_lab/BROOCH_LUXURY_AUDIT_2026-09-17.md` — axis B "metal reflects a flat navy void (no environment to mirror = dead by construction)"; presentation rig landed as ranked move #1.
- `Saved/Accessories/brooch_lab/PIPELINE_GUIDE.md` — rig-not-saved rule, `Melodia_Presentation` glare group (Fog Glow, strength 0.28 / size 0.40 / threshold 1.2), motion-split/SceneTime lessons, headless EEVEE evidence.
- `Saved/Accessories/brooch_lab/BROOCH_EXPANSION_RESEARCH_2026-09-17.md` §6 — register spine (Forte · Radiant · Arcane · Tide · Stone · Gale · Umbral).
- `Saved/Accessories/brooch_lab/genome/melodia_gala_tide_v1.json`, `melodia_gala_umbra_v1.json` — `compose_style`, `gems.material_a`, `gems.color_a` (the variant-selection hooks), lore names/homes ("Sea Above", "Dreamstate").
- `Tools/BlenderAddons/melodia_studio/atmosphere.py` — existing in-repo precedent for a gradient world (`_apply_world`).
- `Saved/Audit/pres_front.png`, `pres_tq.png`, `pres_macro.png` — the current rig's evidence stills (baseline for A/B and for the cost measurement).

*Authored 2026-09-17. No Blender runs, no file mutations other than this document, no git operations.*
