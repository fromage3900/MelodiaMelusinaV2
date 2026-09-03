// STORY-TRAVEL ONLY: deterministic authored-map travel for the opening campaign.
// Never advances UMelodiaRoguelikeRunSubsystem and never invokes ProceduralDungeon.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework\Actor.h"
#include "MelodiaOpeningFlowSubsystem.h"
#include "MelodiaOpeningPortal.generated.h"

class UBoxComponent;
class UTextRenderComponent;

UCLASS(Blueprintable, meta=(DisplayName="Melodia Story Travel Portal"))
class MELODIACORE_API AMelodiaOpeningPortal : public AActor
{
	GENERATED_BODY()

public:
	AMelodiaOpeningPortal();

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Melodia|Story Travel")
	TObjectPtr<UBoxComponent> TriggerVolume;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Melodia|Story Travel")
	TObjectPtr<UTextRenderComponent> PromptText;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Story Travel", meta=(AllowedClasses="/Script/Engine.World"))
	FName DestinationLevelName = TEXT("/Game/ZenForestTest");

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Story Travel")
	EMelodiaOpeningTravelEvent TravelEvent = EMelodiaOpeningTravelEvent::CompleteDreamstate;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Story Travel")
	bool bOneShot = true;

protected:
	virtual void BeginPlay() override;

	UFUNCTION()
	void HandleOverlap(UPrimitiveComponent* OverlappedComponent, AActor* OtherActor,
		UPrimitiveComponent* OtherComp, int32 OtherBodyIndex, bool bFromSweep,
		const FHitResult& SweepResult);

private:
	bool bActivated = false;
};
