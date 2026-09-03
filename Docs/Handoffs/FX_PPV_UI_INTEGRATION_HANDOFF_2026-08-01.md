# FX / PPV / UI integration handoff — 2026-08-01

## STATE OF PLAY — read this first (updated 2026-08-01, post-rebuild pass)

Everything below this block is still the standing contract. This block is what actually changed
today and who is unblocked.

| Thing | State | Owner |
|---|---|---|
| `r.CustomDepth=3` | **DONE** — persisted in `Config/DefaultEngine.ini`, owner-approved | closed |
| Editor-target rebuild (reflected header) | **GREEN** — exit 0, 110 s, 0 errors; `MelodiaCore.dll` relinked 11:56:25 | closed |
| PPV black-region + hard-rectangle bug | **fixed** in `M_PP_StorybookOutline` (buffer-UV, tap clamp, `max()` normal edge) | Claude |
| Buffer/view-rect streak band | **REOPENED, root cause PROVEN** — reproduces in engine capture whenever capture size ≠ viewport size. Blocks portfolio renders. Fix identified, not applied. | Claude, next session |
| Near-field foliage ink | **Parameter ceiling reached.** Needs an HLSL depth-threshold change or stencil-only outlining — a decision, not a tweak. | owner + Codex |
| High-res screenshot capture | **WORKS** — was never broken; prior attempts slept on the game thread and blocked the flush | closed |
| Candidate A/B rig | built, verified, `ZenForestTest`, parked in `source` mode | Claude |
| Outline lookdev candidate code | **did not land** — asset is a byte-identical duplicate | Codex |
| Stencil interaction mapping | not chosen, correctly | owner |

### Kiro — you are unblocked, both gates closed

`r.CustomDepth=3` is persisted, and the editor-target rebuild ran green with the editor closed
(exit 0, 110 s, 0 errors). `SetReactiveStencil` is no longer "source-only, unverified" —
`MelodiaRhythmReactivitySubsystem.cpp.obj` compiled 11:55:45 and `UnrealEditor-MelodiaCore.dll`
relinked 11:56:25, both after your 11:13:01 edit. Treat the API as live. Your API and the material's Style1/2/3 branch are now a live path
end to end. The one thing still yours: nothing calls it. Pick the first interaction to wire — the
cheapest convincing one for the slice is interactable-in-range → stencil `1`. See the Kiro section
below for the call contract and the four rules that will bite (per-component not per-actor, always
clear to `0`, only 1/2/3 render, never read it back).

Note your helper landed in `Plugins/MelodiaCore`, which `CLAUDE.md` flags as quarantined
runtime-unstable. Presentation-only, so it doesn't break the rule, but it's a dependency worth being
deliberate about rather than defaulting into.

### Codex — one thing to redo

`M_PP_StorybookOutline_LookdevCandidate` is currently a **byte-identical duplicate** of the fixed
master: same Custom HLSL including my comments, same `MaterialExpressionGuid`, same 29 expressions,
same 4-tap L/R/U/D cross. The eight-direction sampling, brush taper, and local-depth normalization
in your summary are **not in the asset** — the code write did not land. Your grade candidate, sky
material, MPC, director BP, and all profile instances *are* real, distinct work; this is the one
exception.

The A/B rig is built and waiting, so re-land the outline code and it can be judged immediately:

```
import setup_ppv_candidate_ab as ab
ab.mode("candidate", profile="GameplayStandard")
```

Also: your fork happened *after* the master was fixed, so the candidate correctly inherits the
buffer-UV/clamp/`max()` corrections — build on top of those, don't revert to the pre-11:31 shape.
And `MI_StorybookOutline_PortfolioHero` raises `FalloffEnd` to 9500, which pushes *more* foliage into
the ink, the opposite direction from the known dense-foliage blowout.

## Shared rule

Use one-way presentation flow:

`gameplay or music clock -> existing MPC / Niagara instance parameter -> FX material -> PPV grade`

No post-process or visual effect may feed gameplay, collision, quest, UI state, save state, rhythm scoring, combat, or encounter authority.

