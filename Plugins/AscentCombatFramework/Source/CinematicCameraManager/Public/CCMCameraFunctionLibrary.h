// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 
/*
2018 PakyMan Prod. 
*/
#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include <Engine/DataTable.h>
#include "CCMTypes.h"
#include "CCMCameraFunctionLibrary.generated.h"

class ULevelSequence;
class ALevelSequenceActor;
/**
 * 
 */
UCLASS()
class CINEMATICCAMERAMANAGER_API UCCMCameraFunctionLibrary : public UBlueprintFunctionLibrary
{
	GENERATED_BODY()

public: 

	UFUNCTION(BlueprintCallable, BlueprintPure, meta = (WorldContext = "WorldContextObject"), Category = CCM)
	static class ACCMPlayerCameraManager* GetLocalCinematicCameraManager(const UObject* WorldContextObject);
	
	UFUNCTION(BlueprintCallable, meta = (WorldContext = "WorldContextObject"), Category = CCM)
	static	void TriggerCameraEvent(const UObject* WorldContextObject, FName CameraEventName);

	UFUNCTION(BlueprintCallable, meta = (WorldContext = "WorldContextObject"), Category = CCM)
	static	void TriggerTimedCameraEvent(const UObject* WorldContextObject, FName CameraEventName, float duration);

	UFUNCTION(BlueprintCallable, meta = (WorldContext = "WorldContextObject"), Category = CCM)
	static void StopCameraEvent(const UObject* WorldContextObject, FName CameraEventName);

	UFUNCTION(BlueprintCallable, meta = (WorldContext = "WorldContextObject"), Category = CCM)
	static void LockCameraOnActor(const UObject* WorldContextObject, AActor* ActorLookAt, ELockType locktype, float lockStrength = 5.f);

	UFUNCTION(BlueprintCallable, meta = (WorldContext = "WorldContextObject"), Category = CCM)
	static void StopLockingCameraOnActor(const UObject* WorldContextObject);

	UFUNCTION(BlueprintCallable, meta = (WorldContext = "WorldContextObject"), Category = CCM)
	static void LockCameraOnComponent(const UObject* WorldContextObject, USceneComponent* ComponentLookAt, ELockType locktype, float lockStrength);
	
	UFUNCTION(BlueprintCallable, meta = (WorldContext = "WorldContextObject"), Category = CCM)
	static void ResetCameraPosition(const UObject* WorldContextObject, bool bInstantReset = false);
	
	/** 
	 * Play a level sequence with optional actor bindings.
	 * @param WorldContextObject - World context for getting the camera manager
	 * @param Sequence - The level sequence to play
	 * @param TransformOrigin - Transform used as the origin point for the sequence (starting point)
	 * @param Bindings - Array of binding structs containing tag names and optional actors to bind
	 * @return The created LevelSequenceActor, or nullptr if creation failed
	 */
	UFUNCTION(BlueprintCallable, meta = (WorldContext = "WorldContextObject", AdvancedDisplay = "TransformOrigin,Bindings", AutoCreateRefTerm = "TransformOrigin,Bindings"), Category = CCM)
	static ALevelSequenceActor* PlayGameplaySequenceWithBinding(
		UObject* WorldContextObject,
		ULevelSequence* Sequence,
		const FTransform& TransformOrigin,
		const TArray<FCCMSequenceBinding>& Bindings);

	/** Stops the level sequence started with PlayGameplaySequenceWithBinding. No-op if none is playing. */
	UFUNCTION(BlueprintCallable, meta = (WorldContext = "WorldContextObject"), Category = CCM)
	static void StopSequence(const UObject* WorldContextObject);
};
