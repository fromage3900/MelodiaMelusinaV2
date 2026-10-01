// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "Components/ACFDamageHandlerComponent.h"
#include "CoreMinimal.h"
#include "Game/ACFDamageType.h"
#include "GenericTeamAgentInterface.h"
#include "Interfaces/ACFEntityInterface.h"
#include "Interfaces/ACFInteractableInterface.h"
#include "WheeledVehiclePawn.h"

#include "ACFWheeledVehiclePawn.generated.h"

class UACFTeamComponent;

/**
 * Represents a wheeled vehicle pawn that integrates with ACF combat and interaction systems.
 */
UCLASS()
class VEHICLESYSTEM_API AACFWheeledVehiclePawn : public AWheeledVehiclePawn,
                                                 public IGenericTeamAgentInterface,
                                                 public IACFEntityInterface,
                                                 public IACFInteractableInterface {
    GENERATED_BODY()

public:
    /**
     * Default constructor.
     */
    AACFWheeledVehiclePawn();

    /**
     * Checks if the vehicle entity is alive.
     * @return True if the vehicle is still operational, false otherwise.
     */
    UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = ACF)
    bool IsEntityAlive() const;
    virtual bool IsEntityAlive_Implementation() const override { return DamageHandlerComp->GetIsAlive(); }

    /**
     * Retrieves the extent radius of the entity.
     * @return The radius of the vehicle.
     */
    UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = ACF)
    float GetEntityExtentRadius() const;
    virtual float GetEntityExtentRadius_Implementation() const;

    /**
     * Checks if the vehicle can be interacted with by a specific pawn.
     * @param Pawn The pawn attempting to interact.
     * @return True if the vehicle can be interacted with, false otherwise.
     */
    UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = ACF)
    bool CanBeInteracted(class APawn* Pawn);
    virtual bool CanBeInteracted_Implementation(class APawn* Pawn) override;

    /**
     * Retrieves the name of the interactable object.
     * @return The name of the vehicle.
     */
    UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = ACF)
    FText GetInteractableName();
    virtual FText GetInteractableName_Implementation() override;

    /**
     * Retrieves the last recorded damage event on this vehicle.
     * @return The last damage event details.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    FACFDamageEvent GetLastDamageInfo() const;

    /**
     * Retrieves the statistics component of the vehicle.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    FORCEINLINE class UARSStatisticsComponent* GetStatisticsComponent() const { return StatisticsComp; }

    /**
     * Retrieves the damage handler component of the vehicle.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    FORCEINLINE class UACFDamageHandlerComponent* GetDamageHandlerComponent() const { return DamageHandlerComp; }

    /**
     * Retrieves the mountable component of the vehicle.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    FORCEINLINE class UACFMountableComponent* GetMountComponent() const { return MountComponent; }

    /**
     * Retrieves the dismount point of the vehicle.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    FORCEINLINE class UACFMountPointComponent* GetDismountPoint() const { return DismountPoint; }

    /**
     * Called when the vehicle is destroyed.
     */
    UFUNCTION(BlueprintNativeEvent, Category = ACF)
    void OnVehicleDestroyed();
    virtual void OnVehicleDestroyed_Implementation();

    /// <summary>
    /// /Combat Team Interface
    /// </summary>

    // IACFEntityInterface - Main implementation (source of truth)
    virtual FGameplayTag GetEntityCombatTeam_Implementation() const override;
    virtual void AssignTeamToEntity_Implementation(FGameplayTag inCombatTeam) override;

    // IGenericTeamAgentInterface - Read from TeamComponent
    virtual FGenericTeamId GetGenericTeamId() const override;
    virtual void SetGenericTeamId(const FGenericTeamId& TeamID) override;
    virtual ETeamAttitude::Type GetTeamAttitudeTowards(const AActor& Other) const override;

    /// <summary>
    /// /End Combat Team Entity
    /// </summary>

protected:
    /**
     * Called when the game starts or when spawned.
     */
    virtual void BeginPlay() override;

    /**
     * Handles the vehicle taking damage.
     */
    virtual float TakeDamage(float Damage, FDamageEvent const& DamageEvent, AController* EventInstigator, AActor* DamageCauser) override;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = ACF)
    TObjectPtr<class UARSStatisticsComponent> StatisticsComp;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = ACF)
    TObjectPtr<class UACFEffectsManagerComponent> EffetsComp;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = ACF)
    TObjectPtr<class UACFDamageHandlerComponent> DamageHandlerComp;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = ACF)
    TObjectPtr<class UAIPerceptionStimuliSourceComponent> AIPerceptionStimuliSource;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = ACF)
    TObjectPtr<class UACFMountableComponent> MountComponent;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = ACF)
    TObjectPtr<class UACFMountPointComponent> DismountPoint;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = ACF)
    TObjectPtr<UACFTeamComponent> TeamComponent;

    /**
     * The name of the vehicle.
     */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = ACF)
    FName VehicleName = "SampleCar";

private:
    UFUNCTION()
    void HandleDeath();
};
