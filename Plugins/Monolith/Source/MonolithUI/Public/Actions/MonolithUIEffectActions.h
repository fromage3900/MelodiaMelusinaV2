// Copyright tumourlove. All Rights Reserved.
// MonolithUIEffectActions.h
//
// Phase F (2026-04-26) -- MCP action wrappers for the UEffectSurface widget
// cluster shipped in Phase E. Each `set_effect_surface_<bag>` action targets
// one sub-bag of FEffectSurfaceConfig (Shape / Fill / Border / DropShadow /
// InnerShadow / Glow / Filter / BackdropBlur / InsetHighlight) and writes the
// fields through the existing FUIReflectionHelper allowlist gate, then flips
// the matching EEffectSurfaceFeature bit in FeatureFlags so the shader
// permutation key stays in sync with the live data.
//
// The 10th action `apply_effect_surface_preset` batches a curated config
// initialiser onto the widget (rounded-rect / pill / circle / glass /
// glowing-button / neon) -- preset names are OURS, not derived from any
// third-party library.
//
// Composition rule (Phase E coordination contract): the handlers DO NOT
// reach into UEffectSurface's typed C++ setters. They go through the JSON
// path surface (Effect.Shape.CornerRadii, etc.) the registry curated in
// Phase E. That keeps:
//   - the allowlist gate as the single source of truth for what's writable;
//   - the property-path cache hot for both the action surface AND the spec
//     builder pipeline (Phase H reuses the same path strings);
//   - downstream Python emitters (which consume these actions over MCP)
//     loosely coupled to UEffectSurface's compile-time API surface.
//
// FeatureFlags bookkeeping: each sub-bag setter ORs the corresponding bit
// into Effect.FeatureFlags so material static-permutation keys stay correct.
// Callers are NOT expected to manage the bitmask manually.
//
// MID refresh: a sub-bag setter does NOT push parameters synchronously --
// the next paint pass (or the next ForceMIDRefresh) handles that. The
// `apply_effect_surface_preset` action DOES call ForceMIDRefresh once at
// the end so the live preview snaps to the new look without waiting on a
// paint pass.
//
// Editor-only -- UWidgetBlueprint::WidgetTree is WITH_EDITORONLY_DATA, and
// the type registry / allowlist live in an editor subsystem.

#pragma once

#include "CoreMinimal.h"
#include "MonolithToolRegistry.h"

namespace MonolithUI
{
    struct FEffectSurfaceActions
    {
        /** Register all 10 actions in the `ui::` namespace. */
        static void Register(FMonolithToolRegistry& Registry);

        // Individual handlers exposed for direct test invocation.
        static FMonolithActionResult HandleSetCorners       (const TSharedPtr<FJsonObject>& Params);
        static FMonolithActionResult HandleSetFill          (const TSharedPtr<FJsonObject>& Params);
        static FMonolithActionResult HandleSetBorder        (const TSharedPtr<FJsonObject>& Params);
        static FMonolithActionResult HandleSetDropShadow    (const TSharedPtr<FJsonObject>& Params);
        static FMonolithActionResult HandleSetInnerShadow   (const TSharedPtr<FJsonObject>& Params);
        static FMonolithActionResult HandleSetGlow          (const TSharedPtr<FJsonObject>& Params);
        static FMonolithActionResult HandleSetFilter        (const TSharedPtr<FJsonObject>& Params);
        static FMonolithActionResult HandleSetBackdropBlur  (const TSharedPtr<FJsonObject>& Params);
        static FMonolithActionResult HandleSetInsetHighlight(const TSharedPtr<FJsonObject>& Params);
        static FMonolithActionResult HandleApplyPreset      (const TSharedPtr<FJsonObject>& Params);
    };
}
