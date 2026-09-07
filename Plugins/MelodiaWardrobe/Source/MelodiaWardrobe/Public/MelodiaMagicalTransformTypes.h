// MelodiaWardrobe — Magical Transform presentation vocabulary.
//
// The "Magical Transform" is the authored henshin-style reveal that plays when a
// Resonant Form's capability becomes active: Melusina's accessory materials
// dissolve in from nothing rather than popping on. It exists so a glide outfit
// can be presented WITHOUT authoring a second skeletal mesh -- the wing is a
// material slot on the body mesh whose opacity mask is driven from 0 to 1.
//
// WHY THE NAMES LIVE HERE AND NOWHERE ELSE
// `capability.melodia.glide` was once a raw literal duplicated across two
// modules, and a rename on either side silently disabled the ability
// (MelodiaTraversalCapabilityProvider.h:18). Material parameter names have the
// same failure shape and it is worse: SetScalarParameterValue on a name the
// material does not expose is NOT an error. It returns quietly, the reveal never
// animates, and there is nothing in the log to find. So the vocabulary is
// declared once, here, and both the runtime writer and the Python material
// builder reference it.
//
// Companion authoring script: Content/Python/wire_magical_transform_reveal.py
// -- it creates exactly these parameters on M_Master_Toon_Universal and the two
// MPC scalars below. If you add a name here, add it there in the same change or
// the write lands on nothing.

#pragma once

#include "CoreMinimal.h"
#include "MelodiaMagicalTransformTypes.generated.h"

/**
 * Material parameter names the Magical Transform writes.
 *
 * These are MATERIAL INSTANCE parameters, set per-MID by
 * UMelodiaMagicalTransformComponent. They are not MPC parameters: the reveal is
 * per-character state, and an MPC is global. The two MPC scalars the reveal
 * publishes for world-side effects are in MelodiaMagicalTransformMPC below.
 */
namespace MelodiaMagicalTransformParameter
{
	/**
	 * Master progress, 0 = concealed, 1 = fully revealed.
	 *
	 * Everything else is derived from this in the material graph, so a material
	 * that exposes only this one parameter still reads correctly -- just without
	 * the wavefront flourish.
	 */
	inline const FName Progress{TEXT("MagicalTransformProgress")};

	/**
	 * Opacity-mask multiplier. Deliberately named `Opacity` because that is
	 * already UMelodiaTraversalComponent::WingOpacityParameter's default
	 * (MelodiaTraversalComponent.h:392), so an authored wing material that
	 * predates this system needs no re-authoring to participate.
	 */
	inline const FName Opacity{TEXT("Opacity")};

	/**
	 * The master's own opacity-mask strength, written alongside Opacity.
	 *
	 * M_Master_Toon_Universal exposes OpacityStrength (with OpacityMap and the
	 * bUseOpacityMap switch) feeding MP_OPACITY_MASK -- ported into the opaque
	 * master by Content/Python/converge_toon_universal.py step1_opacity. Writing
	 * both names means the reveal works on the shared master lane and on a
	 * bespoke wing material, without the component needing to know which it got.
	 */
	inline const FName OpacityStrength{TEXT("OpacityStrength")};

	/**
	 * Erosion band position for the dissolve edge.
	 *
	 * The reveal is a MASKED dissolve, not an alpha fade. That is a deliberate
	 * choice, not a limitation: M_Master_Toon_Universal is BLEND_OPAQUE and its
	 * Substrate Toon BSDF has no opacity input, so translucency would mean a new
	 * master and a new sort order for a character that already ships 33 material
	 * slots. Masked dissolve routes through the existing MP_OPACITY_MASK path,
	 * costs nothing extra, and is the look the reference already uses
	 * (MI_Universal_HenshinDither).
	 */
	inline const FName Dissolve{TEXT("MagicalTransformDissolve")};

	/** Emissive gain at the dissolve wavefront -- the bright edge that sells it. */
	inline const FName Bloom{TEXT("MagicalTransformBloom")};

	/** Sparkle-mote density, peaks mid-transition and settles to nothing. */
	inline const FName Sparkle{TEXT("MagicalTransformSparkle")};

	/**
	 * cos^2(BeatPhase * pi), forwarded per-MID so the wavefront lands on the beat.
	 *
	 * cos^2 rather than sin^2 because BeatPhase is 0 ON the beat -- the same
	 * correction already applied in UMelodiaAudioReactivePresentationSubsystem
	 * and wire_audio_foliage_materials.py. Zero-safe: no music clock means 0,
	 * which flattens the modulation instead of inventing a tempo.
	 */
	inline const FName Beat{TEXT("MagicalTransformBeat")};

	/** Wavefront colour. Vector parameter. */
	inline const FName Tint{TEXT("MagicalTransformTint")};
}

/**
 * MPC scalars the reveal publishes for world-side reactions (a bloom lift, a
 * post-process pulse) that cannot read a per-character MID.
 *
 * OWNERSHIP CAUTION: UMelodiaAudioReactivePresentationSubsystem is the declared
 * single writer of MPC_Melodia_Palette's beat namespace. These two names are NOT
 * in that namespace and are written only by the Magical Transform component, so
 * there is still exactly one writer per parameter. Do not add a beat-namespace
 * name here.
 */
