# TouchEngine ↔ Unreal Engine 5.8 — Runtime Integration Contract

**Authority:** `fromage3900/MelodiaMelusinaV2` (game, runtime, signals, implementation gates)  
**TD component source:** `fromage3900/MelodiaTouchDesigner` (authoring, `.tox` exports, TD-specific QA)  
**Owner direction:** 2026-10-11 — pursue TouchEngine as a **canon-bound runtime presentation system**, with *installation / UE 5.8 build / PIE / packaged support still UNVERIFIED*.  
**Current status & priorities:** `CURRENT_STATE.md` **only**. This contract is technical architecture and staged acceptance criteria, not a separate status ledger.

## Goal and non-goals

Embed **one** bounded TouchDesigner `.tox` network through the official TouchEngine-UE plugin so a real Melodia gameplay/music value drives a UE-visible visual texture in PIE. Preserve the existing UE 5.8 / TouchDesigner Spout + OSC workflow during bring-up.

- **Do:** opt-in, presentation-only TouchEngine execution; single UE-side adapter; a known fallback; measurable canary; pin UE/TouchDesigner/plugin/TD commit and source asset.
- **Do not:** vendor the entire TD repo or a second `.toe` into the game; create a new OSC port/beat clock/audio bus/MPC writer; let TD decide quests, HP, saves, hit grading, traversal or authoritative world field values; reparent Melusina's pawn; silently change packaged build dependencies.
- **Do not claim:** UE 5.8 compatibility, running PIE, a packaged game, or shipping rights until separately demonstrated on the actual workstation and license/deployment target.

## Existing system boundaries — reuse, don't replace

| Layer | Authority / route | TouchEngine responsibility |
|---|---|---|
| Musical/game truth | `UMelodiaRhythmReactivitySubsystem`, canonical music-clock and hybrid systems in UE | Receive normalized **presentation parameters** from a single UE adapter; never run an independent clock. |
| Audio/cymatics/palette | `UMelodiaAudioReactivePresentationSubsystem`, `UMelodiaCymaticsSubsystem`, `UMelodiaCymaticsWriterSubsystem`, `MPC_Cymatics_Driver`, `MPC_Melodia_Palette` | Output textures/control visualization. **No direct writes** to existing MPC scalars from a second path. |
| Existing external live TD bridge | UE→TD semantic OSC UDP `:9000`; phrase bridge→UE `:9002`; TD→Blender `:9001`; hand bridge→TD `:7001` | Remain separate and working. Embedded TouchEngine should use plugin inputs/outputs, **not a loopback OSC bridge** for the first canary. |
| Banned legacy route | UDP `:8000` ghost receiver / dual-writer hazard | Never revive. Any future TD→UE OSC lane requires the existing port-contract approval and census. |
| GPU live lookdev | Existing `Plugins/UE5_Spout2_DX12`, UE beauty → TD compositing, TD presentation return where actually proven | Coexist; do not remove/overwrite sender names, Spout components, or the external editor pipeline. |
| World response | UE native materials, Niagara, PCG, World Compiler | TouchEngine's TOP is a **visual input**, not a world-state mutation system. |

Read the authoritative `Docs/TouchDesigner/MELODIA_TD_AE_CROSS_REPO_CONTRACT_2026-09-08.md` and `Docs/Production/SIGNAL_VOCABULARY_2026-09-25.md` before wiring a live signal. Older `deploy/osc_routing.json` header/TD `docs/UE_REALTIME_HUB.md` port prose is historically conflicting; don't infer a :9000 UE inbound receiver.

## Dataflow: first embedded visual canary

```text
UE authoritative rhythm/music state
        |
        | normalized, clamped BeatPhase and Amplitude
        v
Single UE presentation adapter (one writer, no OSC socket)
        |
        | TouchEngine component inputs / custom parameters
        v
TE_MelodiaCanary (TouchEngine Actor; .tox exported from TD repo)
        |
        | TD executes simple TOP network in embedded TouchEngine process
        v
OUT_BEAUTY (TOP) -> valid UE texture -> MID on debug plane
        |
        +-- unavailable / failed load / dropped / stale --> native UE fallback
```

