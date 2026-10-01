// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2024. All Rights Reserved.

#include "ACFGripPointComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/CollisionProfile.h"
#include "Engine/World.h"
#include "GameFramework/Actor.h"

UACFGripPointComponent::UACFGripPointComponent()
{
    PrimaryComponentTick.bCanEverTick = false;
    InitSphereRadius(20.f);
    SetCollisionProfileName(UCollisionProfile::NoCollision_ProfileName);
    SetHiddenInGame(false);
    ShapeColor = FColor(0, 200, 100);
}

void UACFGripPointComponent::BeginPlay()
{
    Super::BeginPlay();
}

UPrimitiveComponent* UACFGripPointComponent::FindOwningMeshComponent() const
{
    AActor* Owner = GetOwner();
    if (!Owner)
    {
        return nullptr;
    }

    // Prefer the attachment parent if it is a mesh
    USceneComponent* ParentComponent = GetAttachParent();
    if (ParentComponent)
    {
        if (UPrimitiveComponent* AsPrimitive = Cast<UPrimitiveComponent>(ParentComponent))
        {
            return AsPrimitive;
        }
    }

    // Fall back: find any skeletal mesh first, then any static mesh
    if (USkeletalMeshComponent* SMC = Owner->FindComponentByClass<USkeletalMeshComponent>())
    {
        return SMC;
    }
    if (UStaticMeshComponent* StMC = Owner->FindComponentByClass<UStaticMeshComponent>())
    {
        return StMC;
    }

    return nullptr;
}

FVector UACFGripPointComponent::GetSurfaceNormal() const
{
    const UPrimitiveComponent* Mesh = FindOwningMeshComponent();
    if (!Mesh)
    {
        return GetForwardVector();
    }

    const FVector GripLoc = GetComponentLocation();

    // Line-trace outward from inside the mesh toward the grip to get the normal
    // We shoot from the mesh origin toward the grip and a bit beyond.
    const FVector MeshOrigin = Mesh->GetComponentLocation();
    const FVector Direction = (GripLoc - MeshOrigin).GetSafeNormal();

    const FVector TraceStart = GripLoc - Direction * 5.f;
    const FVector TraceEnd = GripLoc + Direction * 30.f;

    FHitResult Hit;
    FCollisionQueryParams Params;
    Params.AddIgnoredActor(GetOwner());

    if (GetWorld() && GetWorld()->LineTraceSingleByChannel(Hit, TraceStart, TraceEnd, ECC_Visibility, Params))
    {
        return Hit.Normal;
    }

    // Fallback: direction away from mesh centre
    return Direction * -1.f;
}

FTransform UACFGripPointComponent::GetCharacterAlignTransform() const
{
    const FVector SurfNormal = GetSurfaceNormal();
    const FVector GripLoc = GetComponentLocation();

    // The character should face the wall (into -normal)
    FRotator FacingRot = (-SurfNormal).Rotation();
    FacingRot.Pitch = 0.f; // keep character upright

    // Push the character slightly away from the wall so it doesn't clip
    const FVector CharLoc = GripLoc + SurfNormal * WallOffsetOverride.X;

    return FTransform(FacingRot, CharLoc);
}
