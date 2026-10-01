// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "Components/ACFQuadrupedMovementComponent.h"

#include "ARSStatisticsComponent.h"
#include "Animation/ACFAnimInstance.h"
#include "Components/ACFAbilitySystemComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "GameFramework/Actor.h"
#include "Kismet/GameplayStatics.h"
#include "Net/UnrealNetwork.h"
#include <Animation/AnimEnums.h>
#include <Components/ActorComponent.h>
#include <Engine/World.h>
#include <GameFramework/CharacterMovementComponent.h>
#include <GameFramework/Controller.h>
#include <GameFramework/Pawn.h>
#include <GameFramework/SpringArmComponent.h>
#include <Kismet/KismetMathLibrary.h>
#include <Kismet/KismetSystemLibrary.h>
#include <TimerManager.h>
#include "GameFramework/Character.h"

void UACFQuadrupedMovementComponent::TickComponent(float DeltaTime, enum ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
    Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

    if (!movementInput.IsNearlyZero()) {
        AddInputVector(movementInput);
        movementInput = FVector(0.f);
    }
    if (!FMath::IsNearlyZero(rotationInput.Yaw) && !IsFalling()) {
        CharacterOwner->AddActorWorldRotation(rotationInput);
        rotationInput = FRotator(0.f);
    }


    if (GetForceSpeedToForward() && !IsFalling()) {
        const FVector forward = Character->GetActorForwardVector() * Velocity.Size();
        Velocity = FMath::VInterpTo(Velocity, forward, DeltaTime, GetSpeedToForwardInterpRate());
    }

    UpdateBodyAlignment(DeltaTime);
}

void UACFQuadrupedMovementComponent::UpdateBodyAlignment(float DeltaTime)
{
    if (!CharacterOwner) {
        return;
    }

    USkeletalMeshComponent* MeshComp = CharacterOwner->GetMesh();
    if (!MeshComp) {
        return;
    }

    // The mesh's authored relative rotation (e.g. the typical (0, -90, 0) on a Character)
    // must be preserved as the base orientation we add the slope tilt on top of. We capture
    // it the first time we touch the alignment, before we ever modify the mesh ourselves.
    if (!bMeshBaseRotationCached) {
        MeshBaseRelativeRotation = MeshComp->GetRelativeRotation();
        bMeshBaseRotationCached = true;
    }

    // Early-out only when the feature is disabled AND we are already at rest. This avoids
    // writing to the mesh every frame for actors that never use slope tilt.
    const bool bHasResidualTilt = !FMath::IsNearlyZero(CurrentAlignmentPitch, 0.05f)
        || !FMath::IsNearlyZero(CurrentAlignmentRoll, 0.05f);

    if (!bAlignBodyWithGround && !bHasResidualTilt) {
        return;
    }

    float targetPitch = 0.f;
    float targetRoll = 0.f;

    const bool bCanSampleSlope = bAlignBodyWithGround
        && MovementMode == MOVE_Walking
        && CurrentFloor.bBlockingHit
        && !CurrentFloor.HitResult.ImpactNormal.IsNearlyZero();

    if (bCanSampleSlope) {
        // Use a yaw-only right vector and the world up so the slope decomposition is
        // independent from the tilt we apply to the mesh; otherwise the sampled angle
        // would feed back into itself every frame and either drift to zero or oscillate.
        const FRotator yawOnly(0.f, CharacterOwner->GetActorRotation().Yaw, 0.f);
        const FVector yawRight = yawOnly.RotateVector(FVector::RightVector);

        float slopePitch = 0.f;
        float slopeRoll = 0.f;
        UKismetMathLibrary::GetSlopeDegreeAngles(
            yawRight,
            CurrentFloor.HitResult.ImpactNormal,
            FVector::UpVector,
            slopePitch,
            slopeRoll);

        targetPitch = FMath::Clamp(slopePitch, -MaxAlignmentPitch, MaxAlignmentPitch);
        targetRoll = FMath::Clamp(slopeRoll, -MaxAlignmentRoll, MaxAlignmentRoll);
    }

    CurrentAlignmentPitch = FMath::FInterpTo(CurrentAlignmentPitch, targetPitch, DeltaTime, AlignmentSpeed);
    CurrentAlignmentRoll = FMath::FInterpTo(CurrentAlignmentRoll, targetRoll, DeltaTime, AlignmentSpeed);

    // Build the final mesh world rotation: actor yaw, then tilt in actor-local space,
    // then the mesh's authored offset. Composing as quaternions right-to-left means
    // the mesh is first re-oriented from its art-frame to the actor frame (base),
    // then tilted by (pitch, roll) in the actor frame, then yawed to face the world.
    // The capsule itself is never touched, so floor sampling stays stable and the
    // CharacterMovementComponent does not fight us over rotation (works in MP too).
    const FRotator actorYawOnly(0.f, CharacterOwner->GetActorRotation().Yaw, 0.f);
    const FRotator tilt(CurrentAlignmentPitch, 0.f, CurrentAlignmentRoll);

    const FQuat finalQuat =
        actorYawOnly.Quaternion() * tilt.Quaternion() * MeshBaseRelativeRotation.Quaternion();

    MeshComp->SetWorldRotation(finalQuat);
}


void UACFQuadrupedMovementComponent::Turn(float Value)
{
    if (CharacterOwner && Value != 0.f) {
        const float finalValue = Value * RotationRate.Yaw * UGameplayStatics::GetWorldDeltaSeconds(this);
        rotationInput = FRotator(0, finalValue, 0);
      //  const FVector Direction = CharacterOwner->GetActorForwardVector();
      //  const FVector finalRot = YawRotation.RotateVector(Direction);

        // AddInputVector(finalRot * 0.1f);
        // CharacterOwner->AddActorWorldRotation(YawRotation);
    }
}

void UACFQuadrupedMovementComponent::MoveForwardLocal(float Value)
{
    if (CharacterOwner && Value != 0.0f) {
        // get forward vector
        const FVector Direction = CharacterOwner->GetActorForwardVector();

        movementInput = Direction * Value;
        //  AddInputVector(movementInput);
    }
}
