// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "ACFActionTypes.h"
#include "ACFCCTypes.h"
#include "Animation/ACFAnimTypes.h"
#include "Animation/AnimInstance.h"
#include "CoreMinimal.h"
#include <GameplayTagContainer.h>

#include "ACFAnimInstance.generated.h"

class UACFRiderLayer;
class UACFOverlayLayer;
class UACFClimbingLayer;

// Delegate declarations - fired when movesets/overlays change
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnMovesetChanged, FGameplayTag, NewMovesetTag);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnOverlayChanged, FGameplayTag, NewOverlayTag);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnRiderLayerChanged, FGameplayTag, NewRiderLayerTag);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnClimbingLayerChanged, bool, bIsActive);


/**
 * Animation instance class for ACF characters
 * Handles locomotion states, movement data, overlays, and movesets.
 */
UCLASS()
class CHARACTERCONTROLLER_API UACFAnimInstance : public UAnimInstance {
    GENERATED_BODY()

public:
    UACFAnimInstance();

    /* Returns the movement direction in degrees */
    UFUNCTION(BlueprintPure, Category = ACF)
    FORCEINLINE float GetDirection()  const{ return Direction; }

    /* Returns the normalized movement speed (0..1) */
    UFUNCTION(BlueprintPure, Category = ACF)
    FORCEINLINE float GetNormalizedSpeed() const { return NormalizedSpeed; }

    /* Returns the normalized swim speed (0..1) */
    UFUNCTION(BlueprintPure, Category = ACF)
    FORCEINLINE float GetNormalizedSwimSpeed() const { return NormalizedSwimSpeed; }

    /* Returns the raw movement speed */
    UFUNCTION(BlueprintPure, Category = ACF)
    FORCEINLINE float GetSpeed() const { return Speed; }

    /* Returns the turn rate value */
    UFUNCTION(BlueprintPure, Category = ACF)
    FORCEINLINE float GetTurnRate() const { return TurnRate; }

    /* Checks if this anim instance belongs to the local player */
    UFUNCTION(BlueprintPure, Category = ACF)
    bool IsLocalPlayer() const;

    /* Returns the owning controller's rotation */
    UFUNCTION(BlueprintPure, Category = ACF)
    FRotator GetOwnerControllerRotation() const;

    /* Returns the current locomotion state */
    UFUNCTION(BlueprintPure, Category = ACF)
    ELocomotionState GetCurrentLocomotionState() const;

    /* Returns the target locomotion state (transition) */
    UFUNCTION(BlueprintPure, Category = ACF)
    ELocomotionState GetTargetLocomotionState() const;

    /* Returns whether the character is crouching */
    UFUNCTION(BlueprintPure, Category = ACF)
    bool GetIsCrouching() const;

    /* Returns true if the character is in air */
    UFUNCTION(BlueprintPure, Category = ACF)
    FORCEINLINE bool GetIsInAir() const { return bIsInAir; }

    // MOVESETS
    /* Retrieves the animation overlay matching the given tag */
    UFUNCTION(BlueprintCallable, Category = ACF)
    bool GetAnimationOverlay(const FGameplayTag& tag, FOverlayLayer& outOverlay);

    /* Sets the current animation overlay */
    UFUNCTION(BlueprintCallable, Category = ACF)
    void SetAnimationOverlay(const FGameplayTag& overlayTag);

    /* Sets the riding layer overlay */
    UFUNCTION(BlueprintCallable, Category = ACF)
    void SetRidingLayer(const FGameplayTag& overlayTag);

    /* Sets the current moveset */
    UFUNCTION(BlueprintCallable, Category = ACF)
    void SetMoveset(const FGameplayTag& MovesetTag);

    /* Removes the current overlay and resets to none */
    UFUNCTION(BlueprintCallable, Category = ACF)
    void RemoveOverlay();

    /* Returns the current moveset instance */
    UFUNCTION(BlueprintPure, Category = ACF)
    FORCEINLINE UACFMovesetLayer* GetCurrentMoveset() const { return currentMovesetInstance; }

    /* Retrieves a moveset by tag */
    UFUNCTION(BlueprintCallable, Category = ACF)
    bool GetMovesetByTag(const FGameplayTag& movesetTag, FMoveset& outMoveset) const;

    /* Returns the current moveset tag */
    UFUNCTION(BlueprintPure, Category = ACF)
    FORCEINLINE FGameplayTag GetCurrentMovesetTag() const { return currentMoveset.TagName; }

    /* Returns the current overlay tag */
    UFUNCTION(BlueprintPure, Category = ACF)
    FORCEINLINE FGameplayTag GetCurrentOverlay() const { return currentOverlay.TagName; }

    /* Resets to the default moveset */
    UFUNCTION(BlueprintCallable, Category = ACF)
    void ResetToDefaultMoveset();

