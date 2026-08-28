---
name: melodia-shader-rider
description: Use when editing UE 5.8 shader source (.usf/.ush) in JetBrains Rider for Melodia.
---

# Melodia shader authoring in Rider

Operational runbook for shader source work in JetBrains Rider on `BS_GodFile`. Shader work is
editor-free until a material instance / material function / Niagara system needs to consume the
compiled shader; this skill covers the Rider-side authoring, inspection, and quality gates.

## 0. Scope guard

- **Do not hand-edit `.uasset`.** Shader source (`.usf`, `.ush`) is plain text and safe to edit in
  Rider. Compiled material assets are not.
- **One editor, one MCP surface.** `Get-Process UnrealEditor` single instance; one listener on
  9316. Never two graph-mutation MCP servers on the same graph.
- **Shader source is offline-friendly.** You can author/edit `.usf`/`.ush` in Rider without the editor
  running. Only material functions/instances/Niagara that consume the shader need the editor.
- **Do not invent shader authority.** If a shader drives gameplay, route it through the existing
  presentation/reactivity seams; do not build a new gameplay system out of shader code.

## 1. Rider shader authoring (what you get)

From `AGENTS.md` §2.1:

- Edit `.usf` and `.ush` shaders directly in Rider with full syntax validation, macro expansion, and
  semantic highlighting.
- Rider parses `.uasset` binary files in the background; Code Vision lenses above `UCLASS`,
  `UFUNCTION`, and `UPROPERTY` show derived Blueprint counts, asset usages, and overridden CDO
  property values without starting the editor.
- Rider's Unreal IWYU inspection to strip unneeded `#include` directives and prevent unity-build
  symbol pollution (relevant to AGENTS.md #21 — adaptive unity hides "unbuildable from clean").

## 2. What to author in Rider (offline)

- New `.usf`/`.ush` files for custom material functions, procedural effects, or Niagara shader tasks.
- Edits to existing shader includes/sources under the project's shader paths.
- IWYU-driven `#include` cleanup on shader sources.
- Static analysis via `qodana.yaml` with the `QDJB` profile before the shader reaches review
  (catches memory leaks, missing reflection tags, uninitialized properties where applicable).

## 3. What needs the editor (Junie's lane)

- Material functions that wrap the new shader (Material Editor).
- Material instances that override the shader's parameters.
- Niagara systems/VFX that consume the shader.
- Bloom/compile + fingerprint + promote through the T3D pipeline when the shader is part of a
  versioned content family.

## 4. Verification (before an editor session)

- IWYU clean — no unused `#include` directives on the shader sources you touched.
- `qodana.yaml` `QDJB` profile passes for the C++ side if you touched any C++ that consumes the
  shader (no memory leaks, reflection tags present, properties initialized).
- If the shader is part of a T3D-injectable family, the spec is ready before the editor opens.

## 5. Evidence standard

- A shader edit is "done" when it is authored, IWYU-clean, and qodana-clean on the source side, and
  (if part of content) the material/Niagara side is compiled and fingerprinted through the T3D
  pipeline.
- Screenshots without assertion reports are not evidence. A live PIE capture plus the before/after
  material state reads next to it is the only valid runtime evidence.

## 6. When to use

- Editing/adding `.usf`/`.ush` shader source in Rider.
- Cleaning up `#include` directives on shader sources.
- Preparing shader source for a new outfit, new VFX, or new material function before the editor opens.
- Reviewing shader source changes before they reach the editor lane.

## 7. When NOT to use

- Building material functions/instances/Niagara systems (editor-only).
- Editing `.uasset` files directly.
- Touching gameplay logic from shader code.
