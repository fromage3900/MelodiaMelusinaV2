// MelodiaWardrobe — Magical Transform reveal component.
//
// WHAT THIS SOLVES
// A glide outfit needs to look like something. The wardrobe already swaps
// garments by equipping a second skeletal mesh into a slot
// (UMelodiaWardrobeComponent::EquipGarment), but wings are a bad fit for that
// route: the authored ButterflyWing intake is 818k verts, it needs an LOD pass
// before it can be imported at all, and it would need to be rigged to Melusina's
// exact USkeleton or the leader-pose gate refuses it outright
// (MelodiaWardrobeComponent.cpp:118 IsGarmentSkeletonCompatible).
//
// So this takes the other route, the one the Blender SSOT says the character is
// already built for -- "Clothes today = material slots on one mesh, not modular
// outfits" (Docs/MELUSINA_BLENDER_WARDROBE_SSOT.md). The wing geometry lives in
// Melusina's existing body mesh as its own material slot, permanently present
// and permanently masked out. Unlocking the glide outfit does not add a mesh; it
// animates that slot's opacity mask from 0 to 1. No new skeletal mesh, no
// skeleton compatibility risk, no extra draw call when concealed.
//
// WHY IT IS A SEPARATE COMPONENT
// UMelodiaWardrobeComponent is a non-ticking presentation component that owns
// mesh slots and body-region morphs. This owns a timed material animation, needs
// a tick while it runs, and reads state it must never write. Folding it in would
// give the wardrobe component a tick it does not otherwise need and would blur
// "who owns the equipped map" with "who owns the reveal".
//
// AUTHORITY BOUNDARIES
//  - READS  UMelodiaWardrobeSubsystem (capability + equipped state). Never writes
//           it. The narrative record stays the only durable wardrobe state.
//  - OWNS   every Magical Transform material parameter on the accessory MIDs it
//           claims, and the two MelodiaMagicalTransformMPC scalars.
//  - CLAIMS wing opacity from UMelodiaTraversalComponent, which otherwise slams
//           the same scalar to a binary 0/1 on glide start/stop and would erase
//           the reveal mid-animation. The claim is explicit, not a race.
//
// Companion material authoring: Content/Python/wire_magical_transform_reveal.py

#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "MelodiaCosmeticTypes.h"        // EMelodiaFormCapability
#include "MelodiaMagicalTransformTypes.h"
#include "MelodiaNarrativeTypes.h"       // EMelodiaWardrobeSlot
#include "MelodiaMagicalTransformComponent.generated.h"

class UCurveFloat;
class UMaterialInstanceDynamic;
class UMaterialParameterCollection;
class UMeshComponent;
class USkeletalMeshComponent;
class UMelodiaTraversalComponent;
class UMelodiaWardrobeSubsystem;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(
	FMelodiaMagicalTransformPhaseChanged,
	EMelodiaMagicalTransformPhase, Phase,
	float, Progress);

/**
 * One claimed material, with the provenance needed to diagnose a silent no-op.
 *
 * The slot name is kept because SetScalarParameterValue on a parameter a
 * material does not expose is not an error -- it returns quietly. When a reveal
 * does not appear, the first question is "which slots did it actually claim",
 * and without this the answer is unavailable.
 */
USTRUCT()
struct FMelodiaMagicalTransformBinding
{
	GENERATED_BODY()

	UPROPERTY(Transient)
	TObjectPtr<UMaterialInstanceDynamic> Material = nullptr;

	/** Material slot name this MID was created for, for logging only. */
	UPROPERTY(Transient)
	FName SlotName;

	/** True when this slot is wing geometry and should have its opacity driven. */
	UPROPERTY(Transient)
	bool bIsWing = false;
};

