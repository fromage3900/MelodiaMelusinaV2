// Copyright tumourlove. All Rights Reserved.
// EffectSurfaceBuilder.h
//
// Phase H — sub-builder for the UEffectSurface widget. Translates the
// FUISpecEffect sub-bag into the curated `Effect.*` JSON paths the Phase E
// allowlist accepts, and writes them through `FUIReflectionHelper`. The
// FeatureFlags bookkeeping that the Phase F action wrappers do is replicated
// here (skip-bit-flip-on-zero invariant carried over) so the spec-builder
// path produces the same shader-permutation key as the per-MCP-call path.

#pragma once

#include "CoreMinimal.h"

class UWidget;
struct FUIBuildContext;
struct FUISpecNode;

namespace MonolithUI::EffectSurfaceBuilder
{
    /** Apply FUISpecEffect sub-bag onto an already-constructed UEffectSurface. */
    bool ApplyEffect(
        FUIBuildContext& Context,
        const FUISpecNode& Node,
        UWidget* Widget);
}
