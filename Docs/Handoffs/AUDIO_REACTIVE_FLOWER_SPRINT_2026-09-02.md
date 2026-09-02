# Melodia — Tonight's Experimental Workplan
## Audio-Reactive Flowers → Cymatic World
**Date:** 2026-09-02 (Tonight)  
**Status:** Professional Workplan — Ready to Execute  
**Lens:** Infinity Nikki × Houdini Savant × Environment Designer  
**Principle:** Start simple (flowers breathe with music), prove the pipe, then scale to No Man's Sky experimental systems. No new landscape without permission, height-aware placement mandatory.

---

### 0. EXECUTIVE SUMMARY

Tonight we prove **one living thing**: flowers that hear music. Not a demo — a reusable audio-reactive grammar that scales from a single bloom to the Sea Above cathedral to planet-scale experimental worlds.

**The three-phase arc:**
```
Tonight:  Flower breathes (OSC → MPC → GN/Houdini → UE)  ← START HERE
Next:     Fabric / cymatic cathedral breathes (same pipe, bigger canvas)
Later:    World breathes (Massive Worlds + PCG at NMS scale, still from music)
```

**Why flowers first:** Single mesh, 4 parameters (scale/rotation/open/hue), instant visual payoff, zero terrain risk, validates the entire experimental stack in <4h. Nikki proves this — one hero garment at full fidelity > 20 at half.

---

### 1. EXISTING SPINE AUDIT — WHAT YOU ALREADY OWN

**You do not need to build infrastructure. It's there.**

| System | What Exists | Verified Path | Port / Contract |
|--------|-------------|---------------|-----------------|
| **OSC Bridge** | `deploy/osc_routing.json` schema, `Content/Python/osc_server.py`, `battle_osc.py` | 14 discrete battle routes wired | **8000** (TD→UE wardrobe), **9000** (UE→TD state/events) |
| **TouchDesigner** | `grandmaster_melodia.toe` + `wire_battle_osc.py` OSC In CHOP | Port 9000 listener, 14 handlers | TD CHOP network ready for CHOP→OSC |
| **LiveLink** | BlenderMCP + Melodia Studio Live Bridge | Blender 5.2 ↔ UE `/Game/LiveLink/` | **9876** TCP |
| **Audio Reactive** | `UMelodiaAudioReactivePresentationSubsystem` (Tier 1-3), `MelodiaMusicClockSubsystem` (Harmonix), `MelodiaCymaticsSubsystem` (Chladni read-only) | Single MPC writer `MPC_Melodia_Palette` (BeatPulse/Phase/Intensity) + read-only consumer | `BeatPulse [0,1]` `BassIntensity` |
| **Houdini** | 22.0.368 + Engine + Copernicus + COP Chladni (20.5 native), 65KB cymatic_parallax, dress_bake, terrain→Nanite | `hython.exe` present, WP25600 contract | `Tools/Houdini/copernicus/` |
| **Blender GN Audio** | **NEW 5.2 native `Sample Sound Frequencies` node** + `negdo/Sound_Nodes` lite available + `Audio2Blender` realtime | No addon required for base path | Bake → keyframes → GN attributes |
| **PCG/World** | 103 Python PCG builders, WP25600, Gaea LiquidCathedral, 333 Atlantis meshes, 36 Reef kit | 2 active PCG volumes | `Content/Python/pcg_scale_world_pipeline.py` |

**Critical constraint preserved:** `MelodiaCymaticsSubsystem` is READ-ONLY (`IsReadOnlyByContract()=true`). New audio writer must be separate MPC `MPC_Cymatics_Driver` or extend existing `MPC_Melodia_Palette` via single writer `UMelodiaAudioReactivePresentationSubsystem` — never add second writer.

**Port 9000 is single source of truth** (recon reconciles 9870 vs 9000 to 9000 per handoff docs).

---

### 2. TONIGHT'S MISSION — AUDIO-REACTIVE FLOWERS

#### 2.1 The Flower

**Canonical asset:** `SM_Flower_01` or dress from Reef kit (`Kelp Tall/Mid`, `Coral Table`) — pick ONE. Houdini/Reef kit has 36 built meshes not yet placed — repurpose one as hero flower. Alternative: Blender GN procedural flower (fastest to audio-drive).

**Parameters to breathe (only 4):**
- **Petal scale** → driven by `BassIntensity` (beat hits → bloom opens)
- **Stem sway** → driven by `BeatPhase` (sin wave, 0.02 drift)
- **Petal hue** → driven by Chladni mode (n,m) or audio spectrum band
- **Emissive pulse** → driven by `BeatPulse`

This is your Nikki Tier C → B test: shader/WPO for distant field, Chaos/VAT for hero bloom.

#### 2.2 Three Parallel Paths (pick one, prove, then layer)

