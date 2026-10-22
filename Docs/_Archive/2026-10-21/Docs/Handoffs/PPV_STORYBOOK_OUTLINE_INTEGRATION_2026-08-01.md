# Handoff: Storybook Outline PPV — Integration Points for Kiro & Codex

**Read `_AGENT_WORKING_AGREEMENT.md` first. It is binding.**

**UPDATED 2026-08-01, late — this is now LIVE, not a preview.** `M_PP_StorybookOutline` is wired into
`PPV_NikkiDream` on all 4 target levels (`L_KaleidoNave`, `L_MelusinaMorning`, `ZenForestTest`,
`L_FallenMoon`) via `setup_nikki_render_post_process.py`. The old 2-material stack (`M_PP_ToonOutline`,
`M_PP_StorybookVines`, `M_PP_StorybookVines_Inst`) is quarantined at
`Content/_QuarantinePostProcess_20260801/` (zero referencers confirmed first). Owner has seen it
rendering in-viewport and confirms the outline effect itself looks good. **One bug found and fixed
live** (broad black regions on near-camera geometry from an uncalibrated depth-normalization
constant) — see "Known open issue" below for what's still unresolved after that fix.

## What exists right now

`/Game/EnvSandbox/Materials/PostProcess/M_PP_StorybookOutline` replaces the old two-material stack
(`M_PP_ToonOutline` + `M_PP_StorybookVines_Inst`, which duplicated edge-detection work) with one
material that does real depth+normal edge detection (multi-tap, not the old single-axis
`ddx()`-only version), an anime-style ink option, distance falloff, a vine-growth overlay sharing the
same edge mask, and two real integration points below. Built using this project's existing, tested
`Art of Shader` material-function library (`MF_StencilDepthAlpha`, `MF_PostProcessBlend` — reused,
not reinvented) rather than raw duplicate logic.

## RESOLVED 2026-08-01 (later) — the "cuts off" issue was cause #2, confirmed from a screenshot

Owner supplied a viewport screenshot of `ZenForestTest`. The cutoff boundary was a hard **screen-space
rectangle** (straight vertical + horizontal edges, ~70% of viewport in both axes, anchored top-left,
not following geometry and not distance-dependent) — which rules out cause #1 (`FalloffStart/End`,
which would produce a distance-following boundary) and confirms cause #2. Three fixes applied to
`MaterialExpressionCustom_0` in `M_PP_StorybookOutline`; recompiled, validated clean, saved:

1. `float2 texel = View.ViewSizeAndInvSize.zw` → `View.BufferSizeAndInvSize.zw`. Scene-texture
   lookups are in **buffer** UV space, not view space, so every tap strode `BufferSize/ViewSize`
   pixels instead of one whenever the buffer is larger than the view rect — which is the normal case
   in the editor, where scene targets are allocated for the largest viewport used.
   *Correction: an earlier version of this note attributed that to "screen percentage 1.3". That was
   wrong — `r.ScreenPercentage` is 100; the `1.3` in the viewport toolbar is camera speed. The fix is
   still correct (buffer-vs-view space is the right distinction regardless), but the stated cause was
   not.*
2. All five tap UVs now `clamp()`ed to `View.BufferBilinearUVMinMax` — off-rect garbage can no longer
   read as an edge. This is the clamp the previous pass listed as untested candidate #2.
3. `normalEdge` changed from a **sum** of the two axis terms to `1 - min(dotX, dotY)` (i.e. `max()`)
   plus a `smoothstep(0.35, 0.85)` response, and the sampled normals are now `normalize()`d. The
   summed form saturated to 1.0 on any surface with high-frequency normals, filling whole regions
   with ink instead of drawing lines. Note the earlier depth-math fix switched the *combination* of
   depth vs normal to `max()` but left the normal term itself as the same summed-then-saturated shape
   that caused the original blowout — that is why "broad black regions" partially survived it.

## ⚠️ ROOT CAUSE CONFIRMED 2026-08-01 12:21 — and it is NOT fully fixed. Read before rendering.

**Proven, not inferred.** An engine-side high-res capture
(`Saved/Screenshots/WindowsEditor/PPV_FinalLook_Test.png`, 1920×1080) reproduces the streak bands in
the **render itself** — so this was never a screen-recorder artifact. Requesting a capture size
different from the viewport size forced `BufferSize ≠ ViewSize`, and the artifact appeared
immediately. That is the same condition the editor-restart "fix" merely hid by making buffer and view
happen to match.

**What this means for portfolio renders:** any capture at a resolution other than the live viewport's
will show a garbage band along the bottom edge. This is a hard render blocker, not cosmetic.

