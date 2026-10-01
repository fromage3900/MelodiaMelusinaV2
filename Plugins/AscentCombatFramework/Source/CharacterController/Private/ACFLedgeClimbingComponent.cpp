// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2024. All Rights Reserved.

#include "ACFLedgeClimbingComponent.h"
#include "ACFActionTypes.h"
#include "ACFClimbingMontageDataAsset.h"
#include "ACFGripPointComponent.h"
#include "Components/ACFAbilitySystemComponent.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Net/UnrealNetwork.h"
#include "Engine/OverlapResult.h"
#include "Engine/World.h"

UACFLedgeClimbingComponent::UACFLedgeClimbingComponent()
{
    PrimaryComponentTick.bCanEverTick = false;
    SetIsReplicatedByDefault(true);
}

void UACFLedgeClimbingComponent::BeginPlay()
{
    Super::BeginPlay();
    CacheComponents();
}

void UACFLedgeClimbingComponent::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(UACFLedgeClimbingComponent, CurrentGripPoint);
    DOREPLIFETIME(UACFLedgeClimbingComponent, bIsClimbing);
}

// ---------------------------------------------------------------------------
//  Core API
// ---------------------------------------------------------------------------

bool UACFLedgeClimbingComponent::JumpToNearestGripPoint(FVector2D DirectionInput, bool bInputIsWorldSpace)
{
    if (!CharOwner)
    {
        return false;
    }

    // Only the owning client / server authority should initiate the request
    if (!CharOwner->IsLocallyControlled())
    {
        return false;
    }

    if (DirectionInput.IsNearlyZero())
    {
        return false;
    }

    const FVector WorldDir = InputToWorldDirection(DirectionInput, bInputIsWorldSpace);
    UACFGripPointComponent* TargetGrip = FindBestGripInDirection(WorldDir);
    if (!TargetGrip)
    {
        return false;
    }

    const EClimbingDirection ClimbDir = ClassifyDirection(WorldDir);

    if (CharOwner->HasAuthority())
    {
        // Standalone or listen-server: execute directly
        TriggerClimbAbility(ClimbDir, TargetGrip);
    }
    else
    {
        // Dedicated server: send RPC
        Server_JumpToGrip(TargetGrip, ClimbDir);
    }

    return true;
}

void UACFLedgeClimbingComponent::GrabGripPoint(UACFGripPointComponent* GripPoint)
{
    if (!GripPoint || !CharOwner)
    {
        return;
    }

    CurrentGripPoint = GripPoint;
    bIsClimbing = true;
    SetClimbingMovementMode(true);

    OnGripChanged.Broadcast(CurrentGripPoint, EClimbingDirection::Up);
    OnClimbingStateChanged.Broadcast(true);
}

void UACFLedgeClimbingComponent::ReleaseGrip()
{
    CurrentGripPoint = nullptr;
    bIsClimbing = false;
    SetClimbingMovementMode(false);

    OnClimbingStateChanged.Broadcast(false);
}

// ---------------------------------------------------------------------------
//  Queries
// ---------------------------------------------------------------------------

TArray<UACFGripPointComponent*> UACFLedgeClimbingComponent::FindNearbyGripPoints() const
{
    TArray<UACFGripPointComponent*> Result;

    if (!CharOwner || !GetWorld())
    {
        return Result;
    }

    const FVector Origin = CharOwner->GetActorLocation();

    // Collect all overlapping actors in the search sphere
    TArray<FOverlapResult> Overlaps;
    FCollisionShape Sphere = FCollisionShape::MakeSphere(SearchRadius);
    FCollisionQueryParams Params;
    Params.AddIgnoredActor(CharOwner);

    GetWorld()->OverlapMultiByChannel(Overlaps, Origin, FQuat::Identity, GripSearchChannel, Sphere, Params);

    TSet<AActor*> VisitedActors;
    for (const FOverlapResult& Overlap : Overlaps)
    {
        AActor* OverlapActor = Overlap.GetActor();
        if (!OverlapActor || VisitedActors.Contains(OverlapActor))
        {
            continue;
        }
        VisitedActors.Add(OverlapActor);

        TArray<UACFGripPointComponent*> GripPoints;
        OverlapActor->GetComponents<UACFGripPointComponent>(GripPoints);
        for (UACFGripPointComponent* Grip : GripPoints)
        {
            if (Grip && Grip->IsGripEnabled())
            {
                const float DistSq = FVector::DistSquared(Grip->GetGripWorldLocation(), Origin);
                if (DistSq <= SearchRadius * SearchRadius)
                {
                    Result.Add(Grip);
                }
            }
        }
    }

    // Sort by distance
    Result.Sort([&Origin](const UACFGripPointComponent& A, const UACFGripPointComponent& B)
    {
        return FVector::DistSquared(A.GetGripWorldLocation(), Origin)
             < FVector::DistSquared(B.GetGripWorldLocation(), Origin);
    });

    return Result;
}

UACFGripPointComponent* UACFLedgeClimbingComponent::FindBestGripInDirection(FVector WorldDirection) const
{
    const TArray<UACFGripPointComponent*> NearbyGrips = FindNearbyGripPoints();
    if (NearbyGrips.IsEmpty())
    {
        return nullptr;
    }

    const FVector CharLoc = CharOwner->GetActorLocation();
    const FVector NormDir = WorldDirection.GetSafeNormal();

    UACFGripPointComponent* BestGrip = nullptr;
    float BestScore = -BIG_NUMBER;

    for (UACFGripPointComponent* Grip : NearbyGrips)
    {
        // Skip the current grip
        if (Grip == CurrentGripPoint)
        {
            continue;
        }

        const FVector ToGrip = (Grip->GetGripWorldLocation() - CharLoc).GetSafeNormal();
        const float Dot = FVector::DotProduct(NormDir, ToGrip);

        if (Dot < DirectionDotThreshold)
        {
            continue;
        }

        // Score: prefer alignment over proximity
        const float Dist = FVector::Dist(Grip->GetGripWorldLocation(), CharLoc);
        const float Score = Dot - (Dist / SearchRadius) * 0.2f;

        if (Score > BestScore)
        {
            BestScore = Score;
            BestGrip = Grip;
        }
    }

    return BestGrip;
}

