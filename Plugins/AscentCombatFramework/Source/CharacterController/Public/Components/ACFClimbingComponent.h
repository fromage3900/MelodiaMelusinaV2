// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "Engine/EngineTypes.h"
#include "Engine/HitResult.h"
#include "CollisionQueryParams.h"
#include "GameplayTagContainer.h"
#include "InputAction.h"
#include "InputActionValue.h"

#include "ACFClimbingComponent.generated.h"

class UACFCharacterMovementComponent;
class UACFAnimInstance;
class UAnimMontage;
class UACFAbilitySystemComponent;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnClimbingStateChanged, bool, bIsClimbing);
DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnClimbTransitionRequested);

/**
 * Handles wall climbing mechanics.
 * Add this component to a character alongside UACFCharacterMovementComponent
 * to enable surface climbing, ledge detection and ledge climb-up.
 */
UCLASS(Blueprintable, ClassGroup = (ACF), meta = (BlueprintSpawnableComponent))
class CHARACTERCONTROLLER_API UACFClimbingComponent : public UActorComponent {
	GENERATED_BODY()

public:
	UACFClimbingComponent();

	/** Called when climbing state changes (started or stopped). */
	UPROPERTY(BlueprintAssignable, Category = "ACF|Climbing")
	FOnClimbingStateChanged OnClimbingStateChanged;

	/** Fired when enter climbing is requested and Blueprint controls the enter transition. */
	UPROPERTY(BlueprintAssignable, Category = "ACF|Climbing")
	FOnClimbTransitionRequested OnEnterClimbRequested;

	/** Fired when exit climbing is requested and Blueprint controls the exit transition. */
	UPROPERTY(BlueprintAssignable, Category = "ACF|Climbing")
	FOnClimbTransitionRequested OnExitClimbRequested;

	/** Attempts to start climbing a nearby surface. */
	UFUNCTION(BlueprintCallable, Category = "ACF|Climbing")
	bool TryClimbing();

	UFUNCTION(BlueprintCallable, Category = "ACF|Climbing")
	void FinalizePendingLedgeExit();

	UFUNCTION(BlueprintCallable, Category = "ACF|Climbing")
	void LedgeExit();

	UFUNCTION(Server, Reliable)
	void ServerTryClimbing();

	/** Cancels the current climbing action. */
	UFUNCTION(Server, Reliable, BlueprintCallable, Category = "ACF|Climbing")
	void CancelClimbing();

	/** Requests to exit climbing (bind this to any input action you want). */
	UFUNCTION(Server, Reliable, BlueprintCallable, Category = "ACF|Climbing")
	void RequestExitClimbing();

	/** Call from BP to complete enter-climb when using Blueprint-controlled enter transitions. */
	UFUNCTION(Server, Reliable, BlueprintCallable, Category = "ACF|Climbing")
	void ConfirmEnterClimb();

	/**
	 * Call from enter-climb ability when the character must physically attach to the wall and enter climbing movement.
	 * Refreshes wall hits / surface normal, clears pending-enter, then sets MOVE_Custom + CMOVE_Climbing.
	 * Must run where the ability runs (typically server only): movement replication is handled by CharacterMovement, no extra RPC here.
	 */
	UFUNCTION(BlueprintCallable, Category = "ACF|Climbing")
	void BeginClimbingFromAbility();

	UFUNCTION(BlueprintCallable, Category = "ACF|Climbing")
	void HandleEnterClimbMontageEnded(bool bInterrupted);

	/** Call from BP to complete exit-climb when using Blueprint-controlled exit transitions. */
	UFUNCTION(Server, Reliable, BlueprintCallable, Category = "ACF|Climbing")
	void ConfirmExitClimbing();

	/**
	 * Call this from your input handling and pass the triggered input action.
	 * If it matches ExitClimbingInputAction, climbing exit is requested.
	 */
	UFUNCTION(BlueprintCallable, Category = "ACF|Climbing")
	void HandleExitClimbingInputAction(const UInputAction* TriggeredInputAction);

	/** Returns true if the character is currently climbing. */
	UFUNCTION(BlueprintPure, Category = "ACF|Climbing")
	bool IsClimbing() const;

	/** Returns the surface normal of the currently climbed surface. */
	UFUNCTION(BlueprintPure, Category = "ACF|Climbing")
	FVector GetClimbSurfaceNormal() const;

	/**
	 * Returns the climbing-adjusted forward direction for movement input.
	 * When climbing, forward is along the surface (up direction).
	 */
	UFUNCTION(BlueprintPure, Category = "ACF|Climbing")
	FVector GetClimbingForwardDirection() const;

