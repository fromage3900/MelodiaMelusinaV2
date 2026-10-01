// // Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "ACFActionTypes.h"
#include "ACFCCTypes.h"
#include "CoreMinimal.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameplayTagContainer.h"
#include <ActiveGameplayEffectHandle.h>

#include "ACFCharacterMovementComponent.generated.h"

class UACFAnimInstance;
class UACFClimbingComponent;
class ACharacter;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnLocomotionStateChanged, ELocomotionState, State);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnMoveStanceChanged, FGameplayTag, stance);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnRotationModeChanged, ERotationMode, rotMode);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnMovementModeChanged, EMovementMode, newMovementMode);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnAimChanged, bool, isAiming);



/**
 *	The base character movement component class used by this project.
 */
UCLASS()
class CHARACTERCONTROLLER_API UACFCharacterMovementComponent : public UCharacterMovementComponent {
	GENERATED_BODY()
public:
	UACFCharacterMovementComponent(const FObjectInitializer& ObjectInitializer);

	/** Called when the locomotion state changes. */
	UPROPERTY(BlueprintAssignable)
	FOnLocomotionStateChanged OnLocomotionStateChanged;

	/** Called when the target locomotion state changes. */
	UPROPERTY(BlueprintAssignable)
	FOnLocomotionStateChanged OnTargetLocomotionStateChanged;

	/** Called when the movement stance changes. */
	UPROPERTY(BlueprintAssignable)
	FOnMoveStanceChanged OnLocomotionStanceChanged;

	/** Called when the rotation mode changes. */
	UPROPERTY(BlueprintAssignable)
	FOnRotationModeChanged OnRotationModeChanged;

	/** Called when the aiming state changes. */
	UPROPERTY(BlueprintAssignable)
	FOnAimChanged OnAimChanged;

	/** Called when the movement mode changes (e.g. walking, swimming, flying). */
	UPROPERTY(BlueprintAssignable)
	FOnMovementModeChanged OnMovementModeChangedEvent;
	/**
	 * Returns the character's current max movement speed.
	 * @return The max movement speed based on the current locomotion state.
	 */
	UFUNCTION(BlueprintPure, Category = ACF)
	float GetCharacterMaxSpeed() const { return CharacterMaxSpeed; }

	/**
	 * Returns the current active movement stance.
	 * @return The currently active movement stance.
	 */
	UFUNCTION(BlueprintPure, Category = ACF)
	FGameplayTag GetCurrentLocomotionStance() const { return currentMovestance; }

	/**
	 * Checks if the character is currently strafing.
	 * @return True if the character is in strafe rotation mode.
	 */
	UFUNCTION(BlueprintPure, Category = ACF)
	bool IsCharacterStrafing() const { return RotationMode == ERotationMode::EStrafing; }

	/**
	 * Checks if the character is currently sprinting.
	 * @return True if the character's target locomotion state is sprint.
	 */
	UFUNCTION(BlueprintPure, Category = ACF)
	bool IsSprinting() const { return targetLocomotionState.State == ELocomotionState::ESprint; };

	/**
	 * Gets the current rotation mode of the character.
	 * @return The active rotation mode.
	 */
	UFUNCTION(BlueprintPure, Category = ACF)
	ERotationMode GetRotationMode() const { return RotationMode; };

	/**
	 * Checks if the character is allowed to move.
	 * @return True if movement is currently permitted.
	 */
	UFUNCTION(BlueprintPure, Category = ACF)
	bool GetCanMove() const { return bCanMove; };

	/**
	 * Sets whether the character can move or not.
	 * @param inCanMove Whether movement should be allowed.
	 */
	UFUNCTION(Server, Reliable, BlueprintCallable, Category = ACF)
	void SetCanMove(bool inCanMove);

	/**
	 * Gets the current locomotion state of the character.
	 * @return The current locomotion state enum.
	 */
	UFUNCTION(BlueprintPure, Category = ACF)
	FORCEINLINE ELocomotionState GetCurrentLocomotionState() const
	{
		return currentLocomotionState;
	}

	/**
	 * Returns the character's max movement speed based on a specified locomotion state.
	 * @param State The locomotion state to query.
	 * @return The max movement speed associated with the given state.
	 */
	UFUNCTION(BlueprintCallable, Category = ACF)
	float GetCharacterMaxSpeedByState(ELocomotionState State);

	/**
	 * Returns the character's max swim speed based on a specified locomotion state.
	 * @param State The locomotion state to query.
	 * @return The max swim speed associated with the given state.
	 */
	UFUNCTION(BlueprintCallable, Category = ACF)
	float GetCharacterMaxSwimSpeedByState(ELocomotionState State);