**Why the existing clamp is insufficient.** The material clamps taps to
`View.BufferBilinearUVMinMax`, which is the valid region of the **buffer**. When the buffer is larger
than the view rect, the area between them holds stale/uninitialised data that this clamp still
permits reading. The correct bound is the **view rect** expressed in buffer UV space — roughly
`View.ViewRectMin * View.BufferSizeAndInvSize.zw` for the min and
`(View.ViewRectMin + View.ViewSizeAndInvSize.xy) * View.BufferSizeAndInvSize.zw` for the max, inset
by half a texel.

**Deliberately not attempted this session.** It is a live-material HLSL edit that cannot be visually
verified before the editor closes, and a wrong uniform name is a compile failure on the shipping
outline. Next session: make the change, recompile, then capture at a size *different* from the
viewport — that is now the reliable repro.

## Screenshot capture WORKS — prior "broken" diagnosis was wrong

`AutomationLibrary.take_high_res_screenshot` is functional. It looked broken because every previous
attempt **slept on the game thread** immediately after calling it; the screenshot is queued and
flushed on a later editor tick, so blocking the thread guarantees it never lands.

```python
import unreal
unreal.AutomationLibrary.take_high_res_screenshot(1920, 1080, 'MyShot.png')
# DO NOT sleep here. Return, let the editor tick, check the file on a later call.
```

Output lands in `Saved/Screenshots/WindowsEditor/`. The filename argument is honoured. Press **G**
(Game View) first or editor gizmos and the Ultra Dynamic Sky billboards bake into the capture — both
are visible in `PPV_FinalLook_Test.png`. `HighResShot` via a console command routed through Monolith
does **not** reach the viewport client; use the Python call.

## ~~RESOLVED after editor restart~~ — WRONG, the restart only MASKED it (corrected 12:21)

**Do not trust this section's original claim.** It read "resolved — the rectangle is gone" on the
strength of the owner's post-restart report that the outline covered the full screen. That report was
accurate about what was on screen, but the conclusion drawn from it was not: the restart happened to
make `BufferSize` equal `ViewSize`, which hides the bug rather than fixing it. Forcing a capture at a
different resolution brought it straight back, in the engine's own render. See the **ROOT CAUSE
CONFIRMED** section at the top of this file.

What *is* still true from that pass: the buffer-UV / clamp / `max()` corrections were real and
necessary, the black-grass blowout genuinely improved, and the outline does cover the full viewport
whenever buffer and view sizes match.

**The actual lesson, restated correctly:** a buffer/view-geometry bug is invisible whenever the two
happen to match, so "it looks fine now" is not evidence of a fix. Verify by *deliberately* forcing a
mismatch — capture at a resolution different from the viewport. That is the reliable repro, and it is
also exactly the condition portfolio renders run under, which is why this matters rather than being
a curiosity.

The `ShowFlag.PostProcessing 0` discriminator is obsolete — the engine-side capture settled the
question directly.

### Original investigation notes — kept for the reasoning trail

Measured across three separate owner captures (11:25 still, 11:32 clip, 11:45 clip) at two different
viewport widths: a hard-edged vertical boundary at **0.704–0.705 of viewport width**, with the same
ratio vertically. Same ratio at different viewport sizes means it is a *ratio*, not a fixed pixel
offset. Content outside it is garbage — vertical colour streaks, horizontal scanline bands, and in
one frame what looks like a stale previous frame.

An earlier note in this session claimed this was motion-only and therefore not the shader, on the
basis of one settled frame rendering clean. **That was not reliable** — the 11:45 clip shows the
boundary in a near-settled frame. Treat the cause as unknown.

Two live candidates, not discriminated:
- **Render-side:** editor scene targets allocated larger than the view rect (`BufferSize > ViewSize`),
  with taps or the blend reading the unrendered remainder. Note `r.ScreenPercentage` is **100** and
  `r.DynamicRes.OperationMode` is **0**, so neither of those is the cause. AA is TSR
  (`r.AntiAliasingMethod=4`, `r.TSR.History.ScreenPercentage=200`).
- **Capture-side:** the OS screen recorder tearing / presenting a partially-updated swapchain. All
  three captures came from the same Windows recorder, so this is not ruled out.

**The cheap decisive test, ~30 seconds, do this before touching any shader:** in the viewport run
`ShowFlag.PostProcessing 0` (or just uncheck `Enabled` on `PPV_NikkiDream`) and look at the same
camera. If the rectangle survives with post-processing off, it is **not** this material and no
shader edit will fix it. If it vanishes, it is in the post-process chain and worth pursuing.