**Proposed canary interface `melodia.touchengine_canary/v1`** (new contract, not yet implemented):

| Parameter or output | Direction | Meaning | Validation |
|---|---|---|---|
| `BeatPhase` | UE → TouchEngine custom parameter | Normalized beat phase | float `[0,1]`; finite; independent from display framerate |
| `Amplitude` | UE → TouchEngine custom parameter | Normalized presentation energy | float `[0,1]`; finite; default `0` |
| `OUT_BEAUTY` | TouchEngine → UE TOP | Distinct reactive image | first proof: 256×256 RGBA; verify alpha/color-space in Unreal |
| optional `OUT_DIAG` | TouchEngine → UE DAT/CHOP | Optional diagnostic frame/cook data | Not required for Gate 1 |

Naming is the **desired cross-repo handoff**; confirm the parameter identifiers actually exposed by the `.tox` and plugin before connecting Blueprints. Do not invent unreleased C++ APIs or assume 5.7 Blueprint pins are unchanged in a 5.8 port.

## Implementation sequence — UE lane (strict gates)

### G0 — Plugin compatibility and machine preflight [PROVEN 2026-10-11 on UE 5.8; see result below]

1. Record the exact UE **5.8** engine build, Windows/DirectX/RHI, TouchDesigner Commercial build, and TouchEngine-UE plugin SHA/version. The upstream official sample is currently documented for **UE 5.7.x / plugin 1.7.0**; UE 5.8 is a compatibility experiment, not supported by assertion.
2. Work in a **disposable 5.8 compatibility project / isolated integration lane**. Keep the production `BS_GodFile.uproject` and Spout plugin untouched until loading/build succeeds.
3. Verify plugin module compilation, editor startup, runtime library lookup, appropriate paid license activation, and one successful load/unload. Check logs for missing DLLs, ABI/deprecated API issues and crash-on-exit.
4. Do not copy compiled binaries or third-party runtime files into Git; use existing Perforce/vendor policies for permitted binary artifacts. Record source version/patch and build steps so another workstation can reproduce.
5. **Exit:** editor launches with the plugin enabled and the official sample or minimalist `.tox` reports load success **in UE 5.8**. On failure: stop, document exact compiler/runtime error in the task/PR, and retain Spout-only production.

**G0 result (2026-10-11, owner-waived disposable-lab gate).** The owner has an active TouchDesigner Commercial license and waived the disposable-project step ("not too worried about compatibility"), so G0 ran in the production project with `BS_GodFile.uproject` enabling `TouchEngine` locally (the uproject change is intentionally NOT landed in Git/P4 until G1).
- Closed-editor `Build.bat BS_GodFileEditor Win64 Development` exit 0. Editor 5.8 log: `TouchEngine`, `TouchEngineEditor`, `TouchEngineD3D11RHI`, `TouchEngineD3D12RHI`, `TouchEngineVulkanRHI` all loaded, no plugin error, engine initialized.
- Two UE 5.7 -> 5.8 source breaks patched (plugin source is landed under `Plugins/TouchEngine/`):
  1. `Public/Engine/Util/CookFrameData.h`: `UENUM ECookFrameResult` lacked `#include "CookFrameData.generated.h"`; 5.8 deletes `StaticEnum<>` without it (C2280 in `TouchEngineComponent.cpp`/`TouchFrameCooker.cpp`).
  2. `TouchEngineD3D12RHI/.../ExportedTextureD3D12.cpp:205`: `ID3D12DynamicRHI::RHIWaitManualFence` gained a 4th arg `const TSharedPtr<std::atomic<bool>>& bHasSignalled`; pass `nullptr` (5.8 submission code null-checks it).
