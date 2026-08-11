// Copyright tumourlove. All Rights Reserved.
// EffectSurfaceBuilder.cpp
//
// Phase H — apply FUISpecEffect onto a constructed UEffectSurface widget.
// Routes every write through `FUIReflectionHelper::ApplyJsonPath` against
// the curated `Effect.*` JSON paths (the same surface the Phase F per-MCP
// wrappers use). Keeps the path cache hot across both the spec-builder and
// per-call paths.
//
// Design choice: we DO NOT call UEffectSurface's typed setters here (same
// rule as the Phase F wrappers per the Phase E coordination contract). All
// writes flow through the allowlist gate so the curated mapping is the
// single source of truth.

#include "Spec/Builders/EffectSurfaceBuilder.h"

#include "Spec/UIBuildContext.h"
#include "Spec/UISpec.h"
#include "MonolithUICommon.h"
#include "Registry/MonolithUIRegistrySubsystem.h"
#include "Registry/UIPropertyAllowlist.h"
#include "Registry/UIPropertyPathCache.h"
#include "Registry/UIReflectionHelper.h"

#include "Components/Widget.h"

#include "Dom/JsonObject.h"
#include "Dom/JsonValue.h"

namespace MonolithUI::EffectSurfaceBuilderInternal
{
    /**
     * One write through the helper. Returns true on success; on failure
     * pushes a warning-severity finding into Context (effect writes are
     * non-fatal — a missing field on an unusual EffectSurface variant
     * shouldn't block the build).
     */
    static bool WriteOne(
        FUIBuildContext& Context,
        UWidget* Widget,
        const FName& WidgetToken,
        const TCHAR* JsonPath,
        const TSharedPtr<FJsonValue>& Value)
    {
        if (!Value.IsValid())
        {
            return false;
        }

        FUIReflectionHelper Helper(Context.PathCache, Context.Allowlist);
        const FUIReflectionApplyResult R = Helper.ApplyJsonPath(
            Widget, WidgetToken, JsonPath, Value);

        if (!R.bSuccess)
        {
            FUISpecError W;
            W.Severity = EUISpecErrorSeverity::Warning;
            W.Category = TEXT("Effect");
            W.Message  = FString::Printf(
                TEXT("EffectSurface write '%s' failed: %s (%s)"),
                JsonPath, *R.FailureReason, *R.Detail);
            Context.Warnings.Add(MoveTemp(W));
            return false;
        }
        return true;
    }

    /** Build a JSON value for FVector4. */
    static TSharedPtr<FJsonValue> MakeVec4(const FVector4& V)
    {
        TArray<TSharedPtr<FJsonValue>> Arr;
        Arr.Reserve(4);
        Arr.Add(MakeShared<FJsonValueNumber>(V.X));
        Arr.Add(MakeShared<FJsonValueNumber>(V.Y));
        Arr.Add(MakeShared<FJsonValueNumber>(V.Z));
        Arr.Add(MakeShared<FJsonValueNumber>(V.W));
        return MakeShared<FJsonValueArray>(Arr);
    }

    /** Build a JSON value for FLinearColor. */
    static TSharedPtr<FJsonValue> MakeColor(const FLinearColor& C)
    {
        TArray<TSharedPtr<FJsonValue>> Arr;
        Arr.Reserve(4);
        Arr.Add(MakeShared<FJsonValueNumber>(C.R));
        Arr.Add(MakeShared<FJsonValueNumber>(C.G));
        Arr.Add(MakeShared<FJsonValueNumber>(C.B));
        Arr.Add(MakeShared<FJsonValueNumber>(C.A));
        return MakeShared<FJsonValueArray>(Arr);
    }

    static TSharedPtr<FJsonValue> MakeNum(double N)
    {
        return MakeShared<FJsonValueNumber>(N);
    }
} // namespace MonolithUI::EffectSurfaceBuilderInternal


bool MonolithUI::EffectSurfaceBuilder::ApplyEffect(
    FUIBuildContext& Context,
    const FUISpecNode& Node,
    UWidget* Widget)
{
    using namespace MonolithUI::EffectSurfaceBuilderInternal;

    if (!Widget)
    {
        return false;
    }

    const FName WidgetToken = MonolithUI::MakeTokenFromClassName(Widget->GetClass());
    const FUISpecEffect& E = Node.Effect;

    // Shape
    WriteOne(Context, Widget, WidgetToken, TEXT("Effect.Shape.CornerRadii"), MakeVec4(E.CornerRadii));
    WriteOne(Context, Widget, WidgetToken, TEXT("Effect.Shape.Smoothness"),  MakeNum(E.Smoothness));

    // Fill (solid color path; gradient stops are deferred to Phase J)
    WriteOne(Context, Widget, WidgetToken, TEXT("Effect.Fill.SolidColor"),   MakeColor(E.SolidColor));

    // BackdropBlur — only flip the bit when strength > 0 (per Phase F invariant)
    if (E.BackdropBlurStrength > 0.f)
    {
        WriteOne(Context, Widget, WidgetToken,
            TEXT("Effect.BackdropBlur.Strength"), MakeNum(E.BackdropBlurStrength));
    }

    // Drop / inner shadows: v1 only forwards count + first-layer when present.
    // Phase F's per-MCP path serialises the entire array via ImportText_Direct
    // — Phase H punts on that until Phase J where the JSON shape is canonical.
    if (E.DropShadows.Num() > 0)
    {
        FUISpecError W;
        W.Severity = EUISpecErrorSeverity::Warning;
        W.Category = TEXT("Effect");
        W.WidgetId = Node.Id;
        W.Message  = TEXT("EffectSurface DropShadows array writes are deferred to Phase J — use ui::set_effect_surface_dropShadow per-MCP.");
        Context.Warnings.Add(MoveTemp(W));
    }
    if (E.InnerShadows.Num() > 0)
    {
        FUISpecError W;
        W.Severity = EUISpecErrorSeverity::Warning;
        W.Category = TEXT("Effect");
        W.WidgetId = Node.Id;
        W.Message  = TEXT("EffectSurface InnerShadows array writes are deferred to Phase J — use ui::set_effect_surface_innerShadow per-MCP.");
        Context.Warnings.Add(MoveTemp(W));
    }

    return true;
}