	/**
	 * Returns the climbing-adjusted right direction for movement input.
	 * When climbing, right is along the surface (horizontal direction).
	 */
	UFUNCTION(BlueprintPure, Category = "ACF|Climbing")
	FVector GetClimbingRightDirection() const;

	UFUNCTION(BlueprintPure, Category = "ACF|Climbing")
	FVector GetWarpLocation() const { return WarpLocation; };

	// --- Interface for ACFCharacterMovementComponent delegation ---

	/** Called from movement component's PhysCustom when in climbing mode. */
	void PhysClimbing(float DeltaTime, int32 Iterations);

	/** Called from movement component's OnMovementUpdated to transition into climbing. */
	void HandleMovementUpdated(float DeltaSeconds, const FVector& OldLocation, const FVector& OldVelocity);

	/** Called when movement mode changes, handles climbing enter/exit logic. */
	void HandleMovementModeChanged(EMovementMode PreviousMovementMode, uint8 PreviousCustomMode);

	/** Called each tick while climbing to update wall hit data. */
	void TickClimbing();

	/** Returns max climbing speed. */
	UFUNCTION(BlueprintPure, Category = "ACF|Climbing")
	float GetMaxClimbingSpeed() const { return MaxClimbingSpeed; }

	/** Returns max climbing acceleration. */
	UFUNCTION(BlueprintPure, Category = "ACF|Climbing")
	float GetMaxClimbingAcceleration() const { return MaxClimbingAcceleration; }

	/** Returns whether the character wants to climb. */
	UFUNCTION(BlueprintPure, Category = "ACF|Climbing")
	bool WantsToClimb() const { return bWantsToClimb; }



protected:
	virtual void BeginPlay() override;

	// --- Climbing Configuration ---

	/** If enabled, character automatically tries to start climbing on valid climbable walls. */
	UPROPERTY(Category = "ACF|Climbing", EditAnywhere)
	bool bAutoClimb = true;

	/** If enabled, auto-climb is allowed only while falling/in air. */
	UPROPERTY(Category = "ACF|Climbing", EditAnywhere, meta = (EditCondition = "bAutoClimb"))
	bool bAutoClimbOnlyWhenFalling = true;

	/** Minimum forward input required to auto-climb (prevents immediate reattach on exit). */
	UPROPERTY(Category = "ACF|Climbing", EditAnywhere, meta = (ClampMin = "0.0", ClampMax = "1.0", EditCondition = "bAutoClimb"))
	float AutoClimbForwardInputThreshold = 0.75f;

	/** After manual exit, require forward input release before auto-climb can re-trigger. */
	UPROPERTY(Category = "ACF|Climbing", EditAnywhere, meta = (EditCondition = "bAutoClimb"))
	bool bRequireForwardReleaseAfterExit = true;

	UPROPERTY(Category = "ACF|Climbing|Detection", EditAnywhere)
	int32 CollisionCapsuleRadius = 50;

	UPROPERTY(Category = "ACF|Climbing|Detection", EditAnywhere)
	int32 CollisionCapsuleHalfHeight = 72;

	/** Forward distance used to detect climbable surfaces. */
	UPROPERTY(Category = "ACF|Climbing|Detection", EditAnywhere, meta = (ClampMin = "10.0", ClampMax = "500.0"))
	float ClimbDetectionDistance = 100.f;

	UPROPERTY(Category = "ACF|Climbing|Detection", EditAnywhere, meta = (ClampMin = "1.0", ClampMax = "75.0"))
	float MinHorizontalDegreesToStartClimbing = 25;

	UPROPERTY(Category = "ACF|Climbing|Movement", EditAnywhere, meta = (ClampMin = "10.0", ClampMax = "500.0"))
	float MaxClimbingSpeed = 120.f;

	UPROPERTY(Category = "ACF|Climbing|Movement", EditAnywhere, meta = (ClampMin = "10.0", ClampMax = "2000.0"))
	float MaxClimbingAcceleration = 380.f;

	UPROPERTY(Category = "ACF|Climbing|Movement", EditAnywhere, meta = (ClampMin = "0.0", ClampMax = "3000.0"))
	float BrakingDecelerationClimbing = 550.f;

	UPROPERTY(Category = "ACF|Climbing|Movement", EditAnywhere, meta = (ClampMin = "1.0", ClampMax = "12.0"))
	int32 ClimbingRotationSpeed = 6;

	UPROPERTY(Category = "ACF|Climbing|Movement", EditAnywhere, meta = (ClampMin = "0.0", ClampMax = "60.0"))
	float ClimbingSnapSpeed = 4.f;

	UPROPERTY(Category = "ACF|Climbing|Movement", EditAnywhere, meta = (ClampMin = "0.0", ClampMax = "80.0"))
	float DistanceFromSurface = 45.f;