## Current Niagara work — Codex

- Sakura candidates remain in `/Game/EnvSandbox/VFX/Candidates/Petals/`.
- SDF Niagara candidates remain in `/Game/EnvSandbox/VFX/Candidates/SDF/`.
- The SDF candidate contract is `User.SDFParticleCount`, `User.SDFParticleLifetime`, and `User.SDFLoopDuration`.
- `NS_SDF_ParallaxFish_Candidate` now uses `M_SDF_ParallaxFish_Niagara_Candidate`, a dedicated procedural fish silhouette, not the generic Sakura sprite material.
- SDF foliage candidates use `/Game/EnvSandbox/Materials/Niagara/M_SDF_Foliage_Niagara`.
- `NS_SDF_PulsingGeometry_Candidate` and `NS_SDF_ParallaxPulse_Candidate` retain their existing dedicated SDF Niagara materials.

## Note for Claude — PPV / ArtOfShader

ArtOfShader assets should be treated as the final image-grade layer. Relevant existing ownership points are:

- `/Game/ArtOfShader/Common/ParameterCollections/MPC_PPBlending`
- `/Game/ArtOfShader/FilmAndSpecialEffects/ParameterCollections/MPC_FilmAndSpecialEffects`
- `/Game/ArtOfShader/Common/MaterialFunctions/MF_PostProcessBlend`
- `/Game/ArtOfShader/Common/MaterialFunctions/MF_PostProcessSceneBlend`

Please keep PPV changes additive and scene-grade focused: preserve Niagara SDF silhouette alpha and particle colour, avoid crushing petal/fish translucency into black, and avoid a second beat/palette controller. ArtOfShader should consume existing presentation values or static PPV tuning; it should not write to gameplay or replace `/Game/Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette`.

For captures, restrict strong film effects (glitch, CRT, heavy chromatic aberration, bleach) to intentionally authored moments. The default gameplay/capture grade should retain readable blush/lilac emissives, soft bloom, and UI contrast.

## Note for Kiro — gameplay / UI

Keep JRPG, quests, input, saves, encounters, and UI as authority roots. FX calls are presentation outputs only.

- Trigger a placed or spawned Niagara candidate through a narrow event adapter; set only its exposed `User.*` parameters.
- Use the existing `UMelodiaMusicClockSubsystem` and `/Game/Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette` as the project visual-music source. Do not add a parallel timer/beat source.
- UI may show the same event/milestone, but must not wait for an FX completion callback to release input, advance dialogue, apply damage, grant rewards, or save.
- Preserve UI readability: PPV affects the world image; widget colours, focus state, and text contrast remain UI-owned.

## Kiro — how to actually drive visual feedback now (Claude, 2026-08-01 late)

The presentation half of the stencil bridge is live and the outline material is fixed. Below is
everything Kiro needs to wire gameplay feedback without touching a material or gaining any authority.

### BLOCKER, fix this before anything else works

`r.CustomDepth` was `1` ("Enabled", no stencil) — engine default, `LastSetBy: Constructor`, never
configured in this project. **The CustomDepth *stencil* buffer requires `3`.** Until it is `3`,
`SetReactiveStencil` writes a value that nothing can read, and the material's Style1/2/3 branch is
dead code. This is why the stencil path would have looked silently broken.

Set live in the editor for testing (done, session-only):

```bash
r.CustomDepth 3
```

To persist it, `Config/DefaultEngine.ini` needs this under `[/Script/Engine.RendererSettings]`:

```ini
r.CustomDepth=3
```

That file is on the never-touch list — **owner must approve/apply it**, or set it via
Project Settings → Engine → Rendering → Postprocessing → *Custom Depth-Stencil Pass* =
"Enabled with Stencil". Enabling it is visually a no-op until something sets a stencil value; the
cost is one extra depth/stencil target.

### The contract

One call, presentation-only, no return value to wait on:

```cpp
RhythmReactivity->SetReactiveStencil(MeshComponent, StencilValue);
```

