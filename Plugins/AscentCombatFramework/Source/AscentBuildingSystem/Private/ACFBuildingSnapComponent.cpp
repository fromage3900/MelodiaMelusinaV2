// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ACFBuildingSnapComponent.h"

#include "ACFBuildingSnapPointComponent.h"
#include "Engine/Engine.h"
#include "Kismet/GameplayStatics.h"

UACFBuildingSnapComponent::UACFBuildingSnapComponent()
{
    PrimaryComponentTick.bCanEverTick = true;
    PrimaryComponentTick.bStartWithTickEnabled = true;
}

void UACFBuildingSnapComponent::BeginPlay()
{
    Super::BeginPlay();
    UpdateSnapTargetsCache();
    if (auto* Owner = GetOwner()) {
        Owner->GetComponents<UACFBuildingSnapPointComponent>(SnapPoints);
    }
}

void UACFBuildingSnapComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
    Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

    if (!bSnapEnabled) {
        return;
    }

    // Update cache periodically
    LastCacheUpdate += DeltaTime;
    if (LastCacheUpdate >= CacheUpdateInterval) {
        UpdateSnapTargetsCache();
        LastCacheUpdate = 0.0f;
    }
}

UACFBuildingSnapComponent* UACFBuildingSnapComponent::FindNearestSnapTarget()
{
    const auto* const Owner = GetOwner();
    if (!IsValid(Owner)) {
        return nullptr;
    }

    UACFBuildingSnapComponent* NearestTarget = nullptr;
    float NearestDistance = FLT_MAX;

    TArray<FVector> MySnapPoints = GetWorldSnapPoints();

    for (auto* PotentialTarget : CachedSnapTargets) {
        if (!IsValid(PotentialTarget) || PotentialTarget == this) {
            continue;
        }

        TArray<FVector> TargetSnapPoints = PotentialTarget->GetWorldSnapPoints();

        // Check all combinations of snap points
        for (const FVector& MyPoint : MySnapPoints) {
            for (const FVector& TargetPoint : TargetSnapPoints) {
                const float Distance = FVector::Dist(MyPoint, TargetPoint);
                if (Distance < NearestDistance && Distance <= SnapDistance) {
                    NearestDistance = Distance;
                    NearestTarget = PotentialTarget;
                }
            }
        }
    }

    return NearestTarget;
}

bool UACFBuildingSnapComponent::SnapToTarget(const UACFBuildingSnapComponent* const Target)
{
    auto* const Owner = GetOwner();
    if (!IsValid(Target) || !IsValid(Owner)) {
        return false;
    }

    const TArray<FVector> MySnapPoints = GetWorldSnapPoints();
    const TArray<FVector> TargetSnapPoints = Target->GetWorldSnapPoints();

    float BestDistance = UE_BIG_NUMBER;
    FVector BestSnapPosition = Owner->GetActorLocation();

    // Find the closest snap point combination
    for (int32 i = 0; i < MySnapPoints.Num(); ++i) {
        for (int32 j = 0; j < TargetSnapPoints.Num(); ++j) {
            const float Distance = FVector::Dist(MySnapPoints[i], TargetSnapPoints[j]);
            if (Distance <= SnapDistance && Distance < BestDistance) {
                BestDistance = Distance;
                BestSnapPosition = CalculateSnapPosition(MySnapPoints[i], TargetSnapPoints[j]);
            }
        }
    }

    if (BestDistance <= SnapTolerance) {
        Owner->SetActorLocation(BestSnapPosition);
        return true;
    }

    return false;
}

TArray<FVector> UACFBuildingSnapComponent::GetWorldSnapPoints() const
{
    TArray<FVector> WorldSnapPoints;
    const auto* const Owner = GetOwner();

    if (!IsValid(Owner)) {
        return WorldSnapPoints;
    }

    const FVector ActorLocation = Owner->GetActorLocation();
    const FRotator ActorRotation = Owner->GetActorRotation();

    for (const auto* LocalPoint : SnapPoints) {
        if (IsValid(LocalPoint)) {
            WorldSnapPoints.Add(LocalPoint->GetComponentLocation());
        }
    }

    return WorldSnapPoints;
}

bool UACFBuildingSnapComponent::TrySnap()
{
    if (!bSnapEnabled) {
        return false;
    }

    UACFBuildingSnapComponent* NearestTarget = FindNearestSnapTarget();
    if (IsValid(NearestTarget) && SnapToTarget(NearestTarget)) {
        SetCurrentSnapActor(NearestTarget->GetOwner());
        return true;
    }
    SetCurrentSnapActor(nullptr);
    return  false;
}

FVector UACFBuildingSnapComponent::CalculateSnapPosition(const FVector& MyPoint, const FVector& TargetPoint) const
{
    if (!GetOwner()) {
        return FVector::ZeroVector;
    }

    const FVector CurrentLocation = GetOwner()->GetActorLocation();
    const FVector Offset = TargetPoint - MyPoint;

    FVector NewLocation = CurrentLocation + Offset;

    // Optionally disable vertical snapping
    if (!bSnapVertically) {
        NewLocation.Z = CurrentLocation.Z;
    }

    return NewLocation;
}

bool UACFBuildingSnapComponent::IsWithinSnapDistance(const FVector& Point1, const FVector& Point2) const
{
    const float Distance = FVector::Dist(Point1, Point2);
    return Distance <= SnapDistance;
}

void UACFBuildingSnapComponent::UpdateSnapTargetsCache()
{
    CachedSnapTargets.Empty();
    const auto* const Owner = GetOwner();
    if (!IsValid(Owner) || !IsValid(Owner->GetWorld())) {
        return;
    }

    // Find all actors with snap components
    TArray<AActor*> AllActors;
    UGameplayStatics::GetAllActorsOfClass(Owner->GetWorld(), AActor::StaticClass(), AllActors);

    for (auto* const Actor : AllActors) {
        if (Actor != Owner) {
            auto* const SnapComp = Actor->GetComponentByClass<UACFBuildingSnapComponent>();
            if (IsValid(SnapComp)) {
                CachedSnapTargets.Add(SnapComp);
            }
        }
    }
}
