#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "MelodiaInputContextSubsystem.h"
#include "MelodiaRhythmCombatTypes.h"
#include "MelodiaHybridEncounterComponent.generated.h"

/** The presentation driving one live encounter actor. */
UENUM(BlueprintType)
enum class EMelodiaHybridPresentationMode : uint8
{
	Flow,
	Sequence
};

DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FMelodiaHybridModeChanged,
	EMelodiaHybridPresentationMode, Mode, AActor*, Target);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FMelodiaHybridEffectRequested,
	AActor*, Target, const FMelodiaRhythmEffectRequest&, Request);

/**
 * Coordinates presentation and input for one existing world actor. The owner
 * remains the only encounter target and HP owner through both modes. Rhythm
 * grading belongs to UMelodiaRhythmCombatSubsystem; a stock resolver must
 * supply FinalDamage before either damage entry point may be used.
 */
UCLASS(ClassGroup=(Melodia), meta=(BlueprintSpawnableComponent))
class BS_GODFILE_API UMelodiaHybridEncounterComponent final : public UActorComponent
{
	GENERATED_BODY()

public:
	UMelodiaHybridEncounterComponent();

	/** Stable authored encounter identity, shared by Flow, Sequence and outcome. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Hybrid")
	FName EncounterId = NAME_None;

	UFUNCTION(BlueprintPure, Category="Melodia|Hybrid")
	FName GetEncounterId() const { return EncounterId; }

	UFUNCTION(BlueprintPure, Category="Melodia|Hybrid")
	AActor* GetEncounterTarget() const { return GetOwner(); }

	UFUNCTION(BlueprintPure, Category="Melodia|Hybrid")
	EMelodiaHybridPresentationMode GetPresentationMode() const { return PresentationMode; }

	UFUNCTION(BlueprintPure, Category="Melodia|Hybrid")
	bool HasPendingSequenceEffect() const { return PendingEffectSessionId != 0; }

	/** A deliberate phrase transition; does not create or replace the target. */
	UFUNCTION(BlueprintCallable, Category="Melodia|Hybrid")
	bool EnterSequence(FName RhythmSkillId);

	/** Restore continuous movement after the phrase's effect has resolved. */
	UFUNCTION(BlueprintCallable, Category="Melodia|Hybrid")
	bool ExitSequence();

	/** Forward lane input to the project's sole rhythm grader. */
	UFUNCTION(BlueprintCallable, Category="Melodia|Hybrid")
	EMelodiaSkillGrade RegisterSequenceLaneHit(int32 LaneIndex);

	UFUNCTION(BlueprintCallable, Category="Melodia|Hybrid")
	bool FinishSequencePhrase();

	/** Accept only an already resolved stock damage number, once per phrase. */
	UFUNCTION(BlueprintCallable, Category="Melodia|Hybrid")
	bool ApplyResolvedSequenceDamage(float FinalDamage, int32 SessionId);

	/** Flow attack sink for an already resolved stock damage number. */
	UFUNCTION(BlueprintCallable, Category="Melodia|Hybrid")
	bool ApplyResolvedFlowDamage(float FinalDamage);

	UPROPERTY(BlueprintAssignable, Category="Melodia|Hybrid")
	FMelodiaHybridModeChanged OnPresentationModeChanged;

	/** Request metadata only; the stock resolver must produce FinalDamage. */
	UPROPERTY(BlueprintAssignable, Category="Melodia|Hybrid")
	FMelodiaHybridEffectRequested OnWorldEffectRequested;

protected:
	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

private:
	UFUNCTION()
	void HandleRhythmComplete(EMelodiaSkillGrade Grade, int32 HitCount, int32 MissCount);

	UPROPERTY(Transient)
	EMelodiaHybridPresentationMode PresentationMode = EMelodiaHybridPresentationMode::Flow;

	FMelodiaInputContextHandle RhythmInputHandle;
	int32 SequenceSessionId = 0;
	int32 PendingEffectSessionId = 0;
};
