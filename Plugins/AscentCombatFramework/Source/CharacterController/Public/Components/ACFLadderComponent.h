// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "ACFActionTypes.h"
#include "Components/ActorComponent.h"
#include "CoreMinimal.h"
#include "GameplayTagContainer.h"

#include "ACFLadderComponent.generated.h"

class UACFCharacterMovementComponent;
class UACFAbilitySystemComponent;
class UACFEquipmentComponent;
class UMotionWarpingComponent;
class UCapsuleComponent;
class USkeletalMeshComponent;
class ACharacter;

DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnLadderClimbStarted);
DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnLadderClimbEnded);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnLadderSet, AActor*, NewLadder);

/**
 * Handles ACF ladder climbing mechanics using the ability system and motion warping.
 * Attach this component to a character alongside UACFAbilitySystemComponent and
 * UACFCharacterMovementComponent to enable interaction with ACF ladder actors.
 *
 * SETUP:
 * 1. Assign StartAbility and EndAbilityTag (gameplay tags matching your ladder climb abilities).
 * 2. Tune InteractDistance, FacingTolerance, BottomStartZOffset, TopStartZOffset.
 * 3. Call SetLadder() when the player approaches/overlaps a ladder actor.
 * 4. Call InitiateLadderClimb() from your interact input.
 * 5. Bind ClimbStartCompleted / ClimbEndCompleted to the corresponding ability notifications.
 *
 * LADDER ACTOR REQUIREMENTS:
 * The ladder actor must have:
 * - A SceneComponent named "ReachPoint-Bottom" (entry from bottom)
 * - A SceneComponent named "ReachPoint-Top" (entry from top)
 * - A SceneComponent named "DefaultSceneRoot" (used for distance check)
 * - A boolean variable named "HasValidPlacement" (Blueprint or C++ property)
 */
UCLASS(Blueprintable, ClassGroup = (ACF), meta = (BlueprintSpawnableComponent))
class CHARACTERCONTROLLER_API UACFLadderComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	UACFLadderComponent();

	// --- Delegates ---

	/** Fired when ladder climbing starts (after warp+ability is triggered). */
	UPROPERTY(BlueprintAssignable, Category = "ACF|Ladder")
	FOnLadderClimbStarted OnLadderClimbStarted;

	/** Fired when ladder climbing ends completely. */
	UPROPERTY(BlueprintAssignable, Category = "ACF|Ladder")
	FOnLadderClimbEnded OnLadderClimbEnded;

	/** Fired when the ladder reference is assigned. */
	UPROPERTY(BlueprintAssignable, Category = "ACF|Ladder")
	FOnLadderSet OnLadderSet;

	// --- Public API ---

	/**
	 * Assigns the ladder actor the character will interact with.
	 * Call this when the player enters a ladder trigger volume.
	 */
	UFUNCTION(BlueprintCallable, Category = "ACF|Ladder")
	void SetLadder(AActor* InLadder);

	/**
	 * Checks all preconditions and starts the climb sequence if valid.
	 * Equivalent to the Blueprint "InitiateLadderClimb" custom event.
	 */
	UFUNCTION(BlueprintCallable, Category = "ACF|Ladder")
	void InitiateLadderClimb();

	/**
	 * Directly starts climbing (motion warp + ability trigger).
	 * Equivalent to the Blueprint "Start Ladder Climb" custom event.
	 */
	UFUNCTION(BlueprintCallable, Category = "ACF|Ladder")
	void StartLadderClimb();

	/**
	 * Requests an exit from ladder climbing (triggers EndAbilityTag action).
	 * Equivalent to the Blueprint "Exit Ladder Climb" custom event.
	 */
	UFUNCTION(BlueprintCallable, Category = "ACF|Ladder")
	void ExitLadderClimb();

	/**
	 * Finalizes and cleans up the ladder climb state.
	 * Equivalent to the Blueprint "End Ladder Climb" custom event.
	 */
	UFUNCTION(BlueprintCallable, Category = "ACF|Ladder")
	void EndLadderClimb();

	/**
	 * Called when the start-climb ability montage has completed.
	 * Triggers the looping climb action.
	 */
	UFUNCTION(BlueprintCallable, Category = "ACF|Ladder")
	void ClimbStartCompleted();

	/**
	 * Called when the end-climb ability montage has completed.
	 * Re-enables movement mode and broadcasts OnLadderClimbEnded.
	 */
	UFUNCTION(BlueprintCallable, Category = "ACF|Ladder")
	void ClimbEndCompleted();

	/**
	 * Called when the entire climbing sequence is done.
	 * Unlocks actions and resets climb state.
	 */
	UFUNCTION(BlueprintCallable, Category = "ACF|Ladder")
	void ClimbingCompleted();

	/**
	 * Drives the mid-climb movement direction.
	 * Pass the vertical axis from your movement input (positive = up, negative = down).
	 * Equivalent to the Blueprint InputGraph climb axis handling.
	 */
	UFUNCTION(BlueprintCallable, Category = "ACF|Ladder")
	void HandleClimbInput(float AxisValue);

	/** Returns true if the character is currently on a ladder. */
	UFUNCTION(BlueprintPure, Category = "ACF|Ladder")
	bool IsLadderClimbing() const { return bIsClimbing; }

	/** Returns true if mid-climb movement is allowed (CanClimb state). */
	UFUNCTION(BlueprintPure, Category = "ACF|Ladder")
	bool CanClimb() const { return bCanClimb; }

	/** Returns the current ladder actor reference. */
	UFUNCTION(BlueprintPure, Category = "ACF|Ladder")
	AActor* GetCurrentLadder() const { return Ladder.Get(); }

	/** Returns true if the player entered the ladder from the bottom. */
	UFUNCTION(BlueprintPure, Category = "ACF|Ladder")
	bool IsPlayerAtBottom() const { return bPlayerAtBottom; }