	/** Visual-only mesh offset along character forward while climbing (signed, in cm). */
	UPROPERTY(Category = "ACF|Climbing|Visual", EditAnywhere, meta = (ClampMin = "-100.0", ClampMax = "100.0"))
	float MeshForwardOffsetOnClimbing = 9.f;

	/** Distance from capsule bottom to walkable floor required to auto-exit when climbing down. */
	UPROPERTY(Category = "ACF|Climbing|Exit", EditAnywhere, meta = (ClampMin = "0.0", ClampMax = "150.0"))
	float GroundProximityExitDistance = 8.f;

	/** Prevent immediate reattach after an explicit climbing exit request. */
	UPROPERTY(Category = "ACF|Climbing|Exit", EditAnywhere, meta = (ClampMin = "0.0", ClampMax = "1.0"))
	float ReattachDelayAfterExitRequest = 0.2f;

	UPROPERTY(Category = "ACF|Climbing|Exit", EditAnywhere)
	FGameplayTag ExitClimbingTag;

	UPROPERTY(Category = "ACF|Climbing|Enter", EditAnywhere)
	FGameplayTag EnterClimbingTag;

	UPROPERTY(Category = "ACF|Abilities", EditAnywhere)
	TArray<FGameplayTag> CheckClimbingDuringAbilities;

	/**
	 * Maximum allowed corner angle between current wall normal and predicted side wall normal.
	 * Higher values allow sharper corners before forcing exit.
	 */
	UPROPERTY(Category = "ACF|Climbing|Corner", EditAnywhere, meta = (ClampMin = "0.0", ClampMax = "89.0"))
	float MaxClimbSurfaceTiltAngle = 30.f;

	/** Anticipation margin in degrees for corner exit (higher = exits earlier). */
	UPROPERTY(Category = "ACF|Climbing|Corner", EditAnywhere, meta = (ClampMin = "0.0", ClampMax = "30.0"))
	float ClimbSurfaceExitAnticipationAngle = 5.f;

	/** How far ahead (in cm) to probe wall normal while climbing for early corner exit. */
	UPROPERTY(Category = "ACF|Climbing|Corner", EditAnywhere, meta = (ClampMin = "0.0", ClampMax = "120.0"))
	float ClimbSurfaceExitLookAheadDistance = 30.f;

	/** Forward offset (in cm) applied before corner-angle probe to avoid tiny seam/stair false positives. */
	UPROPERTY(Category = "ACF|Climbing|Corner", EditAnywhere, meta = (ClampMin = "0.0", ClampMax = "120.0"))
	float ClimbCornerCheckForwardOffset = 20.f;

	/** Grace time to keep climbing when wall normal is temporarily lost at seams/edges. */
	UPROPERTY(Category = "ACF|Climbing|Detection", EditAnywhere, meta = (ClampMin = "0.0", ClampMax = "0.5"))
	float LostSurfaceNormalGraceTime = 0.12f;

	/** Input action that requests climbing exit (user configurable). */
	UPROPERTY(Category = "ACF|Climbing|Exit", EditAnywhere)
	TObjectPtr<UInputAction> ExitClimbingInputAction = nullptr;

	/** Forward trace distance (in cm) used to detect ledge edge sooner/later. */
	UPROPERTY(Category = "ACF|Climbing|Exit", EditAnywhere, meta = (ClampMin = "1.0", ClampMax = "500.0"))
	float LedgeEdgeTraceDistance = 150.f;

	UPROPERTY(Category = "ACF|Climbing|Ledge", EditAnywhere)
	float LedgeClimbTargetVerticalOffset = 100.f;

	UPROPERTY(Category = "ACF|Climbing|Ledge", EditAnywhere, meta = (ClampMin = "0.0", ClampMax = "200.0"))
	float LedgeClimbTargetForwardOffset = 80.f;

	/** Additional forward offset applied at ledge exit end (after montage/fallback). */
	UPROPERTY(Category = "ACF|Climbing|Ledge", EditAnywhere, meta = (ClampMin = "-100.0", ClampMax = "200.0"))
	float LedgeExitForwardOffset = 20.f;

	UPROPERTY(Category = "ACF|Climbing|Ledge", EditAnywhere, meta = (ClampMin = "-100.0", ClampMax = "200.0"))
	float LedgeExitVerticalOffset = -98.f;

	/**
	 * Object types that are considered climbable.
	 * Add your custom Object Type here (e.g. "Climbable") and set your meshes
	 * to that Object Type in their Collision settings.
	 * If empty, falls back to WorldStatic.
	 */
	UPROPERTY(Category = "ACF|Climbing|Detection", EditAnywhere, BlueprintReadWrite)
	TArray<TEnumAsByte<EObjectTypeQuery>> ClimbableObjectTypes;

