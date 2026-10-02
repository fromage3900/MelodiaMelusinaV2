// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CCMTypes.h"
#include "Camera/PlayerCameraManager.h"
#include "CoreMinimal.h"
#include <Engine/DataTable.h>
#include <GameFramework/Actor.h>

#include "ACFCameraPointComponent.h"
#include "CCMPlayerCameraManager.generated.h"

class APawn;
class AActor;
class ALevelSequenceActor;
class USceneComponent;
class UACFCameraPointComponent;

/**
 * Delegate that is called when a camera sequence starts.
 * @param cameraSequence - The name of the camera sequence that started.
 */
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnCameraSequenceStarted, const FName&, cameraSequence);

/**
 * Delegate that is called when a camera sequence ends.
 * @param cameraSequence - The name of the camera sequence that ended.
 */
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnCameraSequenceEnded, const FName&, cameraSequence);

/**
 * Player Camera Manager class that handles the camera sequence, movements, and events.
 * Inherits from APlayerCameraManager to manage the player's camera during gameplay.
 */
UCLASS()
class CINEMATICCAMERAMANAGER_API ACCMPlayerCameraManager : public APlayerCameraManager {
	GENERATED_BODY()

public:
	// Default constructor for the camera manager class
	ACCMPlayerCameraManager();

protected:
	/** Called when the game starts or when the actor is spawned */
	virtual void BeginPlay() override;

	/** Function to update the camera state every frame */
	void UpdateCamera(float deltaTime);

	/** Data table to store various camera movements (should be populated via Editor) */
	UPROPERTY(EditAnywhere, Category = "CCM Camera")
	UDataTable* CameraMovements;

	/** Upper pitch limit for camera lock (in degrees) */
	UPROPERTY(EditAnywhere, Category = "CCM Camera")
	float CameraLockPitchUpperLimit = 75.f;

	/** Lower pitch limit for camera lock (in degrees) */
	UPROPERTY(EditAnywhere, Category = "CCM Camera")
	float CameraLockPitchLowerLimit = 35.f;

	/** Offset for global camera lock */
	UPROPERTY(EditAnywhere, Category = "CCM Camera")
	FVector2D GlobalLockOffset = FVector2D();

	/** Class type for the camera actor to use */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "CCM Camera")
	TSubclassOf<ACameraActor> CameraActorClass;

	/** Holds the final camera movement settings (adjustable in Blueprint) */
	UPROPERTY(BlueprintReadOnly, Category = "CCM Camera")
	FCCMCameraMovementSettings FinalMov;

	/** Reference to the player's camera component */
	UPROPERTY(BlueprintReadOnly, Category = "CCM Camera")
	class UCameraComponent* playerCamera;

	/** Reference to the spring arm component for the camera */
	UPROPERTY(BlueprintReadOnly, Category = "CCM Camera")
	class USpringArmComponent* cameraBoom;

	/** If true, the camera will follow the player character */
	UPROPERTY(EditDefaultsOnly, Category = "CCM Camera")
	bool bFollowPlayer = false;

	/** Speed at which the camera will follow the player when the player moves */
	UPROPERTY(EditDefaultsOnly, meta = (EditCondition = "bFollowPlayerWhenMoving"), Category = "CCM Camera")
	float FollowSpeed = 1.f;

	/** Maximum angle difference at which the camera will follow the player */
	UPROPERTY(EditDefaultsOnly, meta = (EditCondition = "bFollowPlayerWhenMoving"), Category = "CCM Camera")
	float MaxFollowDeltaAngle = 180.f;

	/** Debugging setting to print the delta angle when following the player */
	UPROPERTY(EditDefaultsOnly, meta = (EditCondition = "bFollowPlayerWhenMoving"), Category = "CCM Camera")
	bool bPrintDebugDeltaAngle = false;

	/** Flag indicating if a camera sequence is currently playing */
	UPROPERTY()
	bool bIsPlayingSequence = false;

	/** The current camera actor playing a sequence */
	UPROPERTY()
	TObjectPtr<class ACameraActor> sequenceCameraActor;

	/** Current sequence settings */
	UPROPERTY()
	FCurrentSequence currentSequence;