protected:
	virtual void BeginPlay() override;

	// --- Configuration ---

	/**
	 * Maximum distance (XY plane) between the player and the ladder root for
	 * interaction to be valid. Maps to the Blueprint ErrorTolerance on EqualEqual_VectorVector.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|Ladder|Detection")
	float InteractDistance = 200.f;

	/**
	 * Maximum angle (degrees) between player forward and direction toward ladder
	 * for the facing check to pass. Matches Blueprint FacingTolerance variable.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|Ladder|Detection")
	float FacingTolerance = 45.f;

	/** Z offset applied to the motion warp target when entering from the bottom. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|Ladder|Positioning")
	double BottomStartZOffset = 0.0;

	/** Z offset applied to actor position when entering/exiting from the top. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|Ladder|Positioning")
	double TopStartZOffset = 0.0;

	/**
	 * Gameplay tag of the start-climb ability to trigger.
	 * The ability payload tag will be either Actions.LadderClimb.Up or Actions.LadderClimb.Down.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|Ladder|Abilities",
		meta = (Categories = "Actions"))
	FGameplayTag StartAbility;

	/**
	 * Gameplay tag of the end-climb ability to trigger when exiting the ladder.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|Ladder|Abilities",
		meta = (Categories = "Actions"))
	FGameplayTag EndAbilityTag;

	/**
	 * Tag sent as payload when the player climbs upward (entering from bottom).
	 * Default: Actions.LadderClimb.Up
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|Ladder|Abilities",
		meta = (Categories = "Actions"))
	FGameplayTag ClimbUpTag;

	/**
	 * Tag sent as payload when the player climbs downward (entering from top).
	 * Default: Actions.LadderClimb.Down
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|Ladder|Abilities",
		meta = (Categories = "Actions"))
	FGameplayTag ClimbDownTag;

	/**
	 * Tag sent as payload for the mid-climb loop action.
	 * Default: Actions.LadderClimb.Loop
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|Ladder|Abilities",
		meta = (Categories = "Actions"))
	FGameplayTag ClimbLoopTag;

	/** Name of the motion warp target used in the start/end climb montages. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|Ladder|MotionWarp")
	FName WarpTargetName = TEXT("ReachPoint");

	/** Name of the bottom reach point component on the ladder actor. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|Ladder|Components")
	FName ReachPointBottomName = TEXT("ReachPoint-Bottom");

	/** Name of the top reach point component on the ladder actor. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|Ladder|Components")
	FName ReachPointTopName = TEXT("ReachPoint-Top");

	/** Name of the root component on the ladder actor used for distance checks. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|Ladder|Components")
	FName LadderRootName = TEXT("DefaultSceneRoot");

	/** Name of the HasValidPlacement bool property on the ladder Blueprint. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|Ladder|Components")
	FName LadderValidPlacementPropertyName = TEXT("HasValidPlacement");

private:
	// --- Internal helpers ---

	void CacheOwnerComponents();

	/** Full pre-climb validation: ability state, movement mode, ladder validity, facing, distance. */
	bool LadderClimbChecks() const;

	/** XY distance check between player and ladder root within InteractDistance. */
	bool DistanceCheck() const;

	/** Checks that the player is facing the ladder within FacingTolerance degrees. */
	bool DirectionalCheck() const;

	/**
	 * Updates the MotionWarpingComponent warp target to the appropriate reach point
	 * on the current ladder (top or bottom based on bPlayerAtBottom).
	 */
	void MotionWarp();

	/**
	 * Locks actions, sheaths weapon, sets up position/motion-warp and triggers StartAbility.
	 * @param bAtBottom  True if the player is entering from the bottom of the ladder.
	 */
	void InternalStart(bool bAtBottom);

	/**
	 * Triggers the looping climb action after the enter montage has finished.
	 * @param AxisValue  Vertical input: > 0 climbs up, < 0 climbs down.
	 */
	void InternalClimb(float AxisValue);

	/** Resets climb state, repositions the character and triggers EndAbilityTag. */
	void InternalExit();

	/** Finds a SceneComponent on the ladder actor by FName. */
	USceneComponent* FindLadderComponentByName(FName ComponentName) const;

	/** Reads HasValidPlacement from the ladder Blueprint via property reflection. */
	bool GetLadderHasValidPlacement() const;

	/** Returns the reach point component (top or bottom) on the ladder actor. */
	USceneComponent* GetLadderReachPoint(bool bBottom) const;

	// --- Cached component references (filled in BeginPlay) ---

	UPROPERTY()
	TObjectPtr<AActor> Ladder;

	UPROPERTY()
	TObjectPtr<UACFCharacterMovementComponent> PlayerCharacterMovement;

	UPROPERTY()
	TObjectPtr<USkeletalMeshComponent> PlayerSkeletalMesh;

	UPROPERTY()
	TObjectPtr<UCapsuleComponent> PlayerCapsule;

	UPROPERTY()
	TObjectPtr<UACFAbilitySystemComponent> AbilityComponent;

	UPROPERTY()
	TObjectPtr<UMotionWarpingComponent> MotionWarpingComp;

	// --- Runtime state ---

	bool bIsClimbing = false;
	bool bCanClimb = false;
	bool bIsSprinting = false;
	bool bPlayerAtBottom = false;
};
