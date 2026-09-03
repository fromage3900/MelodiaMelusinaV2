// Copyright tumourlove. All Rights Reserved.
// UIAnimationMovieSceneBuilder.h
//
// Phase I — editor MovieScene backend for `FUISpecAnimation`.
//
// `Build` walks the `FUISpecDocument::Animations` list and reconciles each
// entry against the WBP's `UWidgetAnimation` collection. Reuses the
// per-animation helpers exposed by `Actions/Hoisted/AnimationCoreActions.h`
// (find-or-create animation, ensure-binding, ensure-track-section, insert-key)
// so the editor MovieScene logic has exactly one implementation.
//
// Threading: editor-only, main-thread (matches the helpers, which call
// `FKismetEditorUtilities::CompileBlueprint`). Compile-time-gated by
// `WITH_EDITORONLY_DATA`; the Build call is a no-op on a runtime build.

#pragma once

#include "CoreMinimal.h"
#include "Animation/UISpecAnimation.h"

class UWidgetBlueprint;
struct FUISpecDocument;
struct FUISpecAnimation;

/**
 * Stateless editor-side builder. Static methods only; per-pass scratch lives
 * on the stack so concurrent calls on different WBPs are safe in principle
 * (but `FKismetEditorUtilities::CompileBlueprint` is main-thread, so callers
 * still serialise).
 */
class MONOLITHUI_API FUIAnimationMovieSceneBuilder
{
public:
    /**
     * Reconcile every `FUISpecAnimation` in `Document.Animations` against the
     * Widget Blueprint's `UWidgetAnimation` collection.
     *
     * @param Document     Parsed spec document. Animations are read; Root /
     *                     Styles / Metadata are not touched.
     * @param TargetWBP    Target Widget Blueprint. Must be valid; must have a
     *                     non-null `WidgetTree`.
     * @param Options      Build-time controls — preserve list, compile toggle,
     *                     dry-run flag.
     * @return Counters + warnings + bSuccess for the pass.
     */
    static FUIAnimationRebuildResult Build(
        const FUISpecDocument& Document,
        UWidgetBlueprint* TargetWBP,
        const FUIAnimationBuildOptions& Options);

    /**
     * Build a single animation entry. Public so callers (e.g. action handlers)
     * can drive a 1-spec build without constructing a whole `FUISpecDocument`.
     *
     * `OutResult` is accumulated into — counters add to whatever values it
     * carries on entry. Warnings append.
     */
    static void BuildSingle(
        const FUISpecAnimation& Animation,
        UWidgetBlueprint* TargetWBP,
        const FUIAnimationBuildOptions& Options,
        FUIAnimationRebuildResult& OutResult);
};