    /* Resets to the default overlay */
    UFUNCTION(BlueprintCallable, Category = ACF)
    void ResetToDefaultOverlay();

    /**
     * Populates the animation layer tables (MovesetLayers, OverlayLayers, RiderLayers, IKLayer,
     * ClimbingLayer) from an ACFAnimsetDataAsset. Only non-empty arrays / valid classes from the
     * asset overwrite the existing tables; unset entries are left untouched.
     *
     * This is a pure designer-data initialisation call — it does NOT change the currently active
     * moveset or overlay. Active layer selection remains driven by equipment/weapon logic through
     * UACFCharacterMovementComponent as usual.
     */
    UFUNCTION(BlueprintCallable, Category = "ACF|Movesets")
    void ApplyAnimset(class UACFAnimsetDataAsset* AnimsetData);

    // CLIMBING LAYER
    /* Activates the climbing animation layer */
    UFUNCTION(BlueprintCallable, Category = ACF)
    void ActivateClimbingLayer();

    /* Deactivates the climbing animation layer */
    UFUNCTION(BlueprintCallable, Category = ACF)
    void DeactivateClimbingLayer();

    /* Returns the current climbing layer instance */
    UFUNCTION(BlueprintPure, Category = ACF)
    FORCEINLINE UACFClimbingLayer* GetCurrentClimbingLayer() const { return currentClimbingInstance; }

    /* Returns whether the climbing layer is currently active */
    UFUNCTION(BlueprintPure, Category = ACF)
    FORCEINLINE bool IsClimbingLayerActive() const { return currentClimbingInstance != nullptr; }
    // END CLIMBING LAYER

    // END MOVESETS

     // DELEGATES
    /* Broadcast when the moveset changes */
    UPROPERTY(BlueprintAssignable, Category = "ACF|Events")
    FOnMovesetChanged OnMovesetChanged;

    /* Broadcast when the overlay changes */
    UPROPERTY(BlueprintAssignable, Category = "ACF|Events")
    FOnOverlayChanged OnOverlayChanged;

    /* Broadcast when the rider layer changes */
    UPROPERTY(BlueprintAssignable, Category = "ACF|Events")
    FOnRiderLayerChanged OnRiderLayerChanged;

    /* Broadcast when the climbing layer is activated or deactivated */
    UPROPERTY(BlueprintAssignable, Category = "ACF|Events")
    FOnClimbingLayerChanged OnClimbingLayerChanged;
    // END DELEGATES

    // IK
    /* Returns whether foot IK is enabled */
    UFUNCTION(BlueprintPure, Category = ACF)
    bool GetEnableFootIK() const { return EnableFootIK; }

    /* Enables or disables foot IK */
    UFUNCTION(BlueprintCallable, Category = ACF)
    void SetEnableFootIK(bool val) { EnableFootIK = val; }

    /* Returns whether hand IK is enabled */
    UFUNCTION(BlueprintPure, Category = ACF)
    bool GetEnableHandIK() const { return EnableHandIK; }

    /* Enables or disables hand IK */
    UFUNCTION(BlueprintCallable, Category = ACF)
    void SetEnableHandIK(bool val) { EnableHandIK = val; }

    /* Returns the desired start direction for locomotion */
    UFUNCTION(BlueprintCallable, Category = ACF)
    EACFDirection GetStartDirection() const { return DesiredStartDirection; }

    /* Sets the desired start direction for locomotion */
    UFUNCTION(BlueprintCallable, Category = ACF)
    void SetStartDirection(EACFDirection val) { DesiredStartDirection = val; }

    /* Returns the current root transform */
    UFUNCTION(BlueprintPure, Category = ACF)
    FTransform GetRootTrans() const { return RootTrans; }
    // END IK

    virtual void NativeInitializeAnimation() override;

    virtual void NativeBeginPlay() override;

    virtual void NativeThreadSafeUpdateAnimation(float DeltaSeconds) override;

protected:
    // ----- CONFIG ---- //
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|Config")
    float IsMovingSpeedThreshold = 0.02f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|Config")
    float YawOffsetLimit = 60.f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|Config")
    float DirectionDeadZone = 10.f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|Config")
    float LeaningFactor = .5f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|Config")
    float TurnRateSmoothing = 2.f;

