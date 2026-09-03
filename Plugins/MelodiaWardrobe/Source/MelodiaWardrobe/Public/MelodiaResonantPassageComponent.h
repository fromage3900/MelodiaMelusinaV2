#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "MelodiaCosmeticTypes.h"
#include "MelodiaResonantPassageComponent.generated.h"

class UMelodiaMusicClockSubsystem;
class UMelodiaWardrobeSubsystem;

/** Four authored beats of a Resonant World response. */
UENUM(BlueprintType)
enum class EMelodiaResonantPassageStage : uint8
{
	Inactive UMETA(DisplayName = "Inactive"),
	Invocation UMETA(DisplayName = "Invocation"),
	Unfolding UMETA(DisplayName = "Unfolding"),
	Threshold UMETA(DisplayName = "Threshold"),
	Release UMETA(DisplayName = "Release")
};

DECLARE_DYNAMIC_MULTICAST_DELEGATE_FourParams(
	FMelodiaResonantPassageStageChanged,
	FName, MovementId,
	int32, StageIndex,
	EMelodiaResonantPassageStage, Stage,
	bool, bVoiced);

/**
 * Presentation/read-model interpreter for one authored Resonant World passage.
 *
 * The component is deliberately narrow:
 *  - UMelodiaWardrobeSubsystem decides whether the required form is equipped
 *    and unlocked.
 *  - UMelodiaMusicClockSubsystem supplies authored beat events.
 *  - UMelodiaTraversalComponent remains the only movement authority.
 *  - UMelodiaNarrativeSubsystem and the existing world-challenge bridge remain
 *    the only persistence/reward authorities.
 *
 * It never grants a form, equips a cosmetic, writes a save, commits a challenge,
 * or ticks frame-by-frame.  The stage event is the seam for Niagara, PCG dressing,
 * camera/photo presentation, and UI.  A player-facing traversal request is an
 * explicit callable operation and still goes through the canonical traversal
 * component, so a passage cannot silently turn a costume into a capability.
 */
UCLASS(ClassGroup = (Melodia), BlueprintType, Blueprintable, meta = (BlueprintSpawnableComponent))
class MELODIAWARDROBE_API UMelodiaResonantPassageComponent final : public UActorComponent
{
	GENERATED_BODY()

public:
	UMelodiaResonantPassageComponent();

	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

	/** Stable authored movement identity, e.g. petal_cantata. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Resonant Passage")
	FName MovementId = TEXT("petal_cantata");

	/** Form which voices this passage. NAME_None makes the component a preview-only stage clock. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Resonant Passage|Wardrobe")
	FName RequiredResonantFormId = TEXT("ResonantForm_PetalRipple");

	/** Fail closed when a non-empty form id is unknown or locked. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Resonant Passage|Wardrobe")
	bool bRequireUnlockedForm = true;

	/** Number of authored music-clock beats spent in each stage. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Resonant Passage|Timing", meta = (ClampMin = "1", ClampMax = "32"))
	int32 BeatsPerStage = 4;

	/** If false, a Blueprint or UI may advance the presentation explicitly. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Resonant Passage|Timing")
	bool bAdvanceOnMusicBeat = true;

	/** Optional context consumed by the canonical traversal component on the pawn. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Resonant Passage|Traversal")
	FName TraversalContextId = NAME_None;

	/** Stage transition is the presentation handoff; it carries no gameplay mutation. */
	UPROPERTY(BlueprintAssignable, Category = "Melodia|Resonant Passage")
	FMelodiaResonantPassageStageChanged OnStageChanged;

	/** Re-evaluate the equipped form and reset the passage if its voice changed. */
	UFUNCTION(BlueprintCallable, Category = "Melodia|Resonant Passage")
	bool RefreshPassageVoicing();

	/** Reset the beat cursor without changing wardrobe or narrative state. */
	UFUNCTION(BlueprintCallable, Category = "Melodia|Resonant Passage")
	void ResetPassage();

	/** Current read-only voice state. */
	UFUNCTION(BlueprintPure, Category = "Melodia|Resonant Passage")
	bool IsVoicedByWardrobe() const { return bVoicedByWardrobe; }

	UFUNCTION(BlueprintPure, Category = "Melodia|Resonant Passage")
	int32 GetStageIndex() const { return StageIndex; }

	UFUNCTION(BlueprintPure, Category = "Melodia|Resonant Passage")
	EMelodiaResonantPassageStage GetStage() const;

	UFUNCTION(BlueprintPure, Category = "Melodia|Resonant Passage")
	int32 GetBeatsObserved() const { return BeatsObserved; }

	/** True only on the authored threshold/release seam. */
	UFUNCTION(BlueprintPure, Category = "Melodia|Resonant Passage|Traversal")
	bool IsTraversalWindowOpen() const;

	/**
	 * Explicit player-facing request. The request is delegated to the owner's
	 * canonical UMelodiaTraversalComponent and may still be rejected by its
	 * capability/context/resource checks.
	 */
	UFUNCTION(BlueprintCallable, Category = "Melodia|Resonant Passage|Traversal")
	bool RequestGlideAtThreshold();

private:
	UFUNCTION()
	void HandleWardrobeChanged(EMelodiaWardrobeSlot Slot, FName CosmeticId);

	UFUNCTION()
	void HandleMusicBeat(int32 BeatNumber, int32 BeatInBar);

	void BroadcastStage();
	bool IsRequiredFormEquipped() const;
	void Unbind();

	UPROPERTY(Transient)
	TObjectPtr<UMelodiaWardrobeSubsystem> Wardrobe;

	UPROPERTY(Transient)
	TObjectPtr<UMelodiaMusicClockSubsystem> MusicClock;

	UPROPERTY(Transient)
	bool bVoicedByWardrobe = false;

	UPROPERTY(Transient)
	int32 StageIndex = -1;

	UPROPERTY(Transient)
	int32 BeatsObserved = 0;

	bool bBoundWardrobe = false;
	bool bBoundMusicClock = false;
};
