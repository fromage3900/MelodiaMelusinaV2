#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "MelodiaStoryDoorComponent.generated.h"

class UMelodiaNarrativeSubsystem;

/** Where a story-gated room opening is: sealed until its flag is earned, assembling for one bar, then open. */
UENUM(BlueprintType)
enum class EMelodiaStoryDoorStage : uint8
{
	Sealed,
	Assembling,
	Open
};

DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FMelodiaStoryDoorStageChanged, EMelodiaStoryDoorStage, Stage, bool, bFromLoad);

/**
 * Presentation-only listener: reads one narrative flag (UMelodiaNarrativeSubsystem) and reports the door stage.
 * It never writes gameplay state. The owning door Blueprint binds OnStageChanged and calls UDoorComponent::Lock itself
 * (Sealed = locked, Open = unlocked), so this module needs no ProceduralDungeon dependency.
 *
 * Flag already true at BeginPlay (load/replay)  -> Open at once, bFromLoad = true, no assembly animation.
 * Flag becomes true while playing               -> Assembling for AssemblySeconds (one bar of the room's song), then Open.
 * Flag becomes false                            -> Sealed.
 * RequiredFlagId == NAME_None                    -> always Open (entrance hall).
 */
UCLASS(ClassGroup = (Melodia), meta = (BlueprintSpawnableComponent))
class BS_GODFILE_API UMelodiaStoryDoorComponent final : public UActorComponent
{
	GENERATED_BODY()

public:
	UMelodiaStoryDoorComponent();

	/** NarrativeFlagIds entry that opens this door (e.g. quest.harmony_awakening.completed). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Story Door")
	FName RequiredFlagId;

	/** Seconds spent in Assembling; house_story.py writes one bar of the room's song here. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Story Door", meta = (ClampMin = "0.0"))
	float AssemblySeconds = 1.875f;

	UPROPERTY(BlueprintAssignable, Category = "Melodia|Story Door")
	FMelodiaStoryDoorStageChanged OnStageChanged;

	UFUNCTION(BlueprintPure, Category = "Melodia|Story Door")
	EMelodiaStoryDoorStage GetStage() const { return Stage; }

	/** Re-derive the stage from the flag right now (no animation). Safe to call repeatedly. */
	UFUNCTION(BlueprintCallable, Category = "Melodia|Story Door")
	void RefreshFromFlag();

protected:
	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

private:
	UFUNCTION()
	void HandleFlagChanged(FName FlagId, bool Value);

	void SetStage(EMelodiaStoryDoorStage NewStage, bool bFromLoad);
	void FinishAssembly();
	bool ReadFlag() const;

	UPROPERTY(Transient)
	TObjectPtr<UMelodiaNarrativeSubsystem> Narrative;

	EMelodiaStoryDoorStage Stage = EMelodiaStoryDoorStage::Sealed;
	FTimerHandle AssemblyTimer;
};