**Path A — Blender GN (FASTEST, 2h, recommended tonight)**
```
Audio .wav → Blender 5.2 Sample Sound Frequencies node
  → GN: spectrum bands (bass 60-250Hz, mid 250-2000Hz, treble)
  → Drive: Instance Scale (petal instances), Rotate (WPO), Color (hue)
  → Bake: Keyframes → Alembic/VAT → UE `SK_Flower_Audio`
  → UE: MPC_Cymatics_Driver reads VAT time, material samples BeatPulse
```
- Uses native 5.2 node — no addon install, per `docs.blender.org` spec
- Fallback: `Sound_Nodes` lite if native insufficient (bakes to GN keyframes)
- Realtime bonus: `Audio2Blender` (mic → GN) for live improv capture → same path

**Path B — Houdini CHOP (SAVANT, 3h, most breathtaking)**
```
Audio → CHOP Network (File In CHOP → Spectrum CHOP → Filter → Lag)
  → SOP: VEX `cos(nπx)cos(mπy) - cos(mπx)cos(nπy)` with audio-driven n,m
  → SOP: Gradient field → particle advection (Marcus Kulik method)
  → COP: Chladni COP (non-integer mixed-mode) → Iridescence texture
  → HDA: `hda_flower_cymatic.hda` params Seed/audioBand/intensity → UE Cook
```
- Uses your COP Chladni native (20.5) + Kulik vector-field DOP
- CHOP replaces your formula's static n,m with audio-responsive: chord root→n, extension→m

**Path C — TouchDesigner OSC → UE (LIVE, 2h, uses existing OSC)**
```
Audio → TD CHOP (Audio Device In → Spectrum → Math → OSC Out)
  → OSC 9000: /melodia/audio/bass [0,1], /melodia/audio/mid, /melodia/beat/pulse
  → UE: osc_server.py receives → writes MPC_Melodia_Palette
  → UE: Flower material samples MPC, Niagara petals scale via MPC
  → TD: also drives its own particle vis for previz
```
- Leverages **existing** `wire_battle_osc.py` port 9000 + `battle_osc.py` sender
- Add 3 continuous routes to the 14 discrete: `/melodia/audio/*` — extend, don't duplicate
- CHOP→OSC→MPC is the live pipe the handoff docs explicitly ask for: "Stream continuous beat data, not just discrete events"

**Tonight's recommendation:** Run **A + C in parallel** (different owners, no conflict). A gives you baked hero asset for portfolio, C gives you live breathing in PIE. Houdini B is queued as overnight HDA cook after A validates the grammar.

#### 2.3 Acceptance Criteria — Flower Breathes

- [ ] One flower mesh in `LV_SeaAbove_Prototype` or `L_PetalCantata` at height-aware Z (raycast to landscape, not floating)
- [ ] In PIE, flower visibly pulses/opens with music (either baked VAT loop or live OSC→MPC)
- [ ] Material shows hue shift tied to audio (IridescenceTint or emissive, not just scale)
- [ ] 10s screen capture committed to `Saved/Audit/flower_audio_2026-09-02.mp4`
- [ ] No second MPC writer — proof via `MPC_Melodia_Palette` or new `MPC_Cymatics_Driver` single writer

---

### 3. BUILDING ONWARD — THE ONWARD LADDER

Once flower breathes, the *same 4 parameters* scale:

**Week 1 — Fabric / Cymatic Cathedral**
- Same OSC→MPC pipe drives Cathedral kitbash (193 pieces) Iridescence/Emissive
- Marcus Kulik grains flowing to Chladni nodes across nave (GildedLoom/CavernWeave MIs)
- Copernicus mixed-mode regeneration of 12 MIs with audio-driven n,m
- PCGEx `PCG_Hero_ResonanceCathedral` (86 instances) scale via BeatPulse

**Week 2 — NMS-Scale Experimental**
- Gaea LiquidCathedral → Massive Worlds Toolkit → World Partition tiled landscape (5000×3000 → 25600 cells)
- Seeded procedural: music key → cymatic family → biome selection (NMS philosophy: 60 min unique music per planet)
- Houdini heightfield COPs (`Houdini 22 | How to Create Terrains in COPs`) + PCG biome graphs across streaming cells

**Shared contract:** One seeded audio source → Chladni mode → texture → placement. Deterministic, replayable, debuggable.

---

### 4. TONIGHT'S EXECUTION PLAN — 4 HOURS

