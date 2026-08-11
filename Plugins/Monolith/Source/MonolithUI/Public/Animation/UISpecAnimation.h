// Copyright tumourlove. All Rights Reserved.
// UISpecAnimation.h
//
// Phase I — animation-side surface of the FUISpecDocument.
//
// `FUISpecAnimation` and `FUISpecKeyframe` themselves live in `Spec/UISpec.h`
// (Phase A landed them as part of the document tree). This header re-exports
// them via `#include` so the new MovieScene builder + runtime driver can pull
// a single self-documenting include, and adds two Phase-I-only helper types:
//
//   - `FUIAnimationBuildOptions` — controls for the editor MovieScene builder
//     (preserve list, compile-once toggle, dry-run flag).
//   - `FUIAnimationRebuildResult` — populated by the builder so callers can
//     surface counts (animations created/skipped/preserved) without having to
//     re-walk the document.
//
// Why split these out from `Spec/UISpec.h`: build options and result-bag
// structs are a property of the *builder*, not of the document. The document
// describes intent ("here is what should exist"); the build options describe
// process ("how should the builder reconcile what exists today with that
// intent"). Keeping them in their own header lets the MovieScene builder and
// the future `build_ui_from_spec` action share an opt-set without forcing
// callers who only want to *parse* a spec document to drag in builder types.

#pragma once

#include "CoreMinimal.h"
#include "Spec/UISpec.h"
#include "UISpecAnimation.generated.h"

/**
 * Reconciliation policy applied when an animation with the same `Name` already
 * exists on the target Widget Blueprint.
 *
 * `Recreate` is the default — full destroy + rebuild. This is the historical
 * `create_animation_v2` behaviour and matches how reference UMG-spec generators
 * typically behave (lossy regen). Listed `PreservedNames` opt OUT of recreate
 * — those animations are left untouched on the WBP regardless of what the
 * spec says, mirroring CSS's `transition: none` for layout-flicker scenarios.
 *
 * `MergeAdditive` (reserved, not yet implemented) is the future-facing slot
 * for incremental layering. v1 ignores it.
 */
UENUM(BlueprintType)
enum class EUIAnimationRebuildPolicy : uint8
{
    /** Default: any animation named in the spec replaces the existing one. */
    Recreate            UMETA(DisplayName = "Recreate"),

    /** Reserved for v2 — additive merge. v1 treats this as Recreate. */
    MergeAdditive       UMETA(DisplayName = "Merge Additive"),
};

/**
 * Build-option bag for `FUIAnimationMovieSceneBuilder::Build`.
 *
 * Defaults reproduce the historical v1 / `create_animation_v2` behaviour:
 * recreate everything named in the spec, compile after the pass, no dry-run,
 * empty preserve list.
 */
USTRUCT(BlueprintType)
struct MONOLITHUI_API FUIAnimationBuildOptions
{
    GENERATED_BODY()

    /** Reconciliation policy. */
    UPROPERTY(BlueprintReadWrite, Category = "MonolithUI|Animation")
    EUIAnimationRebuildPolicy Policy = EUIAnimationRebuildPolicy::Recreate;

    /**
     * Animation names that MUST NOT be touched on rebuild — even if the spec
     * also defines them. This is the explicit opt-in surface for incremental
     * authoring (the user has hand-tuned `MyHero` in the WBP and a regenerate
     * pass should not blow it away).
     *
     * Names match against `UWidgetAnimation::GetDisplayLabel()`.
     */
    UPROPERTY(BlueprintReadWrite, Category = "MonolithUI|Animation")
    TArray<FName> PreserveAnimationsNamed;

    /**
     * When true, run `FKismetEditorUtilities::CompileBlueprint` once at the end
     * of the build pass instead of after each animation. Default true; set
     * false if the caller is batching multiple builders that share one compile.
     */
    UPROPERTY(BlueprintReadWrite, Category = "MonolithUI|Animation")
    bool bCompileBlueprint = true;

    /**
     * When true, validate-only — no UWidgetAnimation is mutated. The
     * `FUIAnimationRebuildResult` still reports what *would* have happened.
     */
    UPROPERTY(BlueprintReadWrite, Category = "MonolithUI|Animation")
    bool bDryRun = false;
};

/**
 * Aggregate counters produced by one `Build` pass. The builder returns this so
 * action handlers can surface "tracks_created" / "preserved" counts to the LLM
 * without re-walking the document.
 */
USTRUCT(BlueprintType)
struct MONOLITHUI_API FUIAnimationRebuildResult
{
    GENERATED_BODY()

    /** Animations newly created (did not exist before this pass). */
    UPROPERTY(BlueprintReadWrite, Category = "MonolithUI|Animation")
    int32 AnimationsCreated = 0;

    /** Animations recreated (existed, were destroyed and rebuilt). */
    UPROPERTY(BlueprintReadWrite, Category = "MonolithUI|Animation")
    int32 AnimationsRecreated = 0;

    /** Animations explicitly preserved by `PreserveAnimationsNamed` opt-in. */
    UPROPERTY(BlueprintReadWrite, Category = "MonolithUI|Animation")
    int32 AnimationsPreserved = 0;

    /** Total tracks emitted across all built animations. */
    UPROPERTY(BlueprintReadWrite, Category = "MonolithUI|Animation")
    int32 TracksCreated = 0;

    /** Total keys inserted across all built animations. */
    UPROPERTY(BlueprintReadWrite, Category = "MonolithUI|Animation")
    int32 KeysInserted = 0;

    /** Per-animation skip reasons (populated when an entry could not be built). */
    UPROPERTY(BlueprintReadWrite, Category = "MonolithUI|Animation")
    TArray<FString> Warnings;

    /**
     * True when the Build call returned cleanly (no Error-severity finding).
     * False when at least one animation entry was rejected outright (e.g.
     * unknown target widget, malformed keyframes).
     */
    UPROPERTY(BlueprintReadWrite, Category = "MonolithUI|Animation")
    bool bSuccess = true;

    /**
     * Aggregate human-readable error if `bSuccess == false`. Empty otherwise.
     */
    UPROPERTY(BlueprintReadWrite, Category = "MonolithUI|Animation")
    FString ErrorMessage;
};
