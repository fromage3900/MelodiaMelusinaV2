// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ACFFreeClimbJumpAction.h"

#include "Components/ACFClimbingComponent.h"
#include "DrawDebugHelpers.h"
#include "Engine/World.h"
#include "GameFramework/Character.h"
#include "Math/UnrealMathUtility.h"

UACFFreeClimbJumpAction::UACFFreeClimbJumpAction()
{
    // The jump is warped along the wall to land precisely on the next grip.
    ActionConfig.MontageReproductionType = EMontageReproductionType::EMotionWarped;
    ActionConfig.WarpInfo.TargetType = EWarpTargetType::ETargetTransform;

    // Allow the jump to fire while climbing (custom movement mode) as well as in air.
    ActionConfig.PerformableInMovementModes.Reset();
    ActionConfig.PerformableInMovementModes.Add(EMovementMode::MOVE_Custom);
    ActionConfig.PerformableInMovementModes.Add(EMovementMode::MOVE_Falling);
    ActionConfig.PerformableInMovementModes.Add(EMovementMode::MOVE_Walking);

    // Default section mapping; can be overridden per-Blueprint.
    DirectionToMontageSection.Add(EACFClimbJumpDirection::Up, FName("Up"));
    DirectionToMontageSection.Add(EACFClimbJumpDirection::Left, FName("Left"));
    DirectionToMontageSection.Add(EACFClimbJumpDirection::Right, FName("Right"));
}

void UACFFreeClimbJumpAction::ActivateAbility(const FGameplayAbilitySpecHandle Handle, const FGameplayAbilityActorInfo* ActorInfo,
    const FGameplayAbilityActivationInfo ActivationInfo, const FGameplayEventData* TriggerEventData)
{
    // Read the requested direction from the payload. VectorPayload is treated as a 2D
    // intent in wall space: X = right (left when negative), Y = up.
    if (GetTriggerPayload().bIsValid && !GetTriggerPayload().VectorPayload.IsNearlyZero()) {
        RequestedDirection = GetTriggerPayload().VectorPayload;
    } else {
        RequestedDirection = FVector::ZeroVector;
    }

    if (RequestedDirection.IsNearlyZero()) {
        FinalDirection = DefaultDirection;
    } else {
        FinalDirection = ResolveDirection(RequestedDirection.X, RequestedDirection.Y);
    }

    Super::ActivateAbility(Handle, ActorInfo, ActivationInfo, TriggerEventData);
}

FName UACFFreeClimbJumpAction::GetMontageSectionName_Implementation()
{
    if (const FName* Section = DirectionToMontageSection.Find(FinalDirection)) {
        return *Section;
    }
    return Super::GetMontageSectionName_Implementation();
}

FTransform UACFFreeClimbJumpAction::GetWarpTransform_Implementation()
{
    ACharacter* Owner = GetCharacterOwner();
    if (!Owner) {
        return FTransform::Identity;
    }

    FVector WallNormal, WallRight, WallUp;
    if (!BuildWallBasis(WallNormal, WallRight, WallUp)) {
        // No climbable surface resolved: fall back to a plain world jump in the
        // requested direction so the ability still produces a sensible warp.
        WallNormal = -Owner->GetActorForwardVector();
        WallRight = Owner->GetActorRightVector();
        WallUp = FVector::UpVector;
    }

    // Resolve the requested 2D intent. When the payload was empty we still want a
    // motion that matches the default/resolved discrete direction.
    float RightAmount = RequestedDirection.X;
    float UpAmount = RequestedDirection.Y;
    if (FMath::IsNearlyZero(RightAmount) && FMath::IsNearlyZero(UpAmount)) {
        switch (FinalDirection) {
        case EACFClimbJumpDirection::Up:
            UpAmount = 1.f;
            break;
        case EACFClimbJumpDirection::Right:
            RightAmount = 1.f;
            break;
        case EACFClimbJumpDirection::Left:
            RightAmount = -1.f;
            break;
        }
    }

    // The along-wall direction lives entirely in the wall plane, so warping along it
    // keeps the character at the same distance from the surface (works on slopes too).
    FVector AlongWall = (WallRight * RightAmount) + (WallUp * UpAmount);
    if (!AlongWall.Normalize()) {
        AlongWall = WallUp;
    }

    const FVector StartLocation = Owner->GetActorLocation();
    const FVector TargetLocation = StartLocation + AlongWall * JumpLength;

    // Keep the character facing into the wall, tilting with the surface.
    const FRotator TargetRotation = FRotationMatrix::MakeFromXZ(-WallNormal, WallUp).Rotator();

    // Debug draw only where there is a viewport (skip dedicated server).
    if (ActionConfig.WarpInfo.bShowWarpDebug && GetWorld() && GetWorld()->GetNetMode() != NM_DedicatedServer) {
        DrawDebugSphere(GetWorld(), TargetLocation, 16.f, 12, FColor::Green, false, 3.f);
        DrawDebugLine(GetWorld(), StartLocation, TargetLocation, FColor::Cyan, false, 3.f, 0, 2.f);
    }

    return FTransform(TargetRotation, TargetLocation);
}

UACFClimbingComponent* UACFFreeClimbJumpAction::GetClimbingComponent() const
{
    if (const ACharacter* Owner = GetCharacterOwner()) {
        return Owner->FindComponentByClass<UACFClimbingComponent>();
    }
    return nullptr;
}

bool UACFFreeClimbJumpAction::BuildWallBasis(FVector& OutNormal, FVector& OutWallRight, FVector& OutWallUp) const
{
    const UACFClimbingComponent* ClimbComp = GetClimbingComponent();
    if (!ClimbComp) {
        return false;
    }

    OutNormal = ClimbComp->GetClimbSurfaceNormal();
    if (!OutNormal.Normalize()) {
        return false;
    }

    // Horizontal direction along the wall (perpendicular to the surface normal).
    OutWallRight = FVector::CrossProduct(FVector::UpVector, OutNormal);
    if (!OutWallRight.Normalize()) {
        // Degenerate case (near-horizontal surface): use the actor's right vector instead.
        if (const ACharacter* Owner = GetCharacterOwner()) {
            OutWallRight = FVector::VectorPlaneProject(Owner->GetActorRightVector(), OutNormal);
        }
        if (!OutWallRight.Normalize()) {
            return false;
        }
    }

    // Up direction along the wall plane (tilts with the surface).
    OutWallUp = FVector::CrossProduct(OutNormal, OutWallRight);
    return OutWallUp.Normalize();
}

EACFClimbJumpDirection UACFFreeClimbJumpAction::ResolveDirection(float RightAmount, float UpAmount)
{
    // Vertical intent wins ties so a mostly-upward push always reads as "Up".
    if (UpAmount >= FMath::Abs(RightAmount)) {
        return EACFClimbJumpDirection::Up;
    }
    return RightAmount >= 0.f ? EACFClimbJumpDirection::Right : EACFClimbJumpDirection::Left;
}