public:


	/** Event that gets triggered when a camera sequence starts */
	UPROPERTY(BlueprintAssignable, Category = "CCM")
	FOnCameraSequenceStarted OnCameraSequenceStarted;

	/** Event that gets triggered when a camera sequence ends */
	UPROPERTY(BlueprintAssignable, Category = "CCM")
	FOnCameraSequenceEnded OnCameraSequenceEnded;

	/** Trigger a camera event by name (e.g., cinematic sequences, cutscenes) */
	UFUNCTION(BlueprintCallable, Category = "CCM")
	void TriggerCameraEvent(FName CameraEventName);

	/** Trigger a timed camera event that lasts for a specified duration */
	UFUNCTION(BlueprintCallable, Category = "CCM")
	void TriggerTimedCameraEvent(FName CameraEventName, float duration);

	/** Stop a camera event by its name */
	UFUNCTION(BlueprintCallable, Category = "CCM")
	void StopCameraEvent(FName CameraEventName);

	/** Reset the camera position (instant or gradual) */
	UFUNCTION(BlueprintCallable, Category = "CCM")
	void ResetCameraPosition(bool bInstantReset = false);

	/** Lock the camera on an actor with a specified lock type and strength */
	UFUNCTION(BlueprintCallable, Category = "CCM")
	void LockCameraOnActor(class AActor* ActorLookAt, ELockType lockType, float lockStrength = 5.f);

	/** Lock the camera on a specific scene component with a specified lock type and strength */
	UFUNCTION(BlueprintCallable, Category = "CCM")
	void LockCameraOnComponent(class USceneComponent* ComponentToLookAt, ELockType lockType, float lockStrength = 5.f);

	/** Stop locking the camera on the current actor */
	UFUNCTION(BlueprintCallable, Category = "CCM")
	void StopLookingActor();

	UFUNCTION(BlueprintCallable, Category = "CCM")
	void PlayCameraBlend(AActor* TargetActor, const FGameplayTag& ComponentTag, float BlendTime = 1.f,
		TEnumAsByte<EViewTargetBlendFunction> BlendFunc = VTBlend_Linear,
		float BlendExp = 2.f,
		bool bLockOutgoing = false);

	/** Enable or disable camera following the player with an optional follow speed */
	UFUNCTION(BlueprintCallable, Category = "CCM")
	void SetFollowPlayer(bool bFollow, float inFollowSpeed = 1.f);

	/** Update references to the player's camera and boom */
	void UpdateCameraReferences();

	/** Trigger a camera sequence by event name and specify the camera actor owner */
	UFUNCTION(BlueprintCallable, Category = "CCM")
	void TriggerCameraSequence(AActor* cameraOwner, FName CameraEventName);

	/**
	 * Play a level sequence with actor bindings.
	 * Only one sequence can play at a time; starting a new one stops the previous.
	 * The reference to the sequence in progress is stored in CurrentLevelSequenceActor.
	 * @param Sequence - The level sequence to play
	 * @param TransformOrigin - Transform used as the origin point for the sequence (starting point)
	 * @param Bindings - Array of binding structs containing tag names and optional actors to bind
	 * @return The created LevelSequenceActor, or nullptr if creation failed
	 */
	UFUNCTION(BlueprintCallable, Category = "CCM", meta = (AutoCreateRefTerm = "TransformOrigin,Bindings"))
	ALevelSequenceActor* PlayGameplaySequenceWithBinding(
		ULevelSequence* Sequence,
		const FTransform& TransformOrigin,
		const TArray<FCCMSequenceBinding>& Bindings);

	/** Reference to the level sequence currently playing (max one at a time). Cleared when stopped or when the sequence finishes. */
	UPROPERTY(BlueprintReadOnly, Category = "CCM")
	TObjectPtr<ALevelSequenceActor> CurrentLevelSequenceActor = nullptr;

	/** Stops the sequence started with PlayGameplaySequenceWithBinding and clears CurrentLevelSequenceActor. No-op if none is playing. */
	UFUNCTION(BlueprintCallable, Category = "CCM")
	void StopSequence();

	/** Stop the current camera sequence */
	UFUNCTION(BlueprintCallable, Category = "CCM")
	void StopCurrentCameraSequence();

	/**
	 * Force-stops and deactivates the camera point currently activated via BlendToPoint/PlayCameraBlend
	 * (halting any orbit/crane/pan movement preset) and clears the internal reference.
	 * No-op if no camera point is active.
	 */
	UFUNCTION(BlueprintCallable, Category = "CCM")
	void DeactivateCurrentCameraPoint();

	/** Add a sequence event modifier to modify the current sequence behavior */
	UFUNCTION(BlueprintCallable, Category = "CCM")
	void AddSequenceEventModifier(const FCCMSequenceEvent& modifier);

	/** Remove a sequence event modifier */
	UFUNCTION(BlueprintCallable, Category = "CCM")
	void RemoveSequenceEventModifier(const FCCMSequenceEvent& modifier);

	/** Override the camera references (e.g., to set a new camera or boom) */
	UFUNCTION(BlueprintCallable, Category = "CCM")
	void OverrideCameraReferences(class UCameraComponent* inPlayerCamera, class USpringArmComponent* inCameraBoom);

	/** Binds the camera manager to the pawn change event */
	UFUNCTION(BlueprintCallable, Category = "CCM")
	void BindEvents();

	/*
	UFUNCTION(BlueprintCallable, Category = "CCM")
	void PlayCinematicCameraAnim(UCameraAnimationSequence* CameraAnimAsset, USceneComponent* ReferencePoint);*/


	void BlendToPoint(AActor* OwnerWithPoints,
		FGameplayTag CameraTag,
		float BlendTime = 1.f,
		TEnumAsByte<EViewTargetBlendFunction> BlendFunc = VTBlend_Linear,
		float BlendExp = 2.f,
		bool bLockOutgoing = false);

