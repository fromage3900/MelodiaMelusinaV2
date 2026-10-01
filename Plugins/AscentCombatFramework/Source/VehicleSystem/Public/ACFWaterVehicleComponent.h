// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "ACFWaterVehicleComponent.generated.h"

class USkeletalMeshComponent;
class UPrimitiveComponent;

/**
 * Drives physics-based water vehicle movement (thrust + steering).
 * At BeginPlay auto-resolves the target mesh with this priority:
 *   1. SkeletalMeshComponent tagged with PhysicsMeshTag (if set)
 *   2. First simulating SkeletalMeshComponent on the owner
 *   3. First simulating PrimitiveComponent on the owner
 */
UCLASS(ClassGroup = ACF, meta = (BlueprintSpawnableComponent), DisplayName = "ACF Water Vehicle Component")
class VEHICLESYSTEM_API UACFWaterVehicleComponent : public UActorComponent
{
    GENERATED_BODY()

public:
    UACFWaterVehicleComponent();

    /** Applies a physics force along the owner's forward direction. Value: -1..1. */
    UFUNCTION(BlueprintCallable, Category = "ACF|Water Vehicle")
    void AddThrust(float Value);

    /** Applies a physics torque around Z to steer the vehicle. Value: -1..1. */
    UFUNCTION(BlueprintCallable, Category = "ACF|Water Vehicle")
    void AddSteering(float Value);

    /** Returns the physics mesh resolved at BeginPlay. */
    UFUNCTION(BlueprintPure, Category = "ACF|Water Vehicle")
    UPrimitiveComponent* GetPhysicsMesh() const { return PhysicsMesh.Get(); }

    /** Overrides the cached physics mesh manually. Useful when the target mesh is assigned after BeginPlay. */
    UFUNCTION(BlueprintCallable, Category = "ACF|Water Vehicle")
    void SetPhysicsMesh(UPrimitiveComponent* InMesh) { PhysicsMesh = InMesh; }


protected:
    virtual void BeginPlay() override;
    virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

    /** Optional tag to identify the target SkeletalMeshComponent. Leave None to auto-pick. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|Water Vehicle|Setup")
    FName PhysicsMeshTag = NAME_None;

    /** Impulse applied along the forward axis per unit of input. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|Water Vehicle|Movement", meta = (ClampMin = "0"))
    float ThrustForce = 25000.f;

    /** Torque applied around Z per unit of input. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|Water Vehicle|Movement", meta = (ClampMin = "0"))
    float SteeringTorque = 2500.f;

    /** When true, horizontal velocity is progressively steered toward the forward direction to prevent lateral drift on turns. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|Water Vehicle|Movement")
    bool bAlignVelocityToForward = true;

    /** Degrees per second at which velocity tracks the forward vector. Higher = snappier, lower = more drift. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|Water Vehicle|Movement",
        meta = (EditCondition = "bAlignVelocityToForward", ClampMin = "0"))
    float VelocityAlignmentSpeed = 180.f;

private:
    void ResolvePhysicsMesh();
    void TickVelocityAlignment(float DeltaTime);

    UPROPERTY()
    TObjectPtr<UPrimitiveComponent> PhysicsMesh;
};
