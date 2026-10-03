# Audio-Reactive Systems — Canon

**Written:** 2026-10-03. **Status authority:** `CURRENT_STATE.md`. This page is the single map of how audio and
cymatic reactivity flow through the project. Older docs (`MPC_UNIFY_FABRIC_PLAN_2026-08-20`,
`MELODIA_CYMATICS_MONOLITH_HOUDINI_EMERGING3D_PIPELINE`, `UNIVERSE_FOUNDRY_CONTRACT` §10) agree with it on
authority; where they disagree on *what is wired*, this page wins because each row below was read from code on
the date above.

## 1. The chain

```text
TouchDesigner (_TouchDesigner/grandmaster_melodia)   5-band split + beat + pitch
   | OSC UDP :8000  (editor only, see §5)
   v
Content/Python/osc_server.py   (started by init_unreal.py::_register_osc_bridge, raw sockets, 26 routes)
   |  writes MPC_Melodia_Palette: Bass/BassIntensity/Mid/Treble/TrebleIntensity, BeatPulse/BeatIntensity/BeatPhase,
   |  PaletteShift, GlobalAudioReactivity, wind
   v
MPC_Melodia_Palette  (/Game/Melodia/_PROJECT/04_Materials/)   <- canonical; 54 scalars / 17 vectors
   ^  C++ writers (game logic)                                   (a 17-scalar fork exists at /Game/_PROJECT/..., unread)
   |   UMelodiaAudioReactivePresentationSubsystem  beat namespace + Bass/Mid/Treble fallback + MPC_MelodiaInk lane
   |   UMelodiaRhythmReactivitySubsystem            RhythmPulse, GlobalSparkleIntensity (note/command/victory events)
   |   UMelodiaQuantumDrawSubsystem                 QuantumPulse (draw results)
   v
UMelodiaCymaticsWriterSubsystem   SOLE writer of MPC_Cymatics_Driver
   |  Cymatic_BeatPulse (driven pulse), _Bass/_MidIntensity, _EmissiveScale, _IridescenceShift, _UVDistortion,
   |  _ModeN/_ModeM, _WindDirX/Y, _WindStrength
   v
Materials (flower master M_MelodiaPlant_Wind, SDF/Simple/Character/Unified toon masters, landscape master emission,
Oceanology MIDs) and Niagara (NS_Uni_WaterMist reads PlayerProximity)

UMelodiaCymaticsSubsystem  (read-only)  -> Chladni modes from palette -> UWorldFieldBus::PublishResonance
UWorldFieldBus                           -> UMelodiaOceanologyWaterBridgeSubsystem (water ripples)
```

## 2. Authority rules (binding)

- One writer per surface. Palette beat namespace: `UMelodiaAudioReactivePresentationSubsystem`. `RhythmPulse` and
  `GlobalSparkleIntensity`: `UMelodiaRhythmReactivitySubsystem`. `QuantumPulse`: `UMelodiaQuantumDrawSubsystem`.
  `MPC_Cymatics_Driver`: `UMelodiaCymaticsWriterSubsystem` only. `MPC_MelodiaInk` Ink lane: the presentation subsystem.
- `UMelodiaCymaticsSubsystem` and `UWorldFieldBus` consumers are read-only; nothing calls cymatics directly.
- No second OSC bridge, no second MPC/audio writer (also `UNIVERSE_FOUNDRY_CONTRACT` §10, `WORLD_COMPILER_CONTRACT`).
- OSC wins over C++ for `Bass/Mid/Treble` in PIE (the Python flush lands after the C++ write; verified 2026-10-03).

## 3. Lane semantics — read before binding anything

