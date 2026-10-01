// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Actors/ACFActor.h"
#include "ACFFlyingVehicle.generated.h"

class UACFFlyComponent;
class UInputMappingContext;
class USkeletalMeshComponent;
class USceneComponent;

/**
 * Pawn that hosts the spaceship: skeletal mesh + UACFFlyComponent (kinematic 6DOF
 * movement; replicated pose via normal pawn movement replication).
 *
 * The skeletal mesh is the RootComponent and is used as the FlyComponent's UpdatedComponent
 * so all movement sweeps (SafeMoveUpdatedComponent) test the Physics Asset bodies of the
 * ship instead of a single capsule. This is what stops large hulls/wings from clipping
 * through terrain or enemies.
 *
 */
UCLASS()
class VEHICLESYSTEM_API AACFFlyingVehicle : public AACFActor
{
    GENERATED_BODY()

public:
    AACFFlyingVehicle();

    UFUNCTION(BlueprintPure, Category = "ACF|Vehicle")
    UACFFlyComponent* GetFlyComponent() const { return FlyComponent; }

    /**
     * Skeletal mesh: visual representation, gameplay interaction surface AND root component.
     * It is the UpdatedComponent of the FlyComponent so SafeMoveUpdatedComponent sweeps the
     * Physics Asset bodies of the ship instead of a loose capsule, eliminating the wing/hull
     * compenetration with terrain and other actors. Collision profile and Physics Asset are
     * configurable per child Blueprint.
     */
    UFUNCTION(BlueprintPure, Category = "ACF|Vehicle")
    USkeletalMeshComponent* GetMesh() const { return Mesh; }

    /**
     * InputMappingContext registered on the locally controlling PlayerController when this Pawn
     * is possessed (added in PawnClientRestart, removed in UnPossessed and again in EndPlay as a
     * safety net). Configure the actions you use for the spaceship inside this asset.
     *
     * Note: do not move the add to PossessedBy alone. For networked games the owning client
     * typically receives possession via ClientRestart -> DispatchRestart -> PawnClientRestart
     * (SetController on the pawn) without going through PossessedBy on that client copy;
     * PawnClientRestart also runs after the default pawn input component setup.
     */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|Input")
    TObjectPtr<UInputMappingContext> InputMappingContext;

    /** Priority used when registering InputMappingContext on the EnhancedInputLocalPlayerSubsystem. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|Input")
    int32 InputMappingPriority = 0;

protected:
    virtual void BeginPlay() override;
    virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

    /** Called locally on the controlling client when a PlayerController takes possession. */
    virtual void PawnClientRestart() override;

    /** Remove spaceship input when leaving the vehicle (call Remove before Super: base clears Controller). */
    virtual void UnPossessed() override;
    

private:
    /** Adds InputMappingContext to the EnhancedInput subsystem of the controlling LocalPlayer. */
    void AddSpaceshipMappingContext();

    /** Removes InputMappingContext from the EnhancedInput subsystem if it was previously added. */
    void RemoveSpaceshipMappingContext();

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "ACF|Vehicle", meta = (AllowPrivateAccess = "true"))
    TObjectPtr<UACFFlyComponent> FlyComponent;
    
    /**
     * Root skeletal mesh. Drives BOTH visual representation and movement collision: the
     * FlyComponent uses it as its UpdatedComponent so SafeMoveUpdatedComponent sweeps the
     * Physics Asset bodies of the ship.
     *
     * Defaults set in the constructor are kinematic (bSimulatePhysics=false) with the
     * Pawn collision profile; child Blueprints are expected to override the collision
     * profile and the Physics Asset to fit the actual ship hull.
     *
     * Named "CharacterMesh0" to match the ACharacter convention.
     */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "ACF|Vehicle", meta = (AllowPrivateAccess = "true"))
    TObjectPtr<USkeletalMeshComponent> Mesh;
};
