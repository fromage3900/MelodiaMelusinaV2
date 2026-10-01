#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Pawn.h"
#include "Components/ACFDamageHandlerComponent.h"
#include "Game/ACFDamageType.h"
#include "GenericTeamAgentInterface.h"
#include "Interfaces/ACFEntityInterface.h"
#include "Interfaces/ACFInteractableInterface.h"
#include "ACFBoatVehiclePawn.generated.h"

class UACFTeamComponent;
class USkeletalMeshComponent;
class UARSStatisticsComponent;
class UACFEffectsManagerComponent;
class UACFDamageHandlerComponent;
class UAIPerceptionStimuliSourceComponent;
class UACFMountableComponent;
class UACFMountPointComponent;
class UACFWaterVehicleComponent;

UCLASS()
class VEHICLESYSTEM_API AACFBoatVehiclePawn : public APawn,
    public IGenericTeamAgentInterface,
    public IACFEntityInterface,
    public IACFInteractableInterface {
    GENERATED_BODY()

public:
    AACFBoatVehiclePawn();

    // IACFEntityInterface
    UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = ACF)
    bool IsEntityAlive() const;
    virtual bool IsEntityAlive_Implementation() const override { return DamageHandlerComp->GetIsAlive(); }

    UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = ACF)
    float GetEntityExtentRadius() const;
    virtual float GetEntityExtentRadius_Implementation() const;

    // IACFInteractableInterface
    UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = ACF)
    bool CanBeInteracted(class APawn* Pawn);
    virtual bool CanBeInteracted_Implementation(class APawn* Pawn) override;

    UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = ACF)
    FText GetInteractableName();
    virtual FText GetInteractableName_Implementation() override;

    // Getters
    UFUNCTION(BlueprintPure, Category = ACF)
    FACFDamageEvent GetLastDamageInfo() const;

    UFUNCTION(BlueprintPure, Category = ACF)
    FORCEINLINE UARSStatisticsComponent* GetStatisticsComponent() const { return StatisticsComp; }

    UFUNCTION(BlueprintPure, Category = ACF)
    FORCEINLINE UACFDamageHandlerComponent* GetDamageHandlerComponent() const { return DamageHandlerComp; }

    UFUNCTION(BlueprintPure, Category = ACF)
    FORCEINLINE UACFMountableComponent* GetMountComponent() const { return MountComponent; }

    UFUNCTION(BlueprintPure, Category = ACF)
    FORCEINLINE USkeletalMeshComponent* GetMesh() const { return Mesh; }

    UFUNCTION(BlueprintPure, Category = ACF)
    FORCEINLINE UACFWaterVehicleComponent* GetWaterVehicleComponent() const { return WaterVehicleComp; }

    UFUNCTION(BlueprintNativeEvent, Category = ACF)
    void OnVehicleDestroyed();
    virtual void OnVehicleDestroyed_Implementation();

    // Team Interfaces
    virtual FGameplayTag GetEntityCombatTeam_Implementation() const override;
    virtual void AssignTeamToEntity_Implementation(FGameplayTag inCombatTeam) override;
    virtual FGenericTeamId GetGenericTeamId() const override;
    virtual void SetGenericTeamId(const FGenericTeamId& TeamID) override;
    virtual ETeamAttitude::Type GetTeamAttitudeTowards(const AActor& Other) const override;

protected:
    virtual void BeginPlay() override;
    virtual float TakeDamage(float Damage, FDamageEvent const& DamageEvent, AController* EventInstigator, AActor* DamageCauser) override;

    UPROPERTY(Category = Vehicle, VisibleDefaultsOnly, BlueprintReadOnly)
    TObjectPtr<USkeletalMeshComponent> Mesh;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = ACF)
    TObjectPtr<UARSStatisticsComponent> StatisticsComp;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = ACF)
    TObjectPtr<UACFEffectsManagerComponent> EffectsComp;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = ACF)
    TObjectPtr<UACFDamageHandlerComponent> DamageHandlerComp;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = ACF)
    TObjectPtr<UAIPerceptionStimuliSourceComponent> AIPerceptionStimuliSource;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = ACF)
    TObjectPtr<UACFMountableComponent> MountComponent;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = ACF)
    TObjectPtr<UACFTeamComponent> TeamComponent;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = ACF)
    TObjectPtr<UACFWaterVehicleComponent> WaterVehicleComp;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = ACF)
    FName VehicleName = "SampleBoat";

private:
    UFUNCTION()
    void HandleDeath();
};