    UPROPERTY(BlueprintReadOnly, EditDefaultsOnly, Category = "ACF|Config")
    float AimOffsetInterpSpeed = 10.f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, meta = (TitleProperty = "TagName"), Category = "ACF|Movesets")
    TArray<FMoveset> MovesetLayers;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, meta = (TitleProperty = "TagName"), Category = "ACF|Overlays")
    TArray<FOverlayLayer> OverlayLayers;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, meta = (TitleProperty = "TagName"), Category = "ACF|Movesets")
    TArray<FRiderLayer> RiderLayers;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|Movesets")
    TSubclassOf<class UACFIKLayer> IKLayer;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|Movesets")
    TSubclassOf<class UACFClimbingLayer> ClimbingLayer;

    // ----- READ ONLY VARIABLES ---- //
    UPROPERTY(BlueprintReadOnly, Category = "ACF|Movesets")
    FMoveset currentMoveset;

    UPROPERTY(BlueprintReadOnly, Category = "ACF|Movesets")
    FOverlayLayer currentOverlay;

    UPROPERTY(BlueprintReadOnly, Category = "ACF|Movesets")
    FRiderLayer currentRiderLayer;

    // Instances
    UPROPERTY(BlueprintReadOnly, Category = ACF)
    UACFMovesetLayer* currentMovesetInstance;

    UPROPERTY(BlueprintReadOnly, Category = ACF)
    UACFOverlayLayer* currentOverlayInstance;

    UPROPERTY(BlueprintReadOnly, Category = ACF)
    UACFRiderLayer* currentRiderInstance;

    UPROPERTY(BlueprintReadOnly, Category = ACF)
    UACFClimbingLayer* currentClimbingInstance;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|Updates")
    bool bUpdateMovementData = true;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|Updates")
    bool bUpdateLocationData = true;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|Updates")
    bool bUpdateRotationData = true;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|Updates")
    bool bUpdateSpeedData = true;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|Updates")
    bool bUpdateAccelerationData = true;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|Updates")
    bool bUpdateAimData = true;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|Updates")
    bool bUpdateJumpData = true;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|Updates")
    bool bUpdateLeaningData = true;

    UPROPERTY(BlueprintReadOnly, Category = ACF)
    bool bCanUseAdditive = false;

    UPROPERTY(BlueprintReadOnly, Category = "ACF|Movement")
    bool bIsCrouching;

    UPROPERTY(BlueprintReadOnly, Category = "ACF|Movement")
    bool bWasCrouching;

    UPROPERTY(BlueprintReadOnly, Category = "ACF|Movement")
    bool bCrouchChanged;

    UPROPERTY(BlueprintReadOnly, Category = "ACF|Movement")
    bool bIsOnGround;

    UPROPERTY(BlueprintReadOnly, Category = "ACF|Movement")
    bool bIsWalking;

    UPROPERTY(BlueprintReadOnly, Category = "ACF|Movement")
    bool bWasWalking;

    UPROPERTY(BlueprintReadOnly, Category = "ACF|Movement")
    bool bWalkStateChanged;

    UPROPERTY(BlueprintReadOnly, Category = "ACF|Movement")
    bool bIsStrafing;

    UPROPERTY(BlueprintReadOnly, Category = "ACF|Movement")
    bool bIsSwimming;

    UPROPERTY(BlueprintReadOnly, Category = "ACF|Movement")
    bool bIsClimbing;

    UPROPERTY(BlueprintReadOnly, Category = "ACF|Location")
    float Displacement = 0.f;

    UPROPERTY(BlueprintReadOnly, Category = "ACF|Location")
    float DisplacementDelta = 0.f;

    UPROPERTY(BlueprintReadOnly, Category = "ACF|Location")
    FVector OwnerLocation;

    UPROPERTY(BlueprintReadOnly, Category = "ACF|Rotation")
    FRotator OwnerRotation;

    UPROPERTY(BlueprintReadOnly, Category = "ACF|Rotation")
    FRotator ControlRotation;

    UPROPERTY(BlueprintReadOnly, Category = "ACF|Rotation")
    FRotator PreviousRotation;

    UPROPERTY(BlueprintReadOnly, Category = "ACF|Rotation")
    float YawSpeed = 0.f;

    UPROPERTY(BlueprintReadOnly, Category = "ACF|Rotation")
    float YawDelta = 0.f;

    UPROPERTY(BlueprintReadWrite, Category = "ACF|Rotation")
    float YawOffset = 0.f;

    UPROPERTY(BlueprintReadOnly, Category = "ACF|Velocity")
    bool bWasMoving;

    UPROPERTY(BlueprintReadOnly, Category = "ACF|Velocity")
    bool bIsMoving;

    UPROPERTY(BlueprintReadOnly, Category = "ACF|Velocity")
    float Direction = 0.f;

    UPROPERTY(BlueprintReadOnly, Category = "ACF|Velocity")
    float DirectionWithOffset = 0.f;

    UPROPERTY(BlueprintReadOnly, Category = "ACF|Velocity")
    float Speed = 0.f;

    UPROPERTY(BlueprintReadOnly, Category = "ACF|Velocity")
    float DeltaInputDirection = 0.f;

    UPROPERTY(BlueprintReadOnly, Category = "ACF|Velocity")
    float NormalizedSpeed = 0.f;

    UPROPERTY(BlueprintReadOnly, Category = "ACF|Velocity")
    float PreviousSpeed = 0.f;

    UPROPERTY(BlueprintReadOnly, Category = "ACF|Velocity")
    float NormalizedSwimSpeed = 0.f;

    UPROPERTY(BlueprintReadOnly, Category = "ACF|Velocity")
    FVector WorldSpeed;

    UPROPERTY(BlueprintReadOnly, Category = "ACF|Velocity")
    FVector WorldSpeed2D;

    UPROPERTY(BlueprintReadOnly, Category = "ACF|Velocity")
    FVector LocalSpeed2D;

    UPROPERTY(BlueprintReadOnly, Category = "ACF|Velocity")
    EACFDirection SpeedDirection;

    UPROPERTY(BlueprintReadOnly, Category = "ACF|Velocity")
    EACFDirection SpeedDirectionWithOffset;

    UPROPERTY(BlueprintReadOnly, Category = "ACF|Velocity")
    EACFDirection LastSpeedDirection;

    UPROPERTY(BlueprintReadOnly, Category = "ACF|Velocity")
    EACFDirection LastSpeedDirectionWithOffset;

    UPROPERTY(BlueprintReadOnly, Category = "ACF|AimOffset")
    FVector2D AimOffset;

    UPROPERTY(BlueprintReadWrite, Category = "ACF|AimOffset")
    FTransform RootTrans;

    UPROPERTY(BlueprintReadOnly, Category = "ACF|AimOffset")
    float TurnRate;

    UPROPERTY(BlueprintReadOnly, Category = "ACF|Jump")
    bool bIsInAir;

    UPROPERTY(BlueprintReadOnly, Category = "ACF|Jump")
    bool bIsJumping;

    UPROPERTY(BlueprintReadOnly, Category = "ACF|Jump")
    bool bIsFalling;

    UPROPERTY(BlueprintReadOnly, Category = "ACF|Jump")
    float GroundDistance = -1.0f;

    UPROPERTY(BlueprintReadOnly, Category = "ACF|Jump")
    float TimeToApex = 0.f;

    UPROPERTY(BlueprintReadOnly, Category = "ACF|Acceleration")
    bool bIsAccelerating;

    UPROPERTY(BlueprintReadOnly, Category = "ACF|Acceleration")
    float Acceleration = 0.f;

    UPROPERTY(BlueprintReadOnly, Category = "ACF|Acceleration")
    FVector Acceleration2D;

    UPROPERTY(BlueprintReadOnly, Category = "ACF|Acceleration")
    FVector NormalizedAccel;

    UPROPERTY(BlueprintReadOnly, Category = "ACF|Acceleration")
    FVector LocalAccel2D;

    UPROPERTY(BlueprintReadOnly, Category = "ACF|Acceleration")
    FVector PivotDirection;

    UPROPERTY(BlueprintReadWrite, Category = "ACF|Acceleration")
    float TimeSinceLastPivot;

    UPROPERTY(BlueprintReadOnly, Category = "ACF|Acceleration")
    EACFDirection AccelerationDirection;

    UPROPERTY(BlueprintReadOnly, Category = "ACF|Leaning")
    float LeanAngle;

    UPROPERTY(BlueprintReadOnly, EditAnywhere, Category = "ACF|IK")
    bool EnableFootIK;

    UPROPERTY(BlueprintReadOnly, EditAnywhere, Category = "ACF|IK")
    bool EnableHandIK;

    UPROPERTY(BlueprintReadOnly, Category = ACF)
    class ACharacter* CharacterOwner;

    UPROPERTY(BlueprintReadOnly, Category = ACF)
    class UACFCharacterMovementComponent* MovementComp;
    // ----- END READ ONLY VARIABLES ---- //

    // ----- END CONFIG ---- //

    UFUNCTION(BlueprintCallable, Category = ACF)
    void SetTurnInPlaceYawOffset(float inYawOffset);

    UFUNCTION(BlueprintNativeEvent, Category = ACF)
    EACFDirection GetDirectionFromAngle(float angle, EACFDirection currentDirection, bool bUseCurrentDirection);

    UPROPERTY(BlueprintReadOnly, Category = "ACF|Acceleration")
    EACFDirection DesiredStartDirection;

private:
    void SetReferences();

    void UpdateLeaning(float deltatime);
    void UpdateLocation(float deltatime);
    void UpdateRotation(float deltatime);
    void UpdateVelocity(float deltatime);

    void UpdateAimData(float deltatime);
    void UpdateAcceleration(float deltatime);
    void UpdateStateData(float deltatime);
    void UpdateJump(float deltatime);

    FVector CalculateRelativeAccelerationAmount() const;

    UFUNCTION()
    void HandleTargetLocomotionStateChanged(ELocomotionState newState);
};