| Lane | Source in a TD session | Source without TD |
|---|---|---|
| `Bass` | OSC `/audio/band/sub` (~80 Hz RMS) or `/melodia/audio/bass` | combat intensity (battle only, else 0) |
| `BassIntensity` | OSC `/audio/band/low` | same combat intensity |
| `Mid` / `MidIntensity` | OSC `/audio/band/mid` | decaying impact pulse |
| `Treble` | OSC `/audio/band/high` | beat pulse (cos²) |
| `BeatPulse` / `BeatIntensity` | OSC `/melodia/audio/beat/pulse`, `/rhythm/beat_pulse` | music clock cos² (continuous) |
| `RhythmPulse` | player command energy (sticky until encounter ends) | same |
| `GlobalSparkleIntensity` | command/victory pulse, decays 5/s | same |
| `QuantumPulse` | Quantum draw result, decays 3.5/s | same |
| `Cymatic_BeatPulse` | `ComputeDrivenPulse(BeatPulse, max(Sparkle, Quantum))` | same |

Without TD, `Bass` carries *combat intensity*, not low-frequency energy. Bind by meaning.

## 4. Consumer table (state as of 2026-10-03)

| Consumer | Reads | Verified |
|---|---|---|
| `M_PP_MelodiaInk_Frozen` | palette: Beat, Break, Combo, EnemyTension, MeluPrimary, Victory; Ink*: 8 lanes | text export |
| `M_PP_MeluColorGrade_Frozen` | palette: BeatIntensity, BeatPulse, GlobalEmissiveBoost, MeluPrimary, RhythmPulse, VictoryPulse; `InkSyncVision` | text export |
| `M_PP_StorybookOutline_Render2026` | `RhythmPulse` | text export |
| `M_PP_StarryNightOverlay_Candidate`, `M_PP_EdgeDesat` | static palette colours / nothing (no audio) | text export |
| `M_Master_SDF_Toon` | Cymatics driver (1) + palette (3) | text export |
| `M_Master_Simple_Universal`, `_Toon_Character`, `_Toon_Unified` | Cymatics driver (1) | text export |
| `M_Master_Gemstone` | palette (3) | text export |
| `M_Master_Toon_Universal` (DreamRim) | palette Bass, Mid, Treble, BeatPulse, GlobalSparkleIntensity, ... via its graph | owner-reported, graph reads not enumerable by CollectionParameter scan |
| `M_Master_Nikki_Landscape` | beat -> bounded additive emission (`CymaticsLandscapeMaxEmission`) | `fix_landscape_cymatics_response.py` |
| `M_MelodiaPlant_Wind` | `WindDirX/Y`, `WindStrength` (palette), `Cymatic_BeatPulse/EmissiveScale` (driver) | PIE-verified 2026-10-03 |
| Oceanology lake MID | `Biolum_Intensity = 1 + DrivenPulse*1.5` (C++ pushes MI params; the plugin master cannot sample an MPC) | PIE-verified |
| Oceanology ripples | `UWorldFieldBus` Resonance/Tension | wired 2026-10-03 (see §6) |
| `UMelodiaCymaticFieldComponent` (new) | `UWorldFieldBus` Tension/Beat/ModeN/M -> Chladni lift + scale of tagged PCG ISM instances, hit ripples | built 2026-10-03, PIE proof owed |
| Piano keys (`APCGPianoKey`) | write: `NotifyPlayedNote`, `NotifyCommandResolved` -> Sparkle/RhythmPulse | PIE-verified |

Note on scans: counting `CollectionParameter` nodes misses reads made inside material functions; treat a
"no reads" result for a master as unproven, not as absence.

## 5. Known limits

- **The OSC bridge is editor-only.** `osc_server.py` is started from editor Python (`init_unreal.py`). A packaged build
  has no TD input; it runs on the C++ fallbacks in §3. A shipping TD path would need a native OSC receiver that
  writes into the same single palette writer, not a second one.
- Wind arrives from `/niagara/wind` as `abs(x)` into `MPC_SakuraDream.WindStrength` — a legacy lane, separate from the
  palette `WindDirX/Y/Strength` lanes the flower master actually uses.
- `UMelodiaCymaticsSubsystem` derives modes from `BassIntensity`/`BeatPulse`; it has no spatial awareness. The bus
  applies a Faraway-Mother 5000 uu radial falloff to Tension.
