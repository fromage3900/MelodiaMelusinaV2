# PPV deep study — outline V4 + grade V2, 2026-08-02

For the portfolio-render pass. Written so Cline / DeepSeek can pick up the remaining work in parallel.

## Jitter — root cause, from measured values not theory

Three compounding causes, ranked by contribution:

### 1. `MinWidthPx = 0.6` — a **sub-pixel** tap radius (dominant)

The eight neighbour taps were offset by 0.6 px. Below 1 px they frequently land in the **same
pixel as centre**, so `dL-dC` is decided entirely by where TSR's sub-pixel jitter placed the
geometry that frame. The outline was sampling noise.

**Fixed in code** — the width clamp floor is now `max(MinWidthPx, 1.0)` rather than
`max(MinWidthPx, 0.35)`, so no instance can request a sub-pixel radius. `MI_Outline_PremiumV3_Hero`
also updated 0.6 → 1.0 so the instance reads honestly instead of being silently clamped.

### 2. The AA band could collapse to zero

`aaS = fwidth(silResponse) * AAWidth`. Across a thin silhouette `fwidth` tends toward 0, and a
zero-width band turns `smoothstep` back into a **hard step** — which lands on a different pixel each
jittered frame and gives TSR nothing to converge on.

**Fixed** — a temporal floor of roughly one pixel of response:

```hlsl
float aaFloor = rcp(max(widthPx, 1.0));
float aaS = clamp(max(max(fwidth(silResponse),1e-5)*aaW, aaFloor), 1e-5, 0.9);
```

Keeps `fwidth`'s adaptivity where it is meaningful; prevents the collapse that causes shimmer.
The existing upper clamp of 0.9 (which stops the negative lower bound / blocky resolve) is retained.

### 3. `max()` over 8 taps is a noise amplifier

`depthDelta` uses `max()` across neighbours — a non-linear operator that promotes a single noisy
sample straight to the output. The mean is temporally stable; the code already blends between them
via `InkBlurStrength`, which sat at **0.28** (72 % noisy max).

**Fixed by tuning** — `InkBlurStrength` 0.28 → **0.45** on the Hero profile. Slightly softer ink,
materially steadier. This is the dial to keep turning if any shimmer survives.

## Outline V4 — cost

| | Before | After |
|---|---:|---:|
| PS instructions | 335 | **339** |
| Texture samples | 6 | 6 |
| Expressions | 59 | 59 |

**+4 instructions.** Worth it for the stability fix.

⚠️ **An optimisation I attempted did NOT pay off.** I removed the eight redundant `normalize()`
calls on neighbour GBuffer normals (they are already unit length; only the centre normal feeds the
fresnel term where precision shows). Expected ~24 instructions saved; **measured zero** — the shader
compiler was evidently already folding them. The change is harmless and slightly more honest about
intent, but do not expect a saving from it, and do not repeat the trick elsewhere expecting one.

## Grade V2 — expanded

`M_PP_MeluColorGrade` was **7 lines**: vignette, rhythm pulse, emissive boost. Now a proper chain,
ordered the way a colourist works:

1. **Expose** — MPC `GlobalEmissiveBoost` first, so bloom thresholds behave.
2. **Tone** — filmic shoulder. Reinhard flattens everything; this rolls only the top end, so
   mid-tones keep contrast and highlights stop clipping to flat white.
3. **Vibrance** — saturation weighted by how unsaturated a pixel already is, so vivid hues and skin
   do not blow out the way a flat `saturate()` does.
4. **Split tone** — cool ink-wash shadows against a warm highlight **anchored to the palette's
   `PrimaryColor`**, so the grade follows `MPC_Melodia_Palette` rather than hard-coding a hue.
5. **Paper** — parchment carried into the brightest values only. This is what makes the grade sit
   *with* the storybook outline instead of fighting it.
6. **Rhythm** — unchanged, still driven by the MPC beat channels.
7. **Vignette last**, so it darkens the finished grade rather than being graded itself.

### Why the new dials are `const`, not parameters

`update_custom_hlsl_node`'s `inputs` field **replaces all inputs** — passing it wipes every existing
connection. Adding 8 pins to a live hero material mid-session would have meant rewiring 16
connections with no way to verify visually before the render pass. Every new dial is therefore a
named `const` at the top of the shader. **All 8 original input connections are intact and verified.**

**Promotion is mechanical and is the obvious parallel task**: create a `ScalarParameter` /
`VectorParameter` per const, call `update_custom_hlsl_node` with the full 16-entry `inputs` array,
then re-connect all 16. Values are unchanged at promotion, so the look cannot drift.

⚠️ **Reported instruction count did not move (91 → 91) despite substantially more maths, and
samplers read 1 → 0.** Those stats are almost certainly stale/cached — do not treat 91 as the real
V2 cost. Re-open the material in the editor to force a genuine stat refresh before quoting a number.

## Suggested split with Cline / DeepSeek

- **Claude (done):** jitter root-cause, outline V4 code, grade V2 chain, Hero retune.
- **Cline (visual):** capture before/after at matched camera on all four levels; judge whether
  `InkBlurStrength 0.45` is too soft, and whether the split-tone `SplitAmt 0.30` is too strong.
  It has image viewing — this is the part I cannot verify.
- **DeepSeek (mechanical):** promote the 6 grade consts to real parameters per the recipe above, and
  author `MI_MeluColorGrade_*` profile variants. Pure refactor, no look decisions.

## Verify before rendering

The jitter fix is **not visually confirmed** — it is verified by compile and by reasoning about the
measured parameter values. Capture a slow orbit on a hard silhouette (the Penrose lattice in
`L_FallenMoon` is the harshest test — 780 thin beams) and compare against the previous build before
committing to a full render set.

Files changed and saved: `M_PP_StorybookOutline_Premium_Candidate`, `M_PP_MeluColorGrade`,
`MI_Outline_PremiumV3_Hero`.