| Time | Owner | Task | Tool | Output |
|------|-------|------|------|--------|
| **T+0:00** | Env Designer | Health check: prove OSC 9000 listener, MPC_Melodia_Palette values in PIE | `validate_osc_loop.py`, `orchestrator` console | `Saved/Audit/osc_health_2026-09-02.json` PASS |
| **T+0:30** | Blender Op | Build GN flower: Sample Sound Frequencies → instance scale + hue | Blender 5.2, GN editor | `Exports/FlowerAudio/SK_Flower_Audio.blend` + `.abc` |
| **T+0:30** | TD/Houdini Op | Wire TD CHOP→OSC: spectrum → 3 bands → OSC 9000 (parallel, not blocking) | `grandmaster_melodia.toe`, `wire_battle_osc.py` ext | `/melodia/audio/*` routes live |
| **T+1:30** | UE Integrator | Import flower, height-aware place in SeaAbove or PetalCantata, bind MPC to material | Monolith `mesh_query`, `M_Flower_Audio` | Flower in level, material WPO + emissive bound |
| **T+2:30** | PIE Tester | Live PIE: music plays → flower breathes, capture | PIE + `MelodiaCaptureRenderSubsystem` | `Saved/Audit/flower_audio_*.mp4` + `*.json` |
| **T+3:00** | Houdini Op (overnight) | Stage HDA: `copernicus_cymatic_parallax` variant for flower Iridescence | `hython copernicus_cymatic_parallax.py --variant StarlitLoom` | `Saved/Audit/copernicus_cymatic/flower/` 9 maps |
| **T+3:30** | Lead | Review + gate decision: keep baked vs live pipe, queue cathedral pass | - | Decision log, next night queued |

**Parallelization rule:** No two owners touch same graph/level (AGENTS.md #7, #17). Source/C++ builds while TD runs. One editor lock only.

---

### 5. RISKS & MITIGATIONS

| Risk | Mitigation |
|------|------------|
| Audio file not in project | Ship with `Content/Audio/128BPMarpeggiomelody_beatgrid` (already validated tempo/bar/beat maps) |
| Apprentice COP 1080p cap | Tonight use 1K bake, queue 4K on Indie/Core overnight |
| OSC UDP unverified | Use `wardrobe_bridge_health.py --probe-udp` + TD OSC In monitor, not blind send |
| NavMesh not baked | Flower is decorative first — no collision needed for breath test |
| Second MPC writer | Grep `GetParameterCollectionInstance` writes — only `UMelodiaAudioReactivePresentationSubsystem` may write `MPC_Melodia_Palette` |

---

### 6. WHAT TO COMMIT TONIGHT

- `Docs/Handoffs/AUDIO_REACTIVE_FLOWER_SPRINT_2026-09-02.md` (this plan)
- `Exports/FlowerAudio/` (BLEND + ABC + spectral texture if baked)
- `Saved/Audit/flower_audio_*.json` + `.mp4` (gate evidence)
- NO `.uasset` hand-edits without evidence; NO duplicate landscape

---

### 7. RESEARCH ATLAS — CURATED SOURCES (FOR NEXT PASSES)

**Cymatic Breathtaking:**
- Kulik Chladni Plate Engine — `marcuskulik.com/tech/chladniengine`
- SideFX COP Chladni — `sidefx.com/docs/houdini/nodes/cop/chladni.html`
- Entagma VEX101 Chladni — `entagma.com/vex101-pt-9-creating-chladni-patterns/`
- motion-cops — `github.com/Boning1011/motion-cops` (COPs motion toolkit)

**Blender GN Audio (hot):**
- Blender 5.2 Sample Sound Frequencies — `docs.blender.org/manual/en/latest/modeling/geometry_nodes/utilities/sound/sample_sound_frequencies.html`
- Sound_Nodes — `github.com/negdo/Sound_Nodes` (lite free)
- Audio2Blender realtime — `github.com/tom-malaeasy/Audio2Blender`
- GN Visualizer tut — `blendernation.com/2026/08/08/create-an-audio-visualizer-with-geometry-nodes-in-blender-5-2/`

**NMS Scale:**
- Massive Worlds Toolkit — `ehoudiniacademy.com/massiveworlds/` + `youtube.com/watch?v=dly2haJU_Po`
- Compositing Props for WP (EPC 2025) — `youtube.com/watch?v=IYXztEFeBBY`
- GDC Sound of NMS — `gdcvault.com/play/1024067` + `asoundeffect.com/no-mans-sky-sound-procedural-audio/`
- Houdini Copernicus Terrains — `youtube.com/watch?v=5v9lmJcIrIw`

Full deep digests incoming from research scouts — this plan already incorporates their verified findings. Detailed per-tool Handoff + hip specs queued for overnight.

---

**Tonight's first action (pick one to start):**
1. Run `python Tools/validate_osc_loop.py` + check `MPC_Melodia_Palette` in PIE (15 min health gate)
2. Open Blender 5.2 → GN → `Sample Sound Frequencies` prototype on a 6-petal flower (30 min)
3. Open `grandmaster_melodia.toe` → add CHOP spectrum → OSC Out on 9000 for `/melodia/audio/bass`

Say the word and I queue the first daemon.

*— Melusina, 2026-09-02, for the night shift*