	/**
	 * Sets the rotation mode of the character.
	 * Applies immediately on the local machine for responsiveness and sends a Server RPC
	 * to keep RotationMode in sync. Without server authorisation the replicated value would
	 * overwrite the local change every replication tick, causing the CMC to continuously
	 * apply client-corrections (visible as "Client: true / Server: false" divergence).
	 * @param inRotMode The new rotation mode to apply.
	 */
	UFUNCTION(BlueprintCallable, Category = ACF)
	void SetRotationMode(ERotationMode inRotMode);

	/**
	 * Resets strafe movement, typically reverting to forward-facing locomotion.
	 */
	UFUNCTION(BlueprintCallable, Category = ACF)
	void ResetStrafeMovement();

	/**
	 * Activates a new locomotion stance.
	 * @param locStance The stance to activate (e.g., block, crouch).
	 */
	UFUNCTION(Server, Reliable, BlueprintCallable, Category = ACF)
	void ActivateLocomotionStance(FGameplayTag locStance);

	/**
	 * Deactivates the given locomotion stance.
	 * @param locStance The stance to deactivate.
	 */
	UFUNCTION(Server, Reliable, BlueprintCallable, Category = ACF)
	void DeactivateLocomotionStance(FGameplayTag locStance);

	/**
	 * Deactivates the currently active locomotion stance.
	 */
	UFUNCTION(Server, Reliable, BlueprintCallable, Category = ACF)
	void DeactivateCurrentLocomotionStance();

	/**
	 * Transitions to the next locomotion state in the configured order.
	 */
	UFUNCTION(Server, Reliable, BlueprintCallable, Category = ACF)
	void AccelerateToNextState();

	/**
	 * Transitions to the previous locomotion state in the configured order.
	 */
	UFUNCTION(Server, Reliable, BlueprintCallable, Category = ACF)
	void BrakeToPreviousState();

	/**
	 * Applies yaw rotation input to the character.
	 * @param Rate Input rate for turning.
	 */
	UFUNCTION(BlueprintCallable, Category = ACF)
	void TurnAtRate(float Rate);

	/**
	 * Applies pitch rotation input to the character.
	 * @param Rate Input rate for looking up.
	 */
	UFUNCTION(BlueprintCallable, Category = ACF)
	void LookUpAtRate(float Rate);

	/**
	 * Applies local yaw rotation input (not affected by control rotation).
	 * @param Value Input value for local turning.
	 */
	UFUNCTION(BlueprintCallable, Category = ACF)
	void TurnAtRateLocal(float Value);

	/**
	 * Moves the character forward based on the input value.
	 * @param Value Axis input value.
	 */
	UFUNCTION(BlueprintCallable, Category = ACF)
	void MoveForward(float Value);

	/**
	 * Moves the character right based on the input value.
	 * @param Value Axis input value.
	 */
	UFUNCTION(BlueprintCallable, Category = ACF)
	void MoveRight(float Value);

	/**
	 * Moves the character up based on the input value (used in swimming or flying).
	 * @param Value Axis input value.
	 */
	UFUNCTION(BlueprintCallable, Category = ACF)
	void MoveUp(float Value);

	/**
	 * Returns the current ground info. Automatically updates if outdated.
	 * @return A struct with current ground hit result and physical material.
	 */
	UFUNCTION(BlueprintPure, Category = ACF)
	const FCharacterGroundInfo& GetGroundInfo();

	/**
	 * Returns the current ground distance
	 * @return current ground distance
	 */
	UFUNCTION(BlueprintPure, Category = ACF)
	const float GetGroundDistance();

	/**
	 * Returns the current yaw rotation rate.
	 * @return Character's yaw rotation speed.
	 */
	UFUNCTION(BlueprintCallable, Category = ACF)
	float GetRotationRateYaw() const;

	/**
	 * @return Raw input axis value for forward movement.
	 */
	UFUNCTION(BlueprintPure, Category = ACF)
	FORCEINLINE float GetMoveForwardAxis() const { return MoveForwardAxis; }

	/**
	 * @return Raw input axis value for right movement.
	 */
	UFUNCTION(BlueprintPure, Category = ACF)
	FORCEINLINE float GetMoveRightAxis() const { return MoveRightAxis; }

	/**
	 * Returns movement input vector in world space.
	 * @return The world direction based on movement input.
	 */
	UFUNCTION(BlueprintPure, Category = ACF)
	FVector GetWorldMovementInputVector();