Engine-side capture could not settle it this session: `HighResShot` and
`AutomationLibrary.take_high_res_screenshot` were already known broken, and `it-is-unreal`'s
`take_screenshot` is *also* broken — its schema declares `file_path` but the server requires
`filepath`, so the tool cannot be invoked at all. Fixing one of those capture paths is worth more
than another round of inference; this project has repeatedly lost time to fixing from inference
instead of from a picture.

## Foliage tuning — APPLIED 2026-08-01, values live

Owner chose the combined lever. Applied to
`/Game/EnvSandbox/Materials/PostProcess/MI_PP_StorybookOutline` (instance, not master — no shader
recompile, and it does not collide with Codex editing the master graph):

| Parameter | Was | Now | Why |
|---|---|---|---|
| `FalloffStart` | 3000 | **1200** | Fade begins at 12 m, so the mid-to-far grass mass attenuates. |
| `NormalWeight` | 1.0 | **0.5** | Caps the normal term, which is what pins grass to a solid fill. Depth silhouettes keep `DepthWeight=1.0`. |
| `FalloffEnd` | 8000 | unchanged | Long ramp retained. Shorten this first if 1200/0.5 proves insufficient. |

The instance is now attached on all 9 levels in `setup_nikki_render_post_process.py` (verified
`preferred: true` on every one). Tune further by editing the instance — never the master.

**Why both levers and not just `FalloffStart`:** `falloff` only attenuates geometry *beyond*
`FalloffStart`; anything nearer keeps a full-strength outline. And grass fires *both* edge terms —
the depth threshold is 1% of view distance, which grass-blade spacing exceeds easily — so distance
alone buys grass relief only by also weakening distant architecture. Trimming `NormalWeight` targets
the normal blowout directly and preserves more torii/temple silhouette for the same relief.

## ⚠️ FOUND 2026-08-01 — stale quarantined PPV still live in two levels, NOT fixed

`L_SakuraPath` contains **two enabled unbound post-process volumes**:

| Actor | Priority | Blendables |
|---|---|---|
| `PPV_NikkiDream` | 10.0 | `MI_PP_StorybookOutline`, `M_PP_MeluColorGrade` (current) |
| `PostProcessVolume` (unlabeled) | 0.0 | `M_PP_ToonOutline`, `M_PP_StorybookVines_Inst` — **quarantined** |

Weighted blendables **accumulate** across overlapping volumes, so `L_SakuraPath` is currently
running the old quarantined outline stacked on top of the new one. `L_Template` has the same stale
volume (and no `PPV_NikkiDream`), which means every level copied from that template inherits it.

**Deliberately not fixed.** `L_SakuraPath` art direction is human-owned (a standing rule in
`CLAUDE.md`), and `L_Template` propagates to future levels — both are owner calls, not an agent's.
The fix is to delete or disable the unlabeled volume in each. Note the two quarantined materials
were reported as having "zero referencers confirmed first" when they were quarantined; these two
level references were missed, because `.umap` actor references do not show up in a material
referencer check the way asset references do.

**Still open, art-direction call not a bug:** dense foliage (grass cards, `MI_ProcFoliage_NikkiDream`)
will still read as near-solid edge at close range, because adjacent blades genuinely are normal
discontinuities — no threshold can separate that from a silhouette. The durable fix is to stop
outlining foliage: either pull `FalloffStart` in so grass falls outside the outlined range, or drive
outlines from `CustomStencil` only (the material already reads it). Owner's decision.

## Original issue description — kept for context, superseded by the section above

Owner's last live report (in-viewport, `ZenForestTest`): outlines are visibly working and look good,
but something is still **"cutting off" / not framed properly** — described as similar in character to
the black-region bug that was just fixed, but the fix didn't fully resolve it. No screenshot or
further diagnosis was done after the depth-math fix landed. **Untested candidate causes, in rough
priority order:**
1. `FalloffStart`/`FalloffEnd` (3000/8000 world units, i.e. 30m/80m) may be cutting the outline off
   too aggressively at normal camera distances for some levels — try raising both, or setting
   `FalloffEnd` much higher, and see if "cuts off" resolves.
2. The multi-tap cross sampling (`uv ± texel*w`) near screen edges could be reading out-of-bounds
   scene-texture data (no clamping on the UV offsets) — if the cutoff correlates with screen edges
   specifically (not distance), this is the likely cause; needs a `saturate()`/clamp on the sampled
   UVs.
3. Could be a genuinely separate issue from the depth-normalization bug that was just fixed — don't
   assume they're the same root cause without checking.
Get a screenshot or have the owner describe exactly where/when "cuts off" happens (screen position?
distance-dependent? specific meshes?) before guessing further — this project has been burned
repeatedly this session by fixing based on inference instead of actually seeing the bug.

