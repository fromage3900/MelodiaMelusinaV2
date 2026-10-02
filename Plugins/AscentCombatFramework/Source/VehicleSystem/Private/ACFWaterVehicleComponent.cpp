// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ACFWaterVehicleComponent.h"
#include "ACFBoatVehiclePawn.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/PrimitiveComponent.h"
#include "GameFramework/Actor.h"

UACFWaterVehicleComponent::UACFWaterVehicleComponent()
{
    PrimaryComponentTick.bCanEverTick = true;
}

void UACFWaterVehicleComponent::BeginPlay()
{
    Super::BeginPlay();
    ResolvePhysicsMesh();
}

void UACFWaterVehicleComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
    Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

    if (bAlignVelocityToForward)
    {
        TickVelocityAlignment(DeltaTime);
    }
}

void UACFWaterVehicleComponent::AddThrust(float Value)
{
    UPrimitiveComponent* Mesh = PhysicsMesh.Get();
    if (!Mesh || !Mesh->IsSimulatingPhysics() || FMath::IsNearlyZero(Value))
    {
        return;
    }

    const FVector Forward = GetOwner()->GetActorForwardVector();
    const FVector FlatForward = FVector(Forward.X, Forward.Y, 0.f).GetSafeNormal();
    Mesh->AddImpulse(FlatForward * ThrustForce * Value);
}

void UACFWaterVehicleComponent::AddSteering(float Value)
{
    UPrimitiveComponent* Mesh = PhysicsMesh.Get();
    if (!Mesh || !Mesh->IsSimulatingPhysics() || FMath::IsNearlyZero(Value))
    {
        return;
    }

    Mesh->AddTorqueInDegrees(FVector(0.f, 0.f, SteeringTorque * Value));
}

void UACFWaterVehicleComponent::ResolvePhysicsMesh()
{
    AActor* Owner = GetOwner();
    if (!Owner)
    {
        return;
    }

    if (PhysicsMeshTag == NAME_None)
    {
        if (AACFBoatVehiclePawn* Boat = Cast<AACFBoatVehiclePawn>(Owner))
        {
            PhysicsMesh = Boat->GetMesh();
            return;
        }
    }
    else
    {
        TArray<USkeletalMeshComponent*> SkelMeshes;
        Owner->GetComponents<USkeletalMeshComponent>(SkelMeshes);
        for (USkeletalMeshComponent* Comp : SkelMeshes)
        {
            if (Comp->ComponentHasTag(PhysicsMeshTag))
            {
                PhysicsMesh = Comp;
                return;
            }
        }
    }

    UE_LOG(LogTemp, Warning,
        TEXT("ACFWaterVehicleComponent on [%s]: no simulating-physics mesh found. "
             "Thrust and steering will have no effect."),
        *Owner->GetName());
}

void UACFWaterVehicleComponent::TickVelocityAlignment(float DeltaTime)
{
    UPrimitiveComponent* Mesh = PhysicsMesh.Get();
    if (!Mesh || !Mesh->IsSimulatingPhysics())
    {
        return;
    }

    const FVector Velocity = Mesh->GetPhysicsLinearVelocity();
    const FVector HorizontalVel(Velocity.X, Velocity.Y, 0.f);
    const float HorizontalSpeed = HorizontalVel.Size();
    if (HorizontalSpeed < 1.f)
    {
        return;
    }

    const FVector RawForward = GetOwner()->GetActorForwardVector();
    const FVector FlatForward = FVector(RawForward.X, RawForward.Y, 0.f).GetSafeNormal();

    // Right vector in the XY plane, perpendicular to forward
    const FVector FlatRight = FVector::CrossProduct(FVector::UpVector, FlatForward);

    // Lateral (sideways) velocity component — this is the drift we want to kill
    const float LateralSpeed = FVector::DotProduct(HorizontalVel, FlatRight);
    const float MaxCorrection = VelocityAlignmentSpeed * DeltaTime;
    const float Correction = FMath::Clamp(-LateralSpeed, -MaxCorrection, MaxCorrection);

    // Only push in XY to cancel lateral drift — Z is never touched, buoyancy owns it
    Mesh->AddImpulse(FlatRight * Correction * Mesh->GetMass());
}
