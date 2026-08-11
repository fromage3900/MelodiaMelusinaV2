#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "MelodiaStorySequenceTrigger.generated.h"

class UBoxComponent;
class UMelodiaStorySequenceData;
class UMelodiaStorySequenceWidget;
class UPrimitiveComponent;
class APlayerController;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FMelodiaStorySequenceTriggerFinished, AActor*, TriggeringActor);

/**
 * Presentation-only overlap trigger for an authored story sequence. Place it
 * at a destination or immediately before an existing encounter. Blueprint
 * listeners decide what happens after completion; this actor never travels,
 * saves, starts battles, or changes quest state by itself.
 */
UCLASS(Blueprintable)
class MELODIACORE_API AMelodiaStorySequenceTrigger : public AActor
{
	GENERATED_BODY()

public:
	AMelodiaStorySequenceTrigger();

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Melodia|Story")
	TObjectPtr<UBoxComponent> TriggerVolume;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Story")
	TSoftObjectPtr<UMelodiaStorySequenceData> Sequence;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Story")
	TSoftClassPtr<UMelodiaStorySequenceWidget> SequenceWidgetClass;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Story")
	bool bTriggerOnce = true;

	UPROPERTY(BlueprintAssignable, Category="Melodia|Story")
	FMelodiaStorySequenceTriggerFinished OnSequenceFinished;

	UFUNCTION(BlueprintCallable, Category="Melodia|Story")
	bool PlayFor(APlayerController* PlayerController);

protected:
	UFUNCTION()
	void HandleOverlap(UPrimitiveComponent* OverlappedComponent, AActor* OtherActor,
		UPrimitiveComponent* OtherComponent, int32 OtherBodyIndex, bool bFromSweep, const FHitResult& SweepResult);

	UFUNCTION()
	void HandleSequenceFinished(UMelodiaStorySequenceData* FinishedSequence);

private:
	UPROPERTY(Transient)
	TObjectPtr<UMelodiaStorySequenceWidget> ActiveSequence;

	UPROPERTY(Transient)
	TObjectPtr<AActor> ActiveTriggeringActor;

	bool bConsumed = false;
};