- Not in Git by policy (G0 step 4): `Plugins/TouchEngine/Binaries/` (incl. `ThirdParty/Win64/TouchEngine.dll/.lib` from the Derivative 1.7.0 release). Reproduce by installing the 1.7.0 release binaries, applying the two patches above (already in the landed source) and doing a closed-editor build.
- Still open: load/unload of a real `.tox` and crash-on-exit check belong to G1.

### G1 — Isolated `.tox` TOP canary [first actual proof]

1. TD side supplies a self-contained `melodia_te_canary_v1.tox`, exported from a **COMP** with only the two agreed input parameters and `OUT_BEAUTY`. It must not require the complete grandmaster network, OSC sockets, cameras or external file paths.
2. Import it as a **TouchEngine ToxAsset** using a project-relative path under UE `Content` (never an absolute-only external path). The official plugin documentation notes that absolute `.tox` asset paths are **not packaged**.
3. In the test project, create **a dedicated TouchEngine Actor-derived Blueprint** (`TE_MelodiaCanary`), not a reparented player/character. Assign the ToxAsset. Bind documented `On Tox Loaded`, `On Tox Failed Load` and `On End Frame` callbacks; query parameters/outputs after successful load.
4. Bind constant/slider test values; verify `OUT_BEAUTY` changes and can be displayed on a single debug plane via UE material instance. Explicitly verify successful frame/update before replacing a texture; record dropped frames and latency.
5. **Exit:** visible, repeatable parameter→image change in UE PIE. If Tox load fails or stops, native material/neutral texture remains visible; game input and gameplay are unaffected.

### G2 — Connect one *real* Melodia signal [no duplicated bridge]

1. UE-side adapter reads the already-authored rhythm/presentation data; writes `BeatPhase`/`Amplitude` once, via TouchEngine's exposed inputs. Avoid raw second polling of music/FFT, new OSC listeners, or competing MPC writes.
2. Capture a predictable test pattern (0 → .5 → 1 phase, then actual gameplay beat) and a mute/zero-amplitude case.
3. Start/stop PIE repeatedly; test load failures, frame drops, alt-tab, lost TouchEngine process, and optional disabling without hanging the game. Confirm no change in actual beat grading.
4. **Exit:** real signal drives same `.tox` output while authoritative game systems remain unchanged, with explicit failure fallback. Record real hardware frame times (UE game/render thread, TouchEngine cook latency, frame drops, GPU memory); don't invent a performance pass.

### G3 — First meaningful consumer (only after G2)

Choose **one** user-visible material/Niagara/Monolith response, preferably the existing Faraway Mother `OUT_SHOW_FIELD` pattern. Reuse `Docs/Production/FARAWAY_MOTHER_P1_RESONANCE_FIELD_INTEGRATION_SPEC.md`: presentation RGBA semantics, fixed world UV bounds, and static Hython/PCG ground truth. **Do not rewrite that contract or claim its 128×128 field return is already proved.**

Port the validated small `.tox` component or author a separate isolated field `.tox`, preserving the same exact one-writer boundaries. One surface at a time; no general-purpose TouchEngine framework.

### G4 — Integration, packaging and promotion gate

- Build in a fresh editor session; reopen project; PIE restart ×3; source-controlled asset provenance and `.tox` relative-path resolution.
- Package to a scratch Windows build and test on the **intended deployment machine** with verified TouchEngine/TouchPlayer requirements, licensing, external installs and redistribution rules. A working editor ≠ a distributable game.
- Benchmark baseline **without** TouchEngine versus **with** one canary: FPS/frame times, GPU memory, latency, dropped frames, CPU, and loss-of-runtime behavior. Aim for stable 60 FPS where the project normally targets it, but use observed data rather than a fabricated pass.
- Land production enablement **only** when cold install, runtime fallback, gameplay non-regression, and deployment/licensing policy are resolved. Keep feature opt-in / separate if only editor/demo installs are viable.
- Write only verified gate/status changes to `CURRENT_STATE.md`. CI/static gates are not substitutes for actual UE PIE/packaging evidence.

## UE ↔ TD cross-repo handoff contract