- PCG geometry reacts through `UMelodiaCymaticFieldComponent` (CPU, budgeted, tagged instances only). Landscape
  *geometry* (WPO / RVT) does not read the bus yet; the Nikki landscape reacts through emission only.
  `MelodiaWorldFieldBus.h` lists RVT / PCG-metadata representations as intent, not as built.

## 6. Change log

- 2026-10-03 — `UMelodiaCymaticsSubsystem::RefreshFromMPC` now calls `UWorldFieldBus::PublishResonance`. Before this,
  `PublishResonance` had no caller, so the water-ripple drive read compiled-in defaults forever. Tension is
  `saturate(max(Bass, BeatPulse))`.
- 2026-10-03 — Ink lane (`InkReact/InkBass/InkMid/InkTreble`) mirrors the palette's Bass/Mid/Treble as they stand before
  the frame's C++ writes, so OSC analysis reaches the post-process ink.
- 2026-10-03 — `NotifyPlayedNote`/`NotifyCommandResolved` from piano key presses; `ComputeDrivenPulse` shared by the
  cymatics writer and the ocean drive.

## 7. Geometry, PCG and cymatic hits (canon, 2026-10-03)

`UMelodiaCymaticFieldComponent` (`Source/BS_GodFile/PCG/`) is the one geometry consumer of the field:
- Put it on a trigger/volume actor. Targets: ISM components (or actors) tagged `MelodiaCymatic` within `ReactRadius`;
  for PCG, add that tag to the Static Mesh Spawner descriptor `ComponentTags`, or set `bReactToAllInstancedMeshes`.
- Standing wave: `lift = MaxLiftCm * |Chladni(N,M,u,v)| * Tension`; modes and tension come from the bus, never from
  cymatics directly. Hits: Pawn overlap, beat edge (`bHitOnBeat`) or `TriggerHit()` start an expanding ripple and resolve a
  Great command on `UMelodiaRhythmReactivitySubsystem`, which pulses the palette and sends the beat out over OSC.
- Game worlds only; instances are restored at EndPlay. Budget `MaxInstances`, `UpdateHz`.

**Houdini Engine (canon amendment, owner direction 2026-10-03).** Live Houdini Engine procedural creation is part of the
authoring canon: HDAs cook live in the editor through the `HoudiniEngine` plugin, feed PCG/World Field inputs, and bake
to versioned assets. Previous docs prohibit *runtime* Houdini cooking (`FARAWAY_MOTHER_PCG_SYSTEM_ARCHITECTURE` §7,
`UNIVERSE_FOUNDRY_CONTRACT` §10, pipeline doc §4.1); that remains the shipping boundary until a packaged-HE plan exists.
Those docs still say "no live cooking" and need the owner's sign-off to be reworded.

## 8. Next steps (each needs an owner call)

1. `M_PP_MeluColorGrade_Frozen` Bass/Mid/Treble reads (master edit).
2. Landscape WPO/RVT consumer of `UWorldFieldBus`, and a Houdini Engine HDA that outputs PCG points tagged for the component.
3. Retire the 17-scalar `MPC_Melodia_Palette` fork.
4. Native OSC receiver for packaged builds.

## 9. Convergence plan — universal healthy audio reactivity

**Goal (owner, 2026-10-03):** one documented, single-writer audio/cymatic spine that every visible layer follows —
post-process, surface materials, water, PCG and landscape geometry, hits — authored live (Houdini Engine) and proven in
a packaged build. Done = every row of §4 is `proven` with evidence, §5 limits are closed or explicitly accepted, and the
health check (P1) is green. Nothing below adds a second writer, a second OSC semantic bridge, a second compiler or a
second save authority (§2). Orchestration rides the existing Hermes plan
(`.hermes/plans/2026-09-26_hermes-orchestrator-infra-plan.md`) — extend it, no parallel router.

Roles: **Sol** directs and verifies; **Hermes** dispatches long jobs; **Sonnet workers** do scoped read-only/bulk work;
**Jev** picks only among closed candidate sets; **one editor writer** at a time; **Unreal proves** (screenshots + numbers).
Delegated output is not evidence — look at the artifact.