namespace MelodiaMagicalTransformMPC
{
	inline const FName CollectionPath{TEXT("/Game/Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette.MPC_Melodia_Palette")};

	/** Mirror of the active character's transform progress, 0..1. */
	inline const FName Progress{TEXT("MagicalTransform")};

	/** Wavefront intensity, peaks mid-transition. 0 at rest. */
	inline const FName Flare{TEXT("MagicalTransformFlare")};
}

/**
 * Where a character is in the reveal.
 *
 * Dormant and Revealed are both STEADY states that write a held pose every time
 * they are entered; they are not "do nothing" states. A slot equipped while
 * Revealed must inherit the revealed pose, or a garment that arrives late pops
 * in at its material default.
 */
UENUM(BlueprintType)
enum class EMelodiaMagicalTransformPhase : uint8
{
	/** Concealed. Progress 0, wing opacity 0. The zero-safe default. */
	Dormant,

	/** Playing 0 -> 1. */
	Revealing,

	/** Held at 1. */
	Revealed,

	/** Playing 1 -> 0. */
	Concealing
};

/**
 * One authored keyframe of the transform.
 *
 * This is the keyframing surface. It is a struct array rather than a Blueprint
 * timeline because the reveal has to run from native code on a wardrobe
 * broadcast -- a timeline lives on a Blueprint and cannot be evaluated by the
 * component that owns the material writes. It is a struct array rather than four
 * UCurveFloat assets because the channels have to stay in sync: a designer
 * moving the wavefront has to move the bloom with it, and four separate assets
 * is four chances to forget one. A single UCurveFloat override is still
 * available on the component for the progress channel when an artist wants
 * frame-accurate easing.
 *
 * Keys are sampled with linear interpolation on normalized time. They do not
 * need to be sorted; the evaluator sorts a working copy.
 */
USTRUCT(BlueprintType)
struct MELODIAWARDROBE_API FMelodiaMagicalTransformKey
{
	GENERATED_BODY()

	/** Normalized position in the transition, 0..1. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|MagicalTransform", meta=(ClampMin="0.0", ClampMax="1.0"))
	float Time = 0.0f;

	/** Reveal amount at this key, 0..1. Drives the opacity mask. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|MagicalTransform", meta=(ClampMin="0.0", ClampMax="1.0"))
	float Progress = 0.0f;

	/** Erosion band width at this key. Widest mid-transition, 0 at both ends. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|MagicalTransform", meta=(ClampMin="0.0", ClampMax="1.0"))
	float Dissolve = 0.0f;

	/** Emissive gain at this key. Allowed above 1 -- this is the flare. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|MagicalTransform", meta=(ClampMin="0.0", ClampMax="8.0"))
	float Bloom = 0.0f;

	/** Sparkle density at this key, 0..1. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|MagicalTransform", meta=(ClampMin="0.0", ClampMax="1.0"))
	float Sparkle = 0.0f;
};

/**
 * The evaluated transform at one instant -- what actually gets written to MIDs.
 *
 * Separated from the key struct so evaluation is a pure function of
 * (keys, time) with no component or world involved. That is what makes the
 * curve testable in an automation test that never opens a level.
 */
USTRUCT(BlueprintType)
struct MELODIAWARDROBE_API FMelodiaMagicalTransformPose
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadOnly, Category="Melodia|MagicalTransform")
	float Progress = 0.0f;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|MagicalTransform")
	float Dissolve = 0.0f;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|MagicalTransform")
	float Bloom = 0.0f;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|MagicalTransform")
	float Sparkle = 0.0f;
};

/**
 * An authored keyframe track plus its evaluator.
 *
 * Empty track = a straight linear ramp on Progress with no flourish, NOT a
 * no-op. An unauthored component still reveals the wing; it just does it
 * plainly. Failing to nothing here would mean a missing curve asset silently
 * costs you the whole feature.
 */
USTRUCT(BlueprintType)
struct MELODIAWARDROBE_API FMelodiaMagicalTransformTrack
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|MagicalTransform")
	TArray<FMelodiaMagicalTransformKey> Keys;

	/**
	 * Samples the track at NormalizedTime (clamped to 0..1).
	 *
	 * Static and side-effect free so the automation suite can assert on the
	 * curve without a world, a pawn, or a material.
	 */
	static FMelodiaMagicalTransformPose Evaluate(
		const TArray<FMelodiaMagicalTransformKey>& InKeys, float NormalizedTime);

	FMelodiaMagicalTransformPose Evaluate(float NormalizedTime) const
	{
		return Evaluate(Keys, NormalizedTime);
	}

	/**
	 * The default authored shape: a slow bloom-led wavefront that overshoots the
	 * flare before settling. Used when a designer has authored nothing, so the
	 * out-of-the-box reveal already reads as a transformation rather than a fade.
	 */
	static FMelodiaMagicalTransformTrack MakeDefaultRevealTrack();
};
