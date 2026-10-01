// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Components/SceneComponent.h"
#include "Kismet/KismetSystemLibrary.h"
#include "ACFFrontTracerComponent.generated.h"

/** Delegate triggered when a new actor is detected */
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnActorDetected, const AActor*, detectedActor);

/**
 * UACFFrontTracerComponent
 *
 * A component used to perform forward traces in the game world to detect specific actors.
 * It supports both single and continuous tracing modes.
 */
UCLASS(Blueprintable, ClassGroup = (ACF), meta = (BlueprintSpawnableComponent))
class ASCENTCOMBATFRAMEWORK_API UACFFrontTracerComponent : public USceneComponent
{
	GENERATED_BODY()

public:	
	/** Constructor - Sets default values for this component's properties */
	UACFFrontTracerComponent();

protected:
	/** Called when the game starts */
	virtual void BeginPlay() override;

public:	
	/** Called every frame */
	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

	/** Performs a single trace in front of the actor */
	void PerformTrace();

	/**
	 * Performs a single forward trace and returns the first detected actor.
	 * @return The first detected actor in the trace.
	 */
	UFUNCTION(BlueprintCallable, Category = ACF)
	AActor* PerformFrontTraceSingle();

	/** Starts continuous tracing */
	UFUNCTION(BlueprintCallable, Category = ACF)
	void StartContinuousTrace();
	
	/** Stops continuous tracing */
	UFUNCTION(BlueprintCallable, Category = ACF)
	void StopContinuousTrace();

	/**
	 * Gets the currently traced actor.
	 * @return The currently detected actor, or nullptr if no actor is detected.
	 */
	UFUNCTION(BlueprintPure, Category = ACF)
	AActor* GetCurrentlyTracedActor() const {
		return currentTracedActor;
	}

	/** Delegate event triggered when a new actor is detected */
	UPROPERTY(BlueprintAssignable, Category = ACF)
	FOnActorDetected OnNewActorDetected;

	/** The length of the trace (in Unreal units) */
	UPROPERTY(EditDefaultsOnly, Category = ACF)
	float TraceLength = 2500;

	/** Object types to trace against */
	UPROPERTY(EditDefaultsOnly, Category = ACF)
	TArray<TEnumAsByte<EObjectTypeQuery>> ChannelsToTrace;

	/** Debug visualization mode */
	UPROPERTY(EditDefaultsOnly, Category = ACF)
	TEnumAsByte<EDrawDebugTrace::Type> ShowDebug;

	/** The type of actor to detect (if set, only this type will be considered) */
	UPROPERTY(EditDefaultsOnly, Category = ACF)
	TSubclassOf<AActor> ActorToFind;

	/** If true, the player-controlled character will be ignored in traces */
	UPROPERTY(EditDefaultsOnly, Category = ACF)
	bool bIgnorePlayer = true;

	/** If true, debug trace visualization will be enabled */
	UPROPERTY(EditDefaultsOnly, Category = ACF)
	bool bShowDebugTrace = false;

private: 

	/** Current state of the continuous trace */
	bool bCurrentTraceState;

	/** The currently traced actor */
	UPROPERTY()
	AActor* currentTracedActor;

	/** Sets the currently traced actor */
	void SetCurrentTracedActor(AActor* newActor);
};