UCLASS(ClassGroup=(Melodia), Blueprintable, meta=(BlueprintSpawnableComponent))
class MELODIAWARDROBE_API UMelodiaMagicalTransformComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	UMelodiaMagicalTransformComponent();

	// ── Playback ──────────────────────────────────────────────────────────────

	/**
	 * Starts the 0 -> 1 reveal. Safe to call while already revealing (no-op) or
	 * while concealing (reverses from the current progress rather than snapping
	 * back to 0, so a fast unequip/re-equip does not stutter).
	 */
	UFUNCTION(BlueprintCallable, Category="Melodia|MagicalTransform")
	void PlayReveal();

	/** Starts the 1 -> 0 conceal. Mirror of PlayReveal. */
	UFUNCTION(BlueprintCallable, Category="Melodia|MagicalTransform")
	void PlayConceal();

	/**
	 * Jumps straight to a steady phase with no animation.
	 *
	 * This is the save-restore path: a player who loads a save already wearing
	 * the glide outfit should be wearing wings, not watch a transformation
	 * cutscene at every level load.
	 */
	UFUNCTION(BlueprintCallable, Category="Melodia|MagicalTransform")
	void SnapToPhase(EMelodiaMagicalTransformPhase TargetPhase);

	/**
	 * Re-derives the desired phase from the wardrobe's active capabilities and
	 * plays the transition if it differs from the current one.
	 *
	 * Call after anything that could change the equipped set outside the
	 * OnWardrobeChanged broadcast. Idempotent -- only an actual edge animates.
	 */
	UFUNCTION(BlueprintCallable, Category="Melodia|MagicalTransform")
	void SyncToWardrobeState(bool bAllowAnimation = true);

	/**
	 * Rediscovers the accessory material set and re-applies the current pose.
	 *
	 * Necessary because a wardrobe slot component is created lazily on first
	 * equip (MelodiaWardrobeComponent.cpp:138 FindOrCreateSlotComponent). A
	 * garment equipped after the reveal finished would otherwise arrive at its
	 * material default and be the one visibly wrong piece.
	 */
	UFUNCTION(BlueprintCallable, Category="Melodia|MagicalTransform")
	void RefreshAccessoryMaterials();

	/**
	 * Advances the transition by DeltaSeconds and writes the resulting pose.
	 *
	 * This is the whole per-frame body; TickComponent does nothing but call it.
	 * Separated out because the transformation is exactly the kind of thing an
	 * authored scene wants to scrub rather than let run on wall-clock time -- a
	 * Sequencer track or a cutscene director can step it directly, and the
	 * automation suite can assert on the curve without a registered tick.
	 *
	 * Safe to call when nothing is animating: a steady phase just re-applies its
	 * held pose.
	 */
	UFUNCTION(BlueprintCallable, Category="Melodia|MagicalTransform")
	void AdvanceTransform(float DeltaSeconds);

	// ── Read-only state ───────────────────────────────────────────────────────

	UFUNCTION(BlueprintPure, Category="Melodia|MagicalTransform")
	EMelodiaMagicalTransformPhase GetPhase() const { return Phase; }

	/** Current master progress, 0..1. */
	UFUNCTION(BlueprintPure, Category="Melodia|MagicalTransform")
	float GetProgress() const { return Progress; }

	UFUNCTION(BlueprintPure, Category="Melodia|MagicalTransform")
	bool IsRevealed() const { return Phase == EMelodiaMagicalTransformPhase::Revealed; }

	/** True while a transition is animating. */
	UFUNCTION(BlueprintPure, Category="Melodia|MagicalTransform")
	bool IsTransitioning() const
	{
		return Phase == EMelodiaMagicalTransformPhase::Revealing
			|| Phase == EMelodiaMagicalTransformPhase::Concealing;
	}

	/** How many materials the reveal actually claimed. Zero means it will do nothing. */
	UFUNCTION(BlueprintPure, Category="Melodia|MagicalTransform")
	int32 GetClaimedMaterialCount() const { return Bindings.Num(); }

	/** How many of the claimed materials are wing slots. */
	UFUNCTION(BlueprintPure, Category="Melodia|MagicalTransform")
	int32 GetClaimedWingMaterialCount() const;

	UPROPERTY(BlueprintAssignable, Category="Melodia|MagicalTransform")
	FMelodiaMagicalTransformPhaseChanged OnMagicalTransformPhaseChanged;

	// ── Trigger configuration ─────────────────────────────────────────────────

	/**
	 * The capability whose activation reveals the accessories.
	 *
	 * Glide by default, because the wing IS the glide affordance -- the player
	 * needs to be able to see that they can now glide. Kept configurable so a
	 * Swim form can reveal fins through the same component rather than a copy.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|MagicalTransform|Trigger")
	EMelodiaFormCapability TriggerCapability = EMelodiaFormCapability::Glide;

	/**
	 * Context passed to the capability query, matching
	 * UMelodiaTraversalComponent::GetTraversalCapabilityContextId.
	 *
	 * Left None deliberately. A form's RestrictedContextIds can suppress glide in
	 * a boss arena, and passing that context here would strip the wings off her
	 * back on arena entry. The wings are a costume; the ABILITY is what the arena
	 * restricts. Set this only if you want the visual to track the restriction.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|MagicalTransform|Trigger")
	FName CapabilityContextId = NAME_None;

	/**
	 * When true, BeginPlay animates an already-satisfied capability instead of
	 * snapping to it.
	 *
	 * Default false: on level load the outfit is restored from the save and there
	 * is nothing to celebrate. Turn this on only for an authored scene that opens
	 * on the transformation.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|MagicalTransform|Trigger")
	bool bAnimateOnBeginPlay = false;

	// ── Timing and shape ──────────────────────────────────────────────────────

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|MagicalTransform|Timing", meta=(ClampMin="0.05", ClampMax="20.0"))
	float RevealDurationSeconds = 2.4f;

	/**
	 * Conceal is faster than reveal on purpose. Gaining the form is the moment
	 * worth watching; taking the outfit off in a menu is not.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|MagicalTransform|Timing", meta=(ClampMin="0.05", ClampMax="20.0"))
	float ConcealDurationSeconds = 0.9f;

	/** The authored keyframes. Defaults to MakeDefaultRevealTrack in the ctor. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|MagicalTransform|Shape")
	FMelodiaMagicalTransformTrack RevealTrack;

	/**
	 * Optional frame-accurate easing for the progress channel only.
	 *
	 * When set, this replaces the track's Progress output while Dissolve, Bloom
	 * and Sparkle still come from the keys. That split exists because progress is
	 * the channel an animator wants to hand-tune against a music cue, and the
	 * other three are look-dev values that should stay locked to it.
	 *
	 * Expected domain 0..1 on both axes. A curve authored over a different range
	 * is sampled by normalized time regardless, so its tail is what you get.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|MagicalTransform|Shape")
	TObjectPtr<UCurveFloat> ProgressCurveOverride = nullptr;

	/**
	 * Colour written to MagicalTransformTint.
	 * Default is Melusina's pale gold wavefront.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|MagicalTransform|Shape")
	FLinearColor WavefrontTint = FLinearColor(1.0f, 0.86f, 0.62f, 1.0f);

	/**
	 * Multiplies the Bloom channel by cos^2(BeatPhase * pi) so the wavefront
	 * pulses on the beat.
	 *
	 * 0 disables the modulation entirely. This never scales Progress -- a reveal
	 * whose completion depended on the beat would never finish without a music
	 * clock, and the transition has to be able to complete in silence.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|MagicalTransform|Shape", meta=(ClampMin="0.0", ClampMax="1.0"))
	float BeatModulationStrength = 0.6f;

	// ── Discovery ─────────────────────────────────────────────────────────────

	/**
	 * Material slot names on the owning character's body mesh that count as WING
	 * geometry. These get their opacity mask driven by the reveal.
	 *
	 * Matched case-insensitively as a substring, because Melusina's 33 slots use
	 * inconsistent casing and numeric suffixes that shift between exports
	 * (M_shirt_001 / M_SHAWL_001 / M_SKIRT_003), so an exact-match list would go
	 * stale on the next re-import without anything reporting it.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|MagicalTransform|Discovery")
	TArray<FName> WingSlotNameFilters;

	/**
	 * Additional slot names that participate in the transform "accessory wide"
	 * but are NOT wings: they receive progress/dissolve/bloom/sparkle so they
	 * shimmer through the transformation, but their opacity is never touched.
	 *
	 * This is the difference between "the wings appear" and "the whole costume
	 * reacts". Driving opacity here instead would dissolve her clothes.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|MagicalTransform|Discovery")
	TArray<FName> AccessorySlotNameFilters;

	/**
	 * Wardrobe slot components whose materials join the transform.
	 *
	 * Accessories/HairCharm/Trail by default -- the decorative slots. Body,
	 * Shirt and Skirt are deliberately absent: they are the base outfit and
	 * should not shimmer every time a hair charm changes.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|MagicalTransform|Discovery")
	TArray<EMelodiaWardrobeSlot> AccessoryWardrobeSlots;

	/**
	 * A whole mesh component tagged this way is treated as wing geometry, all
	 * material indices included.
	 *
	 * Matches UMelodiaTraversalComponent::WingComponentTag's default so an
	 * already-authored wing component is picked up without re-tagging. This is
	 * the escape hatch for the day the wings DO become their own mesh; the
	 * material-slot route above is the no-new-mesh default.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|MagicalTransform|Discovery")
	FName WingComponentTag = TEXT("MelodiaWings");

	/** As WingComponentTag, but joins the transform without opacity control. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|MagicalTransform|Discovery")
	FName AccessoryComponentTag = TEXT("MelodiaAccessory");

	// ── Interop ───────────────────────────────────────────────────────────────

	/**
	 * Take wing-opacity ownership from UMelodiaTraversalComponent on BeginPlay.
	 *
	 * Leave this on. With it off, both components write the same `Opacity`
	 * scalar: the traversal component sets it to 0 in its own BeginPlay and again
	 * on every StopGlide, so the reveal would be silently erased the first time
	 * the player landed. Turning it off is only correct if this component claims
	 * no wing materials at all.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|MagicalTransform|Interop")
	bool bClaimWingOpacityFromTraversal = true;

	/**
	 * Extra bloom added while gliding, on top of the revealed pose.
	 *
	 * Added, not assigned. The glide flare has to compose with the reveal rather
	 * than replace it, or starting a glide mid-transformation would jump the
	 * wings to full brightness and back.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|MagicalTransform|Interop", meta=(ClampMin="0.0", ClampMax="8.0"))
	float GlideFlareBloom = 1.15f;

	/** Seconds for the glide flare to ease in and out. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|MagicalTransform|Interop", meta=(ClampMin="0.01", ClampMax="4.0"))
	float GlideFlareBlendSeconds = 0.35f;

	/**
	 * Mirror progress and flare onto MPC_Melodia_Palette for world-side effects
	 * that cannot read a per-character MID.
	 *
	 * Only MelodiaMagicalTransformMPC::Progress and ::Flare are written -- never
	 * anything in the beat namespace, which
	 * UMelodiaAudioReactivePresentationSubsystem owns as sole writer.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|MagicalTransform|Interop")
	bool bPublishToParameterCollection = true;

protected:
	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
	virtual void TickComponent(
		float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

private:
	UFUNCTION()
	void HandleWardrobeChanged(EMelodiaWardrobeSlot Slot, FName CosmeticId);

	UFUNCTION()
	void HandleGlideStateChanged(bool bIsGliding);

	/** True when the trigger capability is currently active on the wardrobe. */
	bool IsTriggerCapabilityActive() const;

	/** Collect MIDs from the body mesh, wardrobe slot components, and tagged meshes. */
	void ResolveBindings();

	/**
	 * Claims MIDs from one mesh component.
	 *
	 * @param bForceWing              Treat every slot as wing geometry.
	 * @param bTagDiscovered          Component was found by tag, so it is safe to
	 *                                hide wholesale when concealed.
	 * @param bIncludeUnmatchedSlots  Claim slots that match no name filter. True
	 *                                for a whole component that IS an accessory
	 *                                (a wardrobe garment, a tagged mesh); false
	 *                                for the body mesh, where only the named
	 *                                slots may participate.
	 */
	void CollectFromMeshComponent(
		UMeshComponent* Mesh, bool bForceWing, bool bTagDiscovered, bool bIncludeUnmatchedSlots);

	/** Classify one slot name against the filters. Returns false when it matches neither. */
	bool ClassifySlot(FName SlotName, bool& bOutIsWing) const;

	/** Sample the track (or the curve override) at the current normalized time. */
	FMelodiaMagicalTransformPose EvaluateCurrentPose() const;

	/** Write one pose to every claimed MID, plus the MPC mirror. */
	void ApplyPose(const FMelodiaMagicalTransformPose& Pose);

	/** cos^2(BeatPhase * pi) from the palette MPC, or 0 with no music clock. */
	float ReadBeatPulse() const;

	void SetPhase(EMelodiaMagicalTransformPhase NewPhase);

	/** Enable tick only while something is actually animating. */
	void UpdateTickEnabled();

	USkeletalMeshComponent* GetBodyMesh() const;
	UMelodiaTraversalComponent* GetTraversalComponent() const;

	UPROPERTY(Transient)
	TArray<FMelodiaMagicalTransformBinding> Bindings;

	/**
	 * Mesh components discovered wholly by tag, and therefore safe to hide when
	 * concealed.
	 *
	 * The body mesh is deliberately NOT in this list. A wing that lives as a
	 * material slot on the body mesh must be hidden by its opacity mask alone --
	 * hiding the component would make Melusina invisible.
	 */
	UPROPERTY(Transient)
	TArray<TWeakObjectPtr<UMeshComponent>> HideableWingComponents;

	UPROPERTY(Transient)
	TObjectPtr<UMaterialParameterCollection> PaletteCollection = nullptr;

	EMelodiaMagicalTransformPhase Phase = EMelodiaMagicalTransformPhase::Dormant;

	/**
	 * The animation clock, 0..1 in AUTHORED time -- not the output progress.
	 *
	 * Reversal is why these are separate. Progress comes out of a non-linear
	 * keyframe track, so resuming a reversed transition from a progress value
	 * would mean inverting the curve, which is ambiguous the moment the track is
	 * non-monotonic. Keeping the clock and running it backwards is exact, and it
	 * makes an interrupted transformation reverse along the path it came in on.
	 */
	float NormalizedTime = 0.0f;

	/** Cached Progress output of the last applied pose, for the pure getter. */
	float Progress = 0.0f;

	/** 0..1 blend of the glide flare, eased by GlideFlareBlendSeconds. */
	float GlideFlareAlpha = 0.0f;
	bool bGlideFlareTarget = false;

	/** Warn-once so a mis-filtered slot list does not spam every equip. */
	bool bWarnedNoBindings = false;
	bool bClaimedTraversalWingOpacity = false;
};