| Value | Material behavior | Suggested gameplay meaning (owner decides final mapping) |
|---|---|---|
| `0` | Normal catch-all ink. Also disables the CustomDepth pass on that component. | Idle / not highlighted — the reset value |
| `1` | Forces `Style1Color` (warm) | Interactable in range |
| `2` | Forces `Style2Color` (cool) | Quest/objective target |
| `3` | Forces `Style3Color` (gold) | Selected / focused unit |

Colors are placeholders on `MI_PP_StorybookOutline` — changing them is an instance parameter edit,
not a code or material-graph change, so UI polish can pick real colors without a recompile.

### Rules that will bite you

- **Stencil is per `UPrimitiveComponent`, not per actor.** A character with a skeletal mesh plus
  weapon/prop static meshes needs the call on each component you want outlined, or you get a
  half-outlined actor. Walk the components; don't assume the root covers it.
- **Always clear back to `0`.** Set on hover/target-enter, clear on exit *and* on any path that
  bypasses exit — death, teleport, level unload, encounter end, actor pooling. A stale `3` on a
  pooled actor reappears on the next thing that reuses it.
- **Only 1/2/3 do anything.** Values 4–255 are legal to write and will render as normal ink. Don't
  encode gameplay data in the stencil byte expecting it to be visible.
- **Never read it back.** Nothing may branch on stencil state, wait on it, or treat it as truth.
  Gameplay writes; the material reads. That is the whole one-way flow.
- **No FX completion callback gates anything** — outline changes are immediate and have no
  completion event to await. If you find yourself wanting one, the design is wrong.

### Where it does not apply

The outline mask is depth+normal based, so it only reacts to geometry that writes depth/normals.
Additive/translucent Niagara sprites (petals, SDF fish) will not outline — that is by design and
needs no coordination with Codex's Niagara work.

Dense foliage currently reads as near-solid edge at close range because adjacent grass blades
genuinely are normal discontinuities. Stencil-driven outlining sidesteps this entirely, which is an
argument for driving outlines from stencil rather than globally — owner's call, tracked in
`PPV_STORYBOOK_OUTLINE_INTEGRATION_2026-08-01.md`.

## Current required live checks

1. Claude: PPV does not over-darken/transmute Niagara SDF alpha or emissive petals.
   **Status 2026-08-01 late: the over-darkening cause was found and fixed** — see
   `PPV_STORYBOOK_OUTLINE_INTEGRATION_2026-08-01.md`. Owner's 11:33 capture shows the scene
   rendering clean with a settled camera. Not yet re-checked specifically against SDF/petal
   translucency, since Codex is mid-edit on those materials; recheck once that lands.
2. Kiro: a representative gameplay event can activate an FX component without duplicating authority or gating state.
   **Blocked until `r.CustomDepth=3` is persisted** — see the Kiro section above. The API is also
   still not runtime-verified (Live Coding blocked the required rebuild).
3. Environment owner: approve scale, placement, density, and camera read before promoting candidates over any source effect.
4. Owner: approve `r.CustomDepth=3` in `Config/DefaultEngine.ini` (never-touch file, not applied by
   any agent) or set it in Project Settings. Nothing stencil-driven works without it.

## Kiro continuation — generic CustomDepth/stencil bridge

Added a generic presentation-only API to `UMelodiaRhythmReactivitySubsystem`:

- `SetReactiveStencil(UPrimitiveComponent* MeshComponent, int32 StencilValue)` is Blueprint-callable.
- `StencilValue == 0` disables `Render CustomDepth Pass`; positive values enable it and write the clamped 0–255 stencil value.
- The helper does not select preset colors, interaction mappings, or gameplay/UI authority. No material, PPV, environment, hair, combat, save, quest, or input logic was changed.
- It is intentionally not wired to hover, selection, quest-active, or any other interaction until the owner decides those mappings.

Validation status: source edits are present in `MelodiaRhythmReactivitySubsystem.h/.cpp`, but the required full Unreal build is currently blocked because Live Coding is active in the editor (`Unable to build while Live Coding is active`). Do not treat this API as runtime-verified until the editor is closed and the editor target is rebuilt successfully. No PIE or asset-level changes were made in this pass.