private:

	/**
	* Finds a camera point component by tag on the actor or its child actors.
	* @param OwnerWithPoints - Actor to search
	* @param CameraTag - Tag to match
	* @param OutViewTarget - Output actor to use as view target for SetViewTargetWithBlend
	* @return Camera point component if found, nullptr otherwise
	*/
	UACFCameraPointComponent* ResolveCameraPoint(AActor* OwnerWithPoints, const FGameplayTag& CameraTag, AActor*& OutViewTarget) const;

	void MoveCamera(float deltaTime);

	void SetCameraSequenceData();

	void UpdateLockOnTarget(float deltaTime);

	void UpdateCameraSequence(float deltaTime);

	void LockCameraOnPosition(FVector localPos, float deltaTime);

	void StoreData();
	void RecoverStoredData();

	UPROPERTY()
	TMap<FName, FCCMCameraMovementSettings> currentlyActiveCameraEvents;

	UPROPERTY()
	TObjectPtr<APawn> playerCharacter;

	UPROPERTY()
	FVector originalPos;

	UPROPERTY()
	float originalFov;

	UPROPERTY()
	FRotator _originalRelativeRot;

	UPROPERTY()
	FVector _localPos;

	UPROPERTY()
	float _localFov;

	UPROPERTY()
	float _localTimeDilatation;

	UPROPERTY()
	ETargetLockType _localIsLockingAt;

	UPROPERTY()
	bool _localStrafing;

	UPROPERTY()
	float _lockStrength;

	UPROPERTY()
	bool _localOrientToMov;

	UPROPERTY()
	float _localArmLength;

	UPROPERTY()
	ETargetLockType targetLockType = ETargetLockType::ENone;

	UPROPERTY()
	ELockType currentLockType;

	UPROPERTY()
	TObjectPtr<AActor> localtarget;

	UPROPERTY()
	TObjectPtr<USceneComponent> localtargetComponent;

	UPROPERTY()
	TObjectPtr<UACFCameraPointComponent> currentCameraComp;

	UFUNCTION()
	void HandlePawnChanged(APawn* newPawn);

	UFUNCTION()
	void OnLevelSequenceFinished();

	void FollowPlayer(float deltaTime);

	UPROPERTY()
	FCCMCameraSequenceSettings currentSequenceSettings;

	UPROPERTY()
	bool bFollowPlayerWhenMoving;

	// Battle camera managment

	UPROPERTY(Transient)
	ACameraActor* CameraStubA = nullptr;

	UPROPERTY(Transient)
	ACameraActor* CameraStubB = nullptr;

	UPROPERTY(Transient)
	ACameraActor* LastViewTarget = nullptr;

	UPROPERTY(Transient)
	bool bIsUsingA = false;



};