TD author is responsible for supplying **one self-contained `.tox` per verified consumer** from `fromage3900/MelodiaTouchDesigner`: `melodia_te_canary_v1.tox` first. Deliver the real `.tox` path, its source TD commit SHA, TouchDesigner build, hash, parameter identifier/type/ranges, output OP names and formats, color-space/alpha policy, expected frame/cook behavior, and a TD-side test screenshot or recipe. Export a known diagnostic `OUT_BEAUTY` pattern that visibly changes for `BeatPhase` and `Amplitude`.

UE implementer owns **only** the plugin integration, adapter, ToxAsset reference, UE material consumer, fallback and PIE/package checks. Record UE commit SHA, TD commit SHA, imported ToxAsset identity, plugin/engine versions, and link to real evidence. Use existing Perforce/Git asset placement policies; never copy the entire `.toe` project into the UE repo or invent a mirrored TD runtime.

### Human / agent execution split

| UE owner/integrator | TouchDesigner owner |
|---|---|
| Build 5.8 compatibility lab; protect live project | Export self-contained v1 `.tox` with named parameters and TOP |
| Connect actor inputs to existing rhythm state | Confirm output names, color, dimensions and deterministic visual response |
| Validate UE texture, fallback, PIE and package | Verify `.tox` loads alone without grandmaster/OSC/file dependencies |
| Canonize evidence in `CURRENT_STATE.md` after actual proof | Supply TD commit/version/hash and one reference test |

**Do not touch the TD repo in this UE-side task.** The owner is assembling its implementation independently.

## Known upstream references / compatibility notes

- Official plugin: https://github.com/TouchDesigner/TouchEngine-UE
- Official sample (currently documents UE 5.7.x, TouchEngine-UE 1.7.0): https://github.com/TouchDesigner/TouchEngine-UE-Samples
- Plugin getting-started, actors/components/events/ToxAssets: https://github.com/TouchDesigner/TouchEngine-UE/blob/UE5.7-Release/docs/getting-started.md
- Existing Melodia contracts: `Docs/TouchDesigner/MELODIA_TD_AE_CROSS_REPO_CONTRACT_2026-09-08.md`, `Docs/Production/SIGNAL_VOCABULARY_2026-09-25.md`, `Docs/Production/FARAWAY_MOTHER_P1_RESONANCE_FIELD_INTEGRATION_SPEC.md`.

## Next art-facing TD consumer — Chord Atelier / Infinite Aeolian Atrium

**Owner-requested next authoring action (2026-10-11):** TD develops **one** reusable procedural `ChordAtelier` COMP using existing `geo_engines`, Blender GN Aeolian/chimes, Chladni/Hython field masks, native TD POP/CHOP and the Lookdev Studio. The implementation recipe and TD status are owned in `fromage3900/MelodiaTouchDesigner:docs/CHORD_ATELIER_AEOLIAN_ATRIUM.md` and `docs/CURRENT_PROJECT_STATE.md`. The game sources geometry and musical semantics from `chimes_gn.py`, `chladni_layers.py`, `Tools/chladni_sheets_to_textures.py`, `Tools/archipelago.py` and the harmonic-state subsystem.

**Keep the two tracks distinct:** first build an independent deterministic seeded single-chord TD COMP, then a four-chord Aeolian atrium replay with wind/cymatic fields, reset/fallback and a measured beauty capture. That may later yield a **small, standalone TouchEngine-friendly `.tox`**, but the full procedural TD engine and arbitrary POP mesh output must **not** be assumed importable into UE by TouchEngine. For UE consumers, stick to verified TOP/CHOP/custom input/output channels and the G0–G4 canary sequence above. TouchEngine port to UE 5.8 is **owner-in-progress; successful compilation, PIE, and packaging remain unverified.** No new OSC, world authority, MPC writer or replacement of the existing Spout pipeline. Do not treat the artistic source fixture (Cm→A♭→E♭→B♭) as a change to canonical music/gameplay state.
