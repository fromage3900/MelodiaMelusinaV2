// Copyright tumourlove. All Rights Reserved.
#pragma once

#include "CoreMinimal.h"
#include "MonolithToolRegistry.h"
// Phase I: TRange<FFrameNumber> + FFrameRate + FGuid appear in helper signatures
// below as return-by-value or const-ref-template-instantiation. Forward-decls
// are insufficient for those cases — include the small POD headers directly.
#include "Misc/FrameRate.h"
#include "Math/Range.h"
#include "Misc/Guid.h"

class UMovieScene;
class UWidgetAnimation;
class UWidgetBlueprint;
class UWidget;
struct FMovieSceneFloatChannel;

/**
 * MonolithUI -- UMG widget animation authoring (multi-track, weighted-tangent, spring-bake).
 *
 * create_animation_v2:        Creates a UWidgetAnimation on a WBP with multi-track,
 *                             multi-key cubic / linear / constant keyframe data.
 *                             Cubic supports tangent weight for CSS-style bezier easing.
 * add_bezier_eased_segment:   Convenience wrapper that converts a cubic-bezier(x1,y1,x2,y2)
 *                             control-point pair into UE weighted tangents and inserts the
 *                             resulting 2-key segment into an existing or new animation.
 * bake_spring_animation:      Bakes a damped harmonic spring into dense linear keyframes
 *                             (semi-implicit Euler with convergence early-out).
 *
 * Editor-only -- UWidgetBlueprint::Animations is WITH_EDITORONLY_DATA.
 *
 * Phase I exposure: the helper namespace `MonolithUI::AnimationInternal` (defined in the
 * .cpp) is mirrored here as a thin public-to-MonolithUI surface so the new
 * `FUIAnimationMovieSceneBuilder` (Public/Animation/) can call it without duplicating
 * the CSS-bezier-to-weighted-tangent math, the possessable-binding plumbing, or the
 * track/section/channel ensure routine. The action handlers continue to use the
 * same helpers via the .cpp-internal namespace; the public mirror simply forwards.
 */
namespace MonolithUI
{
    struct FAnimationCoreActions
    {
        static void Register(FMonolithToolRegistry& Registry);

        static FMonolithActionResult HandleCreateAnimationV2(const TSharedPtr<FJsonObject>& Params);
        static FMonolithActionResult HandleAddBezierEasedSegment(const TSharedPtr<FJsonObject>& Params);
        static FMonolithActionResult HandleBakeSpringAnimation(const TSharedPtr<FJsonObject>& Params);
    };

    /**
     * One UMG-keyframe descriptor — neutral to the original-action JSON shape so
     * builders can populate it from an `FUISpecKeyframe` directly.
     *
     * Mirrors `MonolithUI::AnimationInternal::FParsedKey` (.cpp) field-for-field.
     * Kept in the public header so the MovieScene builder can build one without
     * including the .cpp's anonymous helpers.
     */
    struct MONOLITHUI_API FAnimationCoreKey
    {
        double Time = 0.0;
        float Value = 0.0f;
        /** "cubic" / "linear" / "constant". */
        FString Interp = TEXT("cubic");
        float ArriveTangent = 0.0f;
        float LeaveTangent = 0.0f;
        float ArriveTangentWeight = 0.0f;
        float LeaveTangentWeight = 0.0f;
        bool bHasWeights = false;
    };

    /**
     * CSS cubic-bezier-to-weighted-tangent conversion.
     *
     * Given a CSS-style `cubic-bezier(x1, y1, x2, y2)` control-point pair, plus a
     * value-delta (ToValue - FromValue) and segment duration, fill OutKey0 (segment
     * start) and OutKey1 (segment end) with the leave/arrive tangent + tangent-weight
     * pair UE 5.7's weighted-tangent channel API consumes.
     *
     * Math is OUR derivation from the CSS easing spec and UE's `FMovieSceneTangentData`
     * shape: leave-tangent slope from the (x1,y1) handle, leave-weight = handle length / 3
     * (cubic bezier's natural normalisation), and the symmetric pair from (1-x2, 1-y2)
     * for the arrival side. See `Plugins/Monolith/Source/MonolithUI/Private/Actions/Hoisted/AnimationCoreActions.cpp`
     * (the original action handler still calls this — Phase I lifted it from the action body).
     *
     * Both keys are returned with `Interp = "cubic"` and `bHasWeights = true`.
     */
    MONOLITHUI_API void ComputeBezierWeightedTangents(
        double X1, double Y1, double X2, double Y2,
        double FromValue, double ToValue,
        double StartTime, double EndTime,
        FAnimationCoreKey& OutKey0,
        FAnimationCoreKey& OutKey1);

    /**
     * Find an existing UWidgetAnimation by display label, or create+register a new one
     * (including the deterministic-GUID entry the WBP compiler validates against).
     * Returns nullptr on a non-editor build.
     */
    MONOLITHUI_API UWidgetAnimation* FindOrCreateWidgetAnimation(
        UWidgetBlueprint* WBP,
        const FString& AnimationName);

    /**
     * Ensure a possessable binding exists for the given widget on the supplied
     * UWidgetAnimation/MovieScene. Returns the binding GUID. Idempotent.
     */
    MONOLITHUI_API FGuid EnsureWidgetPossessableBinding(
        UWidgetAnimation* WidgetAnim,
        UMovieScene* Scene,
        const FString& WidgetName,
        bool bIsRootWidget);

    /**
     * Find or create a float track + its first section for `PropertyName` on the
     * possessable identified by `PossessableGuid`. Returns the section's float
     * channel ready for key insertion. Re-uses the existing section if present
     * (keys are reset for idempotent re-build).
     */
    MONOLITHUI_API FMovieSceneFloatChannel* EnsureFloatTrackSectionChannel(
        UMovieScene* Scene,
        const FGuid& PossessableGuid,
        const FString& PropertyName,
        const TRange<FFrameNumber>& SectionRange);

    /** Insert a single key into a float channel. */
    MONOLITHUI_API void InsertFloatChannelKey(
        FMovieSceneFloatChannel* Channel,
        const FFrameRate& TickRes,
        const FAnimationCoreKey& Key);
}
