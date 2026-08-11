#pragma once

#include "CoreMinimal.h"
#include "Engine/TriggerBox.h"
#include "MelodiaFallRecoveryVolume.generated.h"

UCLASS()
class MELODIACORE_API AMelodiaFallRecoveryVolume : public ATriggerBox
{
	GENERATED_BODY()

public:
	AMelodiaFallRecoveryVolume();

	UPROPERTY(EditInstanceOnly, BlueprintReadWrite, Category="Melodia|Recovery")
	TObjectPtr<AActor> SafeAnchor;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Recovery")
	float VerticalOffset = 100.0f;

protected:
	virtual void BeginPlay() override;

private:
	UFUNCTION()
	void HandleActorEntered(AActor* OverlappedActor, AActor* OtherActor);
};
