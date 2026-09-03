# Rider 2026.2 workflows for Sea Above P0 closeout

**Purpose:** use only Rider workflows that directly shorten a remaining P0 proof. Rider is the C++
and inspection surface; Unreal remains the asset, PIE and runtime authority.

## Priority workflows

1. **Blueprint + GameplayTag Code Vision:** Find Usages from the Sea Above travel, flag, reward,
   intent and challenge tags into Blueprint assets. Use this to locate the live host and payoff;
   never infer absence from a text dump.
2. **RiderLink test sessions:** run `Melodia.SeaAbove.*`, `Melodia.Wardrobe.*` and integration tests
   against the single running editor. Keep commandlet runs for isolated product tests.
3. **Native debugger:** conditional breakpoints in Sea Above travel dispatch,
   `UMelodiaPCGNarrativeChallengeBridgeComponent::HandlePatternCompleted`, narrative commit and
   replay-no-op paths. Use Natvis and detach without terminating the editor.
4. **Shader source ownership:** validate `.ush` syntax and `/Melodia` includes in Rider; prove the
   runtime result through UE shader compilation and a visible capture. Do not duplicate HLSL in
   Python or inline Custom nodes.
5. **Qodana shipping scan:** analyze `BS_GodFile`, `MelodiaCore`, `MelodiaWardrobe` and
   `MelodiaShader`; exclude generated and vendor code. Empirically validate the local `QDJB`
   invocation against JetBrains' documented Unreal `QDNET` mode before changing the canonical
   command.
6. **Build + trace:** use `Development Editor | Win64` with Unreal closed for reflected/module/API
   changes. Capture existing `TRACE_CPUPROFILER_EVENT_SCOPE` sites in Unreal Insights for pulse,
   music commit and travel.

## Adoption test

A workflow enters the canonical Rider runbook only when it produces project evidence: the exact
Rider action, UE-side counterpart, output/log, failure mode and time saved. Marketing-only or
Unity-only features stay out.

## Tonight's proof order

Build/Qodana -> one editor -> Sea Above travel -> pulse/droplets -> real music phrase -> typed
idempotent result -> visible route -> wardrobe save/restart and Glide -> rhythm gates -> static
gates -> Development package -> packaged golden run -> itch upload.

