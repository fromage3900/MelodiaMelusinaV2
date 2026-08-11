// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "MelodiaMapTransitionComponent.generated.h"

class AActor;

UCLASS(ClassGroup=(Melodia), meta=(BlueprintSpawnableComponent))
class BS_GODFILE_API UMelodiaMapTransitionComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	UMelodiaMapTransitionComponent();

	// Transition to a new map
	UFUNCTION(BlueprintCallable, Category="Melodia|Transition")
	void TransitionToMap(const FString& MapName);

	// Set the target map
	UFUNCTION(BlueprintCallable, Category="Melodia|Transition")
	void SetTargetMap(const FString& MapName);

protected:
	virtual void BeginPlay() override;

private:
	UPROPERTY(EditAnywhere, Category="Melodia|Transition")
	FString TargetMapName;

	/**
	 * PlayerStart to arrive at in the destination. Leave empty and the engine picks,
	 * which is a coin flip on any map with more than one start.
	 */
	UPROPERTY(EditAnywhere, Category="Melodia|Transition")
	FName TargetSpawnTag;

	UPROPERTY(EditAnywhere, Category="Melodia|Transition")
	bool bAutoTransition;

	/**
	 * Auto-overlaps defer at least one frame so dialogue/interactions entered by
	 * the same overlap can claim input first. While Dialogue/Menu owns input the
	 * transition remains pending and fires only after that context is released.
	 */
	UPROPERTY(EditAnywhere, Category="Melodia|Transition", meta=(ClampMin="0.02", ClampMax="1.0"))
	float BlockedTransitionRetryDelay = 0.1f;

	TWeakObjectPtr<AActor> PendingTransitionActor;
	FTimerHandle PendingTransitionTimer;

	UFUNCTION()
	void OnOverlapBegin(UPrimitiveComponent* OverlappedComp, AActor* OtherActor, 
		UPrimitiveComponent* OtherComp, int32 OtherBodyIndex, bool bFromSweep, 
		const FHitResult& SweepResult);

	void AttemptPendingAutoTransition();
};