## The depth-edge bug that WAS found and fixed (context, not still open)

Root cause: `depthEdge / dC` (raw scene depth) combined with a hardcoded, never-calibrated `* 400.0`
multiplier blew the edge mask past 1.0 across broad areas of near-camera geometry instead of staying
confined to thin lines — visible as hard black rectangles on foreground meshes. Fixed by replacing
with a saturated, depth-relative threshold (`depthDelta / max(dC * 0.01, 1.0)`, saturated
independently before combining) and switching depth/normal combination from a summed weight to
`max()` (a pixel is an edge if *either* signal fires, not their sum — standard practice, the sum was
part of what caused the saturation blowout). Recompiled, saved, confirmed compiling clean. This fix
is real and should stay — the "cuts off" issue above is a **different**, not-yet-diagnosed problem.

## Integration point 1 — real-time reactive outlining via `CustomStencil` (relevant to Kiro: gameplay/UI)

The material reads each pixel's `CustomStencil` value and switches outline color to one of 3 presets
if it's non-zero:

| CustomStencil value | Behavior |
|---|---|
| `0` (default) | Normal catch-all ink — whatever `OutlineColor`/UDS tint resolves to. No setup needed. |
| `1` | Forces `Style1Color` (warm preset) |
| `2` | Forces `Style2Color` (cool preset) |
| `3` | Forces `Style3Color` (gold preset) |

**This is the hook for any gameplay-reactive outline** — highlighting an interactable object, a quest
target, a selected unit, a hover state. To use it on a mesh: enable **Render CustomDepth Pass** on
the component and set **Custom Depth Stencil Value** to 1/2/3. That's it — no material edit needed,
purely a per-actor/per-component property, settable at runtime from Blueprint or C++ (e.g. on
hover-enter/quest-active/selection-changed). This is real-time reactive by construction — stencil
values can change every frame if needed, the material re-reads it every pixel.

Preset colors are currently generic placeholders (warm/cool/gold) — if UI polish wants specific,
intentional colors here (e.g. matching an existing UI highlight palette), that's a parameter change on
this one material, not a new system.

## Integration point 2 — automatic UDS time-of-day tint (no gameplay hookup needed)

Outline color automatically shifts warm-at-dusk / cool-at-night via the same
`Day_to_Night_Color`/`UltraDynamicWeather_Parameters` pipeline the rest of the project's materials
already use — reuses the existing bridge, doesn't add a new one. Controlled by `UDSTintStrength`
(currently 0 = off by default until this is wired into a level and tuned). Nothing to hook up on the
gameplay/UI side; this is automatic once enabled.

## For Codex — Niagara/VFX interaction

**The outline mask is depth+normal-based, not color-based.** It will only outline geometry that
writes to the depth/normal G-buffer — most Niagara particle systems (translucent, additive-blend
sprites) **do not write depth**, so this outline generally won't react to or outline VFX, by design.
No coordination needed between your Niagara work and this material unless a specific effect is
opaque/depth-writing and someone wants it outlined too (mesh-renderer particles with an opaque
material could trigger it, sprite/ribbon renderers with additive blending won't).

One shared resource worth knowing about: `MF_PostProcessBlend` (which this material now uses) reads
a global blend-strength scalar from `MPC_PPBlending` (`Art of Shader`'s own MPC). If any Niagara-driven
post-process work ever touches that same MPC, coordinate — it's a shared dial, not per-material.

## Not yet done — don't build against these as if they exist

- `UDSTintStrength` and vine-growth (`VineBranchStrength`, opt-in, default 0) are unset/off — no
  level has been tuned with real values yet.
- Style preset colors (1/2/3) are placeholders, not final art direction.
- `MPC_Portfolio_Palette` per-level scene cohesion — abandoned this session, confirmed unreliable
  from the pure editor viewport (live-instance writes via `MaterialLibrary.set_scalar_parameter_value`
  don't read back correctly there). Don't resurrect this approach without first confirming it works
  in PIE/packaged context, which was never tested.
- ~~Screenshot capture is broken in this session's tooling.~~ **FALSE — corrected 2026-08-01 12:21.**
  `AutomationLibrary.take_high_res_screenshot` works. It appeared broken because the calling code
  slept on the game thread right after invoking it, which prevents the queued screenshot from ever
  flushing. Call it and return; check the file on a later call. See the capture section at the top of
  this file. (`HighResShot` as a console command routed through Monolith genuinely does not reach the
  viewport client — use the Python call.)

## Questions / requests back to the owner, not something either agent should decide unilaterally
- Final preset colors for the 3 stencil styles.
- Which specific meshes/interactions should actually drive `CustomStencil` values, and when.
