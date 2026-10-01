// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "ACFCCTypes.h"
#include "ACFCharacterMovementComponent.h"
#include "Components/ActorComponent.h"
#include "CoreMinimal.h"
#include <Engine/DataTable.h>

#include "ACFQuadrupedMovementComponent.generated.h"


UCLASS(Blueprintable, ClassGroup = (ACF), meta = (BlueprintSpawnableComponent))
class CHARACTERCONTROLLER_API UACFQuadrupedMovementComponent : public UACFCharacterMovementComponent {
    GENERATED_BODY()

public:
    UFUNCTION(BlueprintCallable, Category = ACF)
    void Turn(float Value);

    UFUNCTION(BlueprintCallable, Category = ACF)
    void MoveForwardLocal(float Value);
        
    UFUNCTION(BlueprintPure, Category = ACF)
    bool GetForceSpeedToForward() const
    { return bForceSpeedToForward; }

    UFUNCTION(BlueprintCallable, Category = ACF)
    void SetForceSpeedToForward(bool val) { bForceSpeedToForward = val; }

    UFUNCTION(BlueprintPure, Category = ACF)
    float GetSpeedToForwardInterpRate() const 
    { return SpeedToForwardInterpRate; }

    UFUNCTION(BlueprintCallable, Category = ACF)
    void SetSpeedToForwardInterpRate(float val) { SpeedToForwardInterpRate = val; }

    /* Body alignment / slope tilt */

    UFUNCTION(BlueprintPure, Category = "ACF|Quadruped|BodyAlignment")
    bool GetAlignBodyWithGround() const { return bAlignBodyWithGround; }

    /* Toggles the slope tilt at runtime. When turned off, the body smoothly returns to flat. */
    UFUNCTION(BlueprintCallable, Category = "ACF|Quadruped|BodyAlignment")
    void SetAlignBodyWithGround(bool bEnabled) { bAlignBodyWithGround = bEnabled; }

    UFUNCTION(BlueprintPure, Category = "ACF|Quadruped|BodyAlignment")
    float GetAlignmentSpeed() const { return AlignmentSpeed; }

    UFUNCTION(BlueprintCallable, Category = "ACF|Quadruped|BodyAlignment")
    void SetAlignmentSpeed(float val) { AlignmentSpeed = FMath::Max(0.f, val); }

    UFUNCTION(BlueprintPure, Category = "ACF|Quadruped|BodyAlignment")
    float GetMaxAlignmentPitch() const { return MaxAlignmentPitch; }

    UFUNCTION(BlueprintCallable, Category = "ACF|Quadruped|BodyAlignment")
    void SetMaxAlignmentPitch(float val) { MaxAlignmentPitch = FMath::Clamp(val, 0.f, 89.f); }

    UFUNCTION(BlueprintPure, Category = "ACF|Quadruped|BodyAlignment")
    float GetMaxAlignmentRoll() const { return MaxAlignmentRoll; }

    UFUNCTION(BlueprintCallable, Category = "ACF|Quadruped|BodyAlignment")
    void SetMaxAlignmentRoll(float val) { MaxAlignmentRoll = FMath::Clamp(val, 0.f, 89.f); }

protected:
    virtual void TickComponent(float DeltaTime, enum ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

    /*Forces the movement to follow the forward vector of the actor. Usefull for horses or animals that can't strafe*/
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "ACF|Quadruped")
    bool bForceSpeedToForward = false;

    /*Strength of the force forward*/
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, meta = (EditCondition = "bForceSpeedToForward"), Category = "ACF|Quadruped")
    float SpeedToForwardInterpRate = 20.f;

    /* Tilts the body of the animal to match the slope it's standing on. Only the visual mesh is tilted, the capsule stays upright. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "ACF|Quadruped|BodyAlignment")
    bool bAlignBodyWithGround = false;

    /* How quickly the body interpolates toward the slope orientation (and back to flat). Higher = snappier. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (EditCondition = "bAlignBodyWithGround", ClampMin = "0.0"), Category = "ACF|Quadruped|BodyAlignment")
    float AlignmentSpeed = 8.f;

    /* Maximum pitch (uphill / downhill tilt), in degrees. The body will never tilt forward/back more than this. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (EditCondition = "bAlignBodyWithGround", ClampMin = "0.0", ClampMax = "89.0"), Category = "ACF|Quadruped|BodyAlignment")
    float MaxAlignmentPitch = 35.f;

    /* Maximum roll (sideways tilt), in degrees. The body will never tilt left/right more than this. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (EditCondition = "bAlignBodyWithGround", ClampMin = "0.0", ClampMax = "89.0"), Category = "ACF|Quadruped|BodyAlignment")
    float MaxAlignmentRoll = 25.f;

private:
    FRotator rotationInput;

    FVector movementInput;

    void UpdateBodyAlignment(float DeltaTime);

    /* Cached default relative rotation of the mesh, captured the first time the alignment runs. */
    FRotator MeshBaseRelativeRotation = FRotator::ZeroRotator;
    bool bMeshBaseRotationCached = false;

    /* Smoothed pitch/roll currently applied to the mesh, in actor-local space (degrees). */
    float CurrentAlignmentPitch = 0.f;
    float CurrentAlignmentRoll = 0.f;
};