| Phase | Work | Owner gate | Exit evidence |
|---|---|---|---|
| **P0 Prove the build** | Relaunch on the new binaries. PIE with the OSC test sender: ink lane follows `Bass/Mid/Treble`; water ripples move (bus publishes); piano run + `UMelodiaCymaticFieldComponent` on a Sea Above volume lifts tagged ISMs and ripples on Pawn overlap; glide feel; save dirty packages | none | Numbers (MPC values per frame) + front-view screenshots per row; component recorded at foreground fps |
| **P1 Health baseline** | `Tools/validate_audio_reactive_health.py` + Echo test: writers load their MPCs, every parameter a consumer reads exists in its collection, bus published within N frames, OSC :8000 bound, no duplicate `MPC_Melodia_Palette`. Retire the 17-scalar fork (owner approval: delete/move `.uasset`). Fix the PPV: label, weight 0.18 vs 0.69, surface-domain slot dropped | retire fork; PPV weight | Health check green in CI and in-editor; PPV report matches canon |
| **P2 Surface + post-process** | `M_PP_MeluColorGrade_Frozen` reads `Bass/Mid/Treble` (A/B at low/high MPC, >1.3% pixel delta target); resolve ebony dream-rim magenta; enumerate real master reads (function-level, not node count) and fill §4 | master edit (PP + any Toon change) | A/B screenshot pairs; compile stats; §4 rows promoted to `proven` |
| **P3 Geometry + landscape** | Component placed in Sea Above and Morning West Rim (golden-ratio piano paths, DreamRim keys, Niagara hits bound to beat). Landscape: gated WPO (`AudioReactAmount` default 0) reading the driver lanes via `MF_FabricMountainWPO`, instances opt in; RVT consumer of the bus if WPO is not enough | WPO master/function edit | Per-level PIE capture; instance-count and ms budget table; zero change with amount 0 |
| **P4 Houdini Engine live authoring** | HDA outputs PCG points tagged for the component and carries `Resonance/EcologyClass` attributes; live cook in editor, bake to versioned assets; Foundry mission gains the HDA task (World Genome unchanged). Reword the three "no live cooking" docs | doc rewording; HE licence/packaging statement | One HDA cooked live -> PCG -> reacting instances; baked asset reproducible from genome + seed |
| **P5 Packaged parity** | Packaged builds lose the editor-only Python OSC bridge. Decision needed: native OSC receiver that replaces the Python shim as the single bridge (recommended), or accept C++ fallbacks only. Then packaged 60 fps harness run with the reactive stack on | bridge decision; packaging | Packaged run: audio-driven lanes move, fps/frame-time table, no per-frame allocation in the component |
| **P6 Canonization** | This document stays the SSOT: `CURRENT_STATE.md` gets an entry and a pointer; mirror the binding rules into `AGENTS.md` for Hermes; TD/Embody side documents its OSC routes in `deploy/osc_routing.json`; link from `CURRENT_SYSTEM_MAP.md` | none | One entry per change in §6; stale statements in older docs corrected or annotated |

**Dependencies:** P0 gates everything. P1 before P2/P3 (so every later change is health-checked). P2 and P3 can run in
parallel on different surfaces only if one editor writer is respected (serialize editor sessions). P4 needs P3's
component tag contract. P5 is independent of P2-P4 except the final packaged proof.

**Risks:** per-instance CPU updates on dense PCG (mitigated by budget/Hz; escalate to WPO + instance custom data if over
budget); master edits regress 1,700+ instances (gate with default-off params, compile-stat check after each edit);
bus Tension carries the Faraway radial falloff (sample at origin for raw, or add a spatial-field API in P3); editor
crash from Live Coding (full builds only); `HighResShot` and 3 fps editor throttle distort captures (use a foreground
client or the 60 fps harness).

**Bounded asks for the owner:** retire the palette fork; approve PP/Toon/WPO master edits per phase; choose the packaged
OSC bridge; sign off the Houdini Engine doc rewording; confirm the Sea Above volume that triggers OSC (the existing
trigger script was not found in the repo).
