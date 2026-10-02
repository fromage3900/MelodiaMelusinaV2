// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "ACFBuildableEntityComponent.h"

#include "ACFBuildRecipe.h"
#include "ACFBuildingManagerComponent.h"
#include "Components/ACFInventoryComponent.h"
#include "Net/UnrealNetwork.h"
#include <GameFramework/PlayerState.h>
#include <GameFramework/PlayerController.h>
#include <CollisionQueryParams.h>
#include <Math/UnrealMathUtility.h>
#include <Math/Vector.h>
#include <CollisionShape.h>
#include <Engine/World.h>



UACFBuildableEntityComponent::UACFBuildableEntityComponent()
{
    BlockingChannels.Add(ECollisionChannel::ECC_WorldStatic);
    BlockingChannels.Add(ECollisionChannel::ECC_WorldDynamic);
    SetIsReplicatedByDefault(true);
}


void UACFBuildableEntityComponent::Build(APlayerController* BuilderPC, UACFBuildRecipe* recipe)
{
    if (IsValid(BuilderPC)) {
        BuilderPlayerState = BuilderPC->GetPlayerState<APlayerState>();
    }
    BuildingRecipe = recipe;
    // Dispatch event with builder reference
    OnBuilt.Broadcast(GetBuilderPlayerState());
}

void UACFBuildableEntityComponent::Dismantle(APlayerController* Instigator)
{

    // Dispatch event with instigator and original builder
    OnDismantled.Broadcast(Instigator, GetBuilderPlayerState());
}

bool UACFBuildableEntityComponent::CanBeDismantled_Implementation(APawn* Instigator) const
{

    return Instigator ? Instigator->GetPlayerState() == BuilderPlayerState : false;
}

UACFBuildingManagerComponent* UACFBuildableEntityComponent::GetBuildableManager(APawn* Pawn) const
{
    if (Pawn && Pawn->GetController()) {
        return Pawn->GetController()->GetComponentByClass<UACFBuildingManagerComponent>();
    }
    return nullptr;
}


bool UACFBuildableEntityComponent::IsPlacementValid_Implementation() const
{
    const AActor* Owner = GetOwner();
    if (!IsValid(Owner)) {
        return false;
    }

    const UWorld* World = Owner->GetWorld();
    if (!World) {
        return false;
    }

    // CRITICAL FIX: Use consistent reference point for all calculations
    // The bounding box changes with rotation, so we need to be careful
    const FBox Bounds = Owner->GetComponentsBoundingBox();
    const FVector BoundsCenter = Bounds.GetCenter();
    const FVector BoundsExtent = Bounds.GetExtent();

    // Setup collision query params once
    FCollisionQueryParams QueryParams;
    QueryParams.AddIgnoredActor(Owner);
    QueryParams.bTraceComplex = false; // Use simple collision for performance

    // ========================================
    // 1. GROUND CHECK - Use bounds center, not actor location
    // ========================================
    FHitResult GroundHit;

    // Trace from the center of the bounding box for consistency
    const FVector TraceStart = BoundsCenter + FVector(0.f, 0.f, 200.f);
    const FVector TraceEnd = BoundsCenter + FVector(0.f, 0.f, -2000.f);

    if (!World->LineTraceSingleByChannel(
            GroundHit,
            TraceStart,
            TraceEnd,
            ECC_Visibility,
            QueryParams)) {
        return false; // No ground found
    }

    // ========================================
    // 2. SLOPE CHECK
    // ========================================
    const float SlopeDegrees = FMath::RadiansToDegrees(
        FMath::Acos(FVector::DotProduct(GroundHit.ImpactNormal, FVector::UpVector)));

    if (SlopeDegrees > MaxAllowedSlope) {
        return false; // Slope too steep
    }

    // ========================================
    // 3. SETUP IGNORE LIST
    // ========================================

    // Ignore the ground/landscape we hit
    if (GroundHit.GetActor()) {
        QueryParams.AddIgnoredActor(GroundHit.GetActor());
    }
    /*
    // Ignore snap target if we're snapping to something
    const UACFBuildingSnapComponent* SnapComponent = Owner->GetComponentByClass<UACFBuildingSnapComponent>();
    if (SnapComponent) {
        const AActor* SnapTarget = SnapComponent->GetCurrentSnapActor();
        if (SnapTarget) {
            QueryParams.AddIgnoredActor(SnapTarget);

            // Also ignore all attached actors to the snap target
            TArray<AActor*> AttachedActors;
            SnapTarget->GetAttachedActors(AttachedActors);
            for (AActor* Attached : AttachedActors) {
                QueryParams.AddIgnoredActor(Attached);
            }
        }
    }*/

    // ========================================
    // 4. OVERLAP CHECK WITH PROPER ROTATION HANDLING
    // ========================================

    // Apply margin to avoid false positives when objects are perfectly aligned
    const FVector CollisionExtent = BoundsExtent - ShapeCollisionMargin;

    // Use oriented bounding box (OBB) for accurate collision after rotation
    const FCollisionShape CollisionShape = FCollisionShape::MakeBox(CollisionExtent);

    // Check each blocking channel
    for (const ECollisionChannel Channel : BlockingChannels) {

#if WITH_EDITOR
        if (bShowExtentDebug) {
            // Draw the actual collision box being tested
            DrawDebugBox(
                World,
                BoundsCenter,
                CollisionExtent,
                Owner->GetActorQuat(),
                FColor::Green,
                false,
                0.0f,
                0,
                2.0f);

            // Draw ground hit point
            DrawDebugSphere(
                World,
                GroundHit.Location,
                10.0f,
                12,
                FColor::Yellow,
                false,
                0.0f);

            // Draw trace line
            DrawDebugLine(
                World,
                TraceStart,
                GroundHit.Location,
                FColor::Blue,
                false,
                0.0f,
                0,
                1.0f);
        }
#endif

        // Perform overlap test using the bounds center and actor rotation
        if (World->OverlapBlockingTestByChannel(
                BoundsCenter, // Use bounds center for position
                Owner->GetActorQuat(), // Use actor quaternion for rotation
                Channel,
                CollisionShape,
                QueryParams)) {

#if WITH_EDITOR
            if (bShowExtentDebug) {
                // Draw red box when blocked
                DrawDebugBox(
                    World,
                    BoundsCenter,
                    CollisionExtent,
                    Owner->GetActorQuat(),
                    FColor::Red,
                    false,
                    2.0f, // Show for 2 seconds
                    0,
                    3.0f);
            }
#endif
            return false; // Blocked by something
        }
    }

    return true; // Placement is valid!
}

void UACFBuildableEntityComponent::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(UACFBuildableEntityComponent, BuildingRecipe);
    DOREPLIFETIME(UACFBuildableEntityComponent, BuilderPlayerState);
}