// ---------------------------------------------------------------------------
//  Internal helpers
// ---------------------------------------------------------------------------

void UACFLedgeClimbingComponent::CacheComponents()
{
    CharOwner = Cast<ACharacter>(GetOwner());
    if (CharOwner)
    {
        AbilityComp = CharOwner->FindComponentByClass<UACFAbilitySystemComponent>();
    }
}

FVector UACFLedgeClimbingComponent::InputToWorldDirection(FVector2D Input2D, bool bIsWorldSpace) const
{
    if (bIsWorldSpace)
    {
        // Project the world-space input onto the wall plane of the current grip
        if (CurrentGripPoint)
        {
            const FVector WallNormal = CurrentGripPoint->GetSurfaceNormal();
            FVector WorldDir3D = FVector(Input2D.X, Input2D.Y, 0.f);
            // Remove the component along the wall normal
            WorldDir3D = FVector::VectorPlaneProject(WorldDir3D, WallNormal).GetSafeNormal();
            return WorldDir3D;
        }
        return FVector(Input2D.X, Input2D.Y, 0.f).GetSafeNormal();
    }

    // Interpret Input2D as (Right, Up) in character-local space on the wall
    // Right → character right axis, Up → world up (Z)
    const FVector CharRight = CharOwner ? CharOwner->GetActorRightVector() : FVector::RightVector;
    const FVector WorldUp = FVector::UpVector;

    return (CharRight * Input2D.X + WorldUp * Input2D.Y).GetSafeNormal();
}

EClimbingDirection UACFLedgeClimbingComponent::ClassifyDirection(FVector WorldDir) const
{
    // Project onto the character's wall-aligned right and up axes
    const FVector CharRight = CharOwner ? CharOwner->GetActorRightVector() : FVector::RightVector;
    const FVector WorldUp = FVector::UpVector;

    const float HorizontalComponent = FVector::DotProduct(WorldDir, CharRight);
    const float VerticalComponent = FVector::DotProduct(WorldDir, WorldUp);

    const float AbsH = FMath::Abs(HorizontalComponent);
    const float AbsV = FMath::Abs(VerticalComponent);
    const float DiagThreshold = 0.35f; // ~sin(20°) — below this, it is considered pure axis

    if (AbsH < DiagThreshold && AbsV >= DiagThreshold)
    {
        return VerticalComponent >= 0.f ? EClimbingDirection::Up : EClimbingDirection::Down;
    }
    if (AbsH >= DiagThreshold && AbsV < DiagThreshold)
    {
        return HorizontalComponent >= 0.f ? EClimbingDirection::Right : EClimbingDirection::Left;
    }

    // Diagonal
    if (VerticalComponent >= 0.f)
    {
        return HorizontalComponent >= 0.f ? EClimbingDirection::UpRight : EClimbingDirection::UpLeft;
    }
    return HorizontalComponent >= 0.f ? EClimbingDirection::DownRight : EClimbingDirection::DownLeft;
}

bool UACFLedgeClimbingComponent::TriggerClimbAbility(EClimbingDirection Direction, UACFGripPointComponent* TargetGrip)
{
    if (!AbilityComp || !ClimbingMontageData)
    {
        return false;
    }

    const FGameplayTag AbilityTag = ClimbingMontageData->GetAbilityTagForDirection(Direction);
    if (!AbilityTag.IsValid())
    {
        return false;
    }

    // Store the pending grip so the ability can read it during warp setup
    CurrentGripPoint = TargetGrip;

    const bool bTriggered = AbilityComp->TriggerAction(AbilityTag, EActionPriority::EHigh);
    if (bTriggered)
    {
        bIsClimbing = true;
        OnGripChanged.Broadcast(TargetGrip, Direction);
        OnClimbingStateChanged.Broadcast(true);
    }
    else
    {
        // Roll back: ability failed to activate
        CurrentGripPoint = nullptr;
    }

    return bTriggered;
}

void UACFLedgeClimbingComponent::Server_JumpToGrip_Implementation(UACFGripPointComponent* TargetGrip, EClimbingDirection Direction)
{
    if (!TargetGrip)
    {
        return;
    }
    TriggerClimbAbility(Direction, TargetGrip);
}

void UACFLedgeClimbingComponent::SetClimbingMovementMode(bool bEnter)
{
    if (!CharOwner)
    {
        return;
    }

    UCharacterMovementComponent* MoveComp = CharOwner->GetCharacterMovement();
    if (!MoveComp)
    {
        return;
    }

    if (bFreezePawnWhileClimbing)
    {
        if (bEnter)
        {
            MoveComp->StopMovementImmediately();
            MoveComp->DisableMovement();
        }
        else
        {
            MoveComp->SetMovementMode(MOVE_Walking);
        }
    }
}

void UACFLedgeClimbingComponent::OnRep_CurrentGripPoint()
{
    // Notify locally-simulated clients so animations/UI can react
    if (CurrentGripPoint)
    {
        OnGripChanged.Broadcast(CurrentGripPoint, EClimbingDirection::Up);
    }
}

void UACFLedgeClimbingComponent::OnRep_IsClimbing()
{
    OnClimbingStateChanged.Broadcast(bIsClimbing);
    SetClimbingMovementMode(bIsClimbing);
}