	/**
	 * Returns movement input vector in camera space.
	 * @return The camera-relative movement input.
	 */
	UFUNCTION(BlueprintPure, Category = ACF)
	FVector GetCameraMovementInputVector();

	/**
	 * Returns the target locomotion state the character is transitioning to.
	 * @return Target locomotion state.
	 */
	UFUNCTION(BlueprintPure, Category = ACF)
	FORCEINLINE ELocomotionState GetTargetLocomotionState() const { return targetLocomotionState.State; }

	/**
	 * Returns the current input vector applied to character movement.
	 * @return Current movement input vector.
	 */
	UFUNCTION(BlueprintPure, Category = ACF)
	FVector GetCurrentInputVector();

	/**
	 * Returns the directional enum of the current input.
	 * @return Input direction as an EACFDirection.
	 */
	UFUNCTION(BlueprintPure, Category = ACF)
	EACFDirection GetCurrentInputDirection();

	/**
	 * @return The current aim offset data for the character.
	 */
	UFUNCTION(BlueprintPure, Category = ACF)
	FORCEINLINE FAimOffset GetAimOffset() const { return aimOffest; }

	/**
	 * Resets locomotion state to the default configuration.
	 */
	UFUNCTION(BlueprintCallable, Category = ACF)
	void ResetToDefaultLocomotionState();

	/**
	 * Sets a new target locomotion state.
	 * @param State New locomotion state to transition to.
	 */
	UFUNCTION(Server, Reliable, BlueprintCallable, Category = ACF)
	void SetLocomotionState(ELocomotionState State);

	/**
	 * Overrides movement and swim speed for a given locomotion state.
	 * @param State Locomotion state to modify.
	 * @param speed New movement speed.
	 * @param swimSpeed New swim speed.
	 */
	UFUNCTION(Server, Reliable, BlueprintCallable, Category = ACF)
	void SetLocomotionStateSpeed(ELocomotionState State, float speed, float swimSpeed);

	/**
	 * @return True if the character is aiming.
	 */
	UFUNCTION(BlueprintPure, Category = ACF)
	bool GetIsAiming() const { return bAiming; }

	/**
	 * Sets the character's aiming state.
	 * @param bIsAiming Whether the character is aiming.
	 */
	UFUNCTION(BlueprintCallable, Server, Reliable, Category = ACF)
	void SetIsAiming(bool bIsAiming);

	/**
	* * Gets the ACF animation instance.
	*
	* @return The ACF animation instance.
	*/
	UFUNCTION(BlueprintPure, Category = ACF)
	UACFAnimInstance* GetACFAnimInstance() const {
		return animInstance;
	}

	virtual void SimulateMovement(float DeltaTime) override;

	virtual bool CanAttemptJump() const override;

	virtual float GetMaxSpeed() const override;
	virtual float GetMaxAcceleration() const override;

	virtual void OnMovementModeChanged(EMovementMode PreviousMovementMode, uint8 PreviousCustomMode) override;
	virtual void OnMovementUpdated(float DeltaSeconds, const FVector& OldLocation, const FVector& OldVelocity) override;

	// --- Helpers to expose protected CMC methods to the climbing component ---
	void StartNewPhysicsForClimbing(float DeltaTime, int32 Iterations);
	void RestorePreAdditiveRootMotionVelocityForClimbing();
	void ApplyRootMotionToVelocityForClimbing(float DeltaTime);
	void HandleImpactForClimbing(const FHitResult& Hit, float TimeSlice, const FVector& MoveDelta);
	float SlideAlongSurfaceForClimbing(const FVector& Delta, float Time, const FVector& Normal, FHitResult& Hit, bool bHandleImpact);

	void SetReplicatedAcceleration(const FVector& InAcceleration);
	void SetReplicatedClimbingState(bool bInIsClimbing);

	UFUNCTION(BlueprintPure, Category = "ACF|Climbing")
	bool GetIsClimbingReplicated() const { return bIsClimbingReplicated; }

	UFUNCTION(BlueprintCallable, Category = ACF)
	void SetCurrentMoveset(FGameplayTag moveset) { currentMoveset = moveset; OnRep_Moveset(); }

	UFUNCTION(BlueprintCallable, Category = ACF)
	void SetCurrentOverlay(FGameplayTag overlay) { currentOverlay = overlay; OnRep_Overlay(); }

	/* Called when the climbing component fires OnClimbingStateChanged */
	UFUNCTION()
	void HandleClimbingStateChanged(bool bNewIsClimbing);

protected:
	virtual void BeginPlay() override;
	virtual void TickComponent(float DeltaTime, enum ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction);

