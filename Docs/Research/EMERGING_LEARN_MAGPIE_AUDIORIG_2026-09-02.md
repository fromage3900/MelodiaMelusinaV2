# LEARN 2026-09-02 — Magpie co-arse-to-real renderer + Houdini no-CHOP audio rig

**Source threads baked into this hour's loom.** Magpie = direct hit on the
`UMelodiaVisualRepresentationSubsystem` WATCH seam (§3 Master Index). The r/Houdini
audio rig = a buildable, no-CHOP cymatic alternative worth a probe.

---

## 1. Magpie — real-time generative world renderer (arxiv 2608.27168)

**Reference:** https://arxiv.org/pdf/2608.27168.pdf (Mogo AI Ltd + Nanjing U + Southampton)

**Core idea — "coarse-to-real", not engine-replacement.** Magpie does NOT replace the
game engine with a generative model. It *separates gameplay from visuals*:

- **Game Engine** keeps authority over logic: physics, collisions, state, progression
  flags, cooldowns, hidden triggers. All runtime gameplay truth lives here.
- Engine emits a **white-box frame** — a render stripped of textures/materials but with
  all structural + depth info and camera pose — the structural guide.
- **Render Server** (generative) denoises that white-box into the final high-fidelity
  frame. Continues previous denoise with pose-retrieved historical frames.
- Because only the white-box (not raw game state) crosses the boundary, the generator
  *cannot* contradict gameplay collisions — if the engine says the character hit the
  wall, the white-box shows the wall, the renderer honors it.

**Why this matters to Melodia:** this is *exactly* the architecture our
`UMelodiaVisualRepresentationSubsystem` scaffolds — "Magpie simulation↔visual seam
(read-only)". The subsys stays a WATCH/promotable item because we lack (a) the trained
render-server model and (b) a white-box SceneCapture path. Both are knowable:

- **White-box capture** = our existing `UMelodiaCaptureRenderSubsystem` offscreen
  SceneCapture HDR pipeline (4-view, PPV gate) — currently used for contact sheets, but
  the exact same 4-view capture is what a generative render server would consume.
- **Training data** = 300h of paired UE white-box/final video — we cannot collect this
  in a night's loom. So: **PARK full Magpie promotion** (model absence is §3 gate),
  but **ADOPT the white-box-frame discipline** for our capture pipeline so a future
  render server can slot in. Alignment: Render Server takes camera pose + frame; our
  capture rig already transmits pose + 4-view passes.

**Designable + reproducible** is the killer property for us — matches the project rule
"gameplay authority + final composition stay in Unreal; bake — never leave final
playable scenes dependent on live HDA cooking."

## 2. Houdini audio rig WITHOUT CHOPs (r/Houdini 1pneydl)

**Reference:** https://www.reddit.com/r/Houdini/comments/1pneydl/houdini_audio_reactive_rig_download/

A lightweight drop-in **audio→motion rig that bypasses CHOPs**: a single **Python SOP**
reads and analyzes a WAV and emits motion/attributes directly, instead of a CHOP network.
Value for Melodia: our cymatic pipeline is C++-native and Houdini-parallel; a pure
Python-SOP audio->geometry path is **copy-portable into our `copernicus_cymatic_parallax`
toolchain** without Houdini CHOP licensing/semantics. It trades CHOP realtime buffering
for offline readability — fine for baked VDM/capture rigs.

Companion thread (r/Houdini 1nw692k, RBD CHOP audio-reactive, free tutorial+hip): the
classic **CHOP log-scale pitfall** — File CHOP output must be converted to log scale on
BOTH X and Y or bass-heavy audio swamps the sim (DC dominated by kick). Encoding this
into our CHOP lineage: any future Non-cyclical CHOP import MUST `log-scale` both axes
before driving displacement/scatter, else the kick masks everything.

**Adopt/Park:** ADOPT the awareness (Python-SOP path available if we ever need
non-CHOP offline audio→geometry); the CHOP double-log-scale rule is a real pipeline rule,
recorded for any Houdini audio impulse. REJECT wholesale CHOP-network rebuild — cymatic
is already PRESENT in C++.

---

## Pipeline rules touched
1. **White-box discipline** — capture rig emits clean 4-view + pose, render-server-ready.
2. **Bake don't live-cook** — generator/CHOP input to geometry is offline; playable
   scenes never depend on live Houdini/Magpie cook.
3. **No second cymatic writer** — Python-SOP audio rig is a *parallel/bake* tool, never a
   PIE-time MPC writer (single-writer guard holds).
4. **Height-aware everywhere** — any captured/placed geometry raycasts to CanonicalLandscape.