	/** If true, character movement is locked while EnterClimbMontage is playing. */
	UPROPERTY(Category = "ACF|Climbing|Enter", EditAnywhere)
	bool bLockMovementDuringEnterClimbMontage = true;


	/** Forward world offset applied before EnterClimbMontage starts. */
	UPROPERTY(Category = "ACF|Climbing|Enter", EditAnywhere, meta = (ClampMin = "-100.0", ClampMax = "100.0"))
	float EnterClimbForwardOffset = 0.f;

	/** Vertical world offset applied before EnterClimbMontage starts. */
	UPROPERTY(Category = "ACF|Climbing|Enter", EditAnywhere, meta = (ClampMin = "-100.0", ClampMax = "100.0"))
	float EnterClimbVerticalOffset = 0.f;

	/** Enables all climbing debug draw helpers (lines/spheres/capsules). */
	UPROPERTY(Category = "ACF|Climbing|Debug", EditAnywhere)
	bool bEnableClimbingDebugDraw = false;


private:
	void TryBindExitClimbingInputAction();

	FCollisionObjectQueryParams BuildClimbObjectQueryParams() const;
	FCollisionObjectQueryParams BuildFloorObjectQueryParams() const;

	void SweepAndStoreWallHits();

	bool IsWallClimbable(const FHitResult& Hit, const FVector& Forward) const noexcept;

	bool EyeHeightTrace(float TraceDistance) const;

	bool IsFacingSurface(float Steepness) const;

	void ComputeSurfaceInfo();

	void ComputeClimbingVelocity(float DeltaTime);

	bool ShouldStopClimbing();

	void StopClimbing(float DeltaTime, int32 Iterations);

	void MoveAlongClimbingSurface(float DeltaTime);

	void SnapToClimbingSurface(float DeltaTime) const;

	FQuat GetClimbingRotation(float DeltaTime) const;

	bool ClimbDownToFloor() const;

	bool TryClimbUpLedge();

	bool HasReachedEdge() const;

	bool CanMoveToLedgeClimbLocation(FVector* OutLedgeClimbLocation = nullptr) const;



	bool IsLocationWalkable(const UWorld* World, const FVector& LocationToCheck, float WalkableHeight, const FCollisionQueryParams& QueryParams) const;

	FHitResult CheckFloor(const UWorld* World, const FVector& Location, float MaxDistance, const FCollisionQueryParams& QueryParams) const;

	bool GetPredictedClimbingNormal(FVector& OutPredictedNormal) const;
	void ApplyClimbingMeshOffset();
	void RestoreClimbingMeshOffset();
	void PerformImmediateExitClimbing();

	void ApplyClimbingMovementModeFromAbilityInternal();

	UPROPERTY()
	TObjectPtr<UACFCharacterMovementComponent> MovementComponent;

	UPROPERTY()
	TObjectPtr<UACFAbilitySystemComponent> AbilitySystem;

	UPROPERTY()
	TObjectPtr<UACFAnimInstance> AnimInstance;

	TArray<FHitResult> CurrentWallHits;
	FCollisionQueryParams ClimbQueryParams;

	UPROPERTY(Replicated)
	FVector CurrentClimbingNormal;

	FVector CurrentClimbingPosition;

	// Throttle how often we do expensive wall sweeps while climbing.
	UPROPERTY(EditDefaultsOnly, Category = "ACF|Climbing", meta = (ClampMin = "0.0", ClampMax = "0.2"))
	float WallHitSweepInterval = 0.033f; // ~30Hz

	float LastWallHitSweepTime = -1000.f;
	float LastValidClimbingNormalTime = -1000.f;
	float LastExitRequestTime = -1000.f;

	bool bHasPendingLedgeExit = false;
	FVector PendingLedgeExitLocation = FVector::ZeroVector;
	FVector PendingLedgeExitTriggerLocation = FVector::ZeroVector;
	bool bHasPendingEnterClimb = false;
	bool bPrevCanMoveBeforeEnterMontage = true;

	UFUNCTION()
	void OnExitClimbingActionTriggered(const FInputActionValue& InputValue);

	bool bExitInputActionBound = false;
	bool bExitClimbingRequested = false;
	bool bWantsToClimb = false;
	bool bHasReleasedForwardSinceExit = true;
	FVector DefaultMeshRelativeLocation = FVector::ZeroVector;
	bool bHasStoredMeshRelativeLocation = false;
	FVector WarpLocation = FVector::ZeroVector;
};
