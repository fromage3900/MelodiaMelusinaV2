// MelodiaShader — custom shader source for the PPV ink, Nikki aesthetic, and bioluminescence systems.
//
// This module exists so JetBrains Rider can index, validate, and semantically highlight
// the project's custom HLSL (.usf/.ush) shader source as a first-class shader IDE
// (AGENTS.md §2.1: "Shader Authoring: Edit .usf and .ush shaders directly in Rider
// with full syntax validation, macro expansion, and semantic highlighting").
//
// The shader source here is OFFLINE-FRIENDLY: it can be authored and reviewed in Rider
// without the editor running. The editor is only needed when a Material Function or
// Material Instance that consumes this shader is compiled, fingerprinted, or promoted
// through the T3D pipeline.
//
// What lives here:
//   Shaders/
//     MelodiaInkCommon.ush       — shared types, constants, and helpers for all ink shaders
//     MelodiaInkHalftone.ush     — the existing Ben-Day halftone (ported from the Custom node HLSL)
//     MelodiaInkSdfNotation.ush  — SDF music-notation patterns (staff lines, note-heads, crescendo swells)
//     MelodiaInkPatternRouter.ush — interchanging pattern router driven by musical state
//     MelodiaInkBioluminescent.ush — bioluminescent decay bridge (shared I(t) = I₀·e^(-λ·dt) with water)
//     MelodiaNikkiCommon.ush     — shared Nikki aesthetic helpers (SDF ribbon, pearl sheen, glitter)
//     MelodiaBiolumCommon.ush   — shared bioluminescence decay + contact impulse helpers
//
// How these are consumed:
//   The Custom HLSL node in M_PP_MelodiaInk and the Nikki MF_* material functions
//   currently embed their HLSL as inline strings in Python build scripts
//   (Content/Python/build_dreamprint_material.py, expand_nikki_features.py).
//   This module makes that HLSL a proper shader source file that Rider can validate,
//   and that the build scripts can #include or copy into the Custom node at build time.
//
// Build.cs dependencies:
//   "RenderCore", "RHI", "Engine" — the minimal set for a shader module.
//   No Runtime/Editor split needed: the shader source is compiled by UE's shader
//   compiler, not by UBT as C++. The .build.cs just tells UBT where the shader
//   directory is so the shader compiler can find it.

using UnrealBuildTool;

public class MelodiaShader : ModuleRules
{
    public MelodiaShader(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;

        PublicDependencyModuleNames.AddRange(new string[]
        {
            "Core",
            "CoreUObject",
            "Engine",
            "RenderCore",
            "RHI",
        });

        // Register the shader directory so UE's shader compiler and Rider both find it.
        // This is the path Rider maps as a shader source root for syntax validation.
        PrivateIncludePaths.Add(System.IO.Path.Combine(ModuleDirectory, "Shaders"));
    }
}