	/** Base turn rate, in deg/sec. Other scaling may affect final turn rate. */
	UPROPERTY(EditAnywhere    , BlueprintReadWrite, Category = "ACF|Controller")
	float TurnRate = 75;

	/** Base look up/down rate, in deg/sec. Other scaling may affect final rate. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|Controller")
	float LookUpRate = 75;

	/**Indicates if this character can Move */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Replicated, Category = "ACF|Movement")
	bool bCanMove = true;

	/**Indicates the default locomtionstate*/
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|Movement")
	ELocomotionState DefaultState = ELocomotionState::EJog;

	/**Indicates if this character follows control rotation and strafes*/
	UPROPERTY(EditAnywhere, ReplicatedUsing = OnRep_IsStrafing, Category = "ACF|Movement")
	ERotationMode RotationMode;

	/**Indicates if this character follows control rotation and strafes*/
	UPROPERTY(ReplicatedUsing = OnRep_IsAiming)
	bool bAiming;

	/**Indicates max speed for each locomtion state*/
	UPROPERTY(EditAnywhere, Replicated, BlueprintReadWrite, Category = "ACF|Movement")
	TArray<FACFLocomotionState> LocomotionStates;

	/*Indicates the max angular distance from the cone that allows your character to sprint
	(you cannot sprint backward)*/
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|Movement")
	float SprintDirectionCone = 10.f;

	UPROPERTY(EditAnywhere, Category = "ACF|Movement")
	float GroundTraceDistance = 3000.f;

	UPROPERTY(Replicated)
	float CharacterMaxSpeed;

	float MoveForwardAxis;
	float MoveRightAxis;
	float MoveUpAxis;

	void UpdateCharacterMaxSpeed();

	UPROPERTY(ReplicatedUsing = OnRep_LocomotionStance)
	FGameplayTag currentMovestance;

	//Movesets etc are now moved here for replication
	UPROPERTY(ReplicatedUsing = OnRep_Moveset)
	FGameplayTag currentMoveset;

	UPROPERTY(ReplicatedUsing = OnRep_Overlay)
	FGameplayTag currentOverlay;

	UPROPERTY(ReplicatedUsing = OnRep_RiderLayer)
	FGameplayTag currentRider;

	UPROPERTY()
	TObjectPtr<UACFAnimInstance> animInstance;

	UPROPERTY()
	TObjectPtr<ACharacter> Character;

	UPROPERTY(ReplicatedUsing = OnRep_LocomotionState)
	FACFLocomotionState targetLocomotionState;

	UPROPERTY(ReplicatedUsing = OnRep_CurrentLocomotionState)
	ELocomotionState currentLocomotionState;

	UPROPERTY(ReplicatedUsing = OnRep_IsClimbingReplicated, BlueprintReadOnly, Category = "ACF|Climbing")
	bool bIsClimbingReplicated = false;

	UFUNCTION()
	void OnRep_LocomotionState();

	UFUNCTION()
	void OnRep_Moveset();

	UFUNCTION()
	void OnRep_Overlay();

	UFUNCTION()
	void OnRep_RiderLayer();

	UFUNCTION()
	void OnRep_CurrentLocomotionState();

	UFUNCTION()
	void OnRep_IsClimbingReplicated();

	UFUNCTION()
	void HandleStateChanged(ELocomotionState newState);

	UFUNCTION()
	void OnRep_LocomotionStance();

	UPROPERTY()
	bool bIsSprinting = false;

	void UpdateLocomotion();

	// UPROPERTY(Replicated)
	FAimOffset aimOffest;


	virtual void InitializeComponent() override;

	virtual void PhysCustom(float DeltaTime, int32 Iterations) override;

	/** Cached pointer to the optional climbing component on the same actor. */
	UPROPERTY()
	TObjectPtr<UACFClimbingComponent> ClimbingComponent;

	FCharacterGroundInfo CachedGroundInfo;

	UPROPERTY(Transient)
	bool bHasReplicatedAcceleration = false;

private:
	UFUNCTION()
	void OnRep_IsStrafing();

	UFUNCTION()
	void OnRep_IsAiming();

	void Internal_SetStrafe();

	/** Server RPC used by SetRotationMode to authorise the RotationMode change. */
	UFUNCTION(Server, Reliable)
	void Server_SetRotationMode(ERotationMode inRotMode);

	ERotationMode defaultRotMode;

	void UpdateMaxSpeed(ELocomotionState State);

	/* END DEPRECATED*/
	FActiveGameplayEffectHandle activeEffect;
};
