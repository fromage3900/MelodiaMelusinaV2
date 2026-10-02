// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "Components/ACFDamageHandlerComponent.h"
#include "CoreMinimal.h"
#include "Game/ACFDamageType.h"
#include "Game/ACFTypes.h"
#include "GameFramework/Actor.h"
#include "Interfaces/ACFEntityInterface.h"
#include <GameFramework/Pawn.h>
#include <GenericTeamAgentInterface.h>
#include "Components/ACFTeamComponent.h"

#include "ACFActor.generated.h"

class UACFTeamComponent;

UCLASS()
class ASCENTCOMBATFRAMEWORK_API AACFActor : public APawn,
                                            public IGenericTeamAgentInterface,
                                            public IACFEntityInterface {
    GENERATED_BODY()

public:
    // Sets default values for this actor's properties
    AACFActor();

protected:
    // Called when the game starts or when spawned
    virtual void BeginPlay() override;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = ACF)
    TObjectPtr<class UARSStatisticsComponent> StatisticsComp;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = ACF)
    TObjectPtr<class UACFEffectsManagerComponent> EffetsComp;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = ACF)
    TObjectPtr<class UACFEquipmentComponent> EquipmentComp;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = ACF)
    TObjectPtr<class UACFDamageHandlerComponent> DamageHandlerComp;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = ACF)
    TObjectPtr<class UAudioComponent> AudioComp;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = ACF)
    TObjectPtr<class UPrimitiveComponent> RootComp;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = ACF)
    TObjectPtr<UACFTeamComponent> TeamComponent;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = ACF)
    TObjectPtr<class UAIPerceptionStimuliSourceComponent> AIPerceptionStimuliSource;

    UFUNCTION(BlueprintNativeEvent, Category = ACF)
    void OnActorDestroyed();
    virtual void OnActorDestroyed_Implementation();

public:
    virtual float TakeDamage(float Damage, FDamageEvent const& DamageEvent, AController* EventInstigator, AActor* DamageCauser) override;

    UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = ACF)
    bool IsEntityAlive() const;
    virtual bool IsEntityAlive_Implementation() const override
    {
        return DamageHandlerComp->GetIsAlive();
    }

    UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = ACF)
    float GetEntityExtentRadius() const;
    virtual float GetEntityExtentRadius_Implementation() const;

    UFUNCTION(BlueprintPure, Category = ACF)
    FACFDamageEvent GetLastDamageInfo() const;

    UFUNCTION(BlueprintPure, Category = ACF)
    FORCEINLINE class UARSStatisticsComponent* GetStatisticsComponent() const { return StatisticsComp; }

    UFUNCTION(BlueprintPure, Category = ACF)
    FORCEINLINE class UACFEquipmentComponent* GetEquipmentComponent() const { return EquipmentComp; }

    UFUNCTION(BlueprintPure, Category = ACF)
    FORCEINLINE class UACFDamageHandlerComponent* GetDamageHandlerComponent() const { return DamageHandlerComp; }

    /**
     * Returns the combat team assigned to this AI controller.
     *
     * @return The current ETeam value assigned to this controller.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    FORCEINLINE FGameplayTag GetCombatTeam() const { return TeamComponent->GetTeam(); }

    /// <summary>
    /// /Combat Team Interface
    /// </summary>

    // IACFEntityInterface - Main implementation (source of truth)
    virtual FGameplayTag GetEntityCombatTeam_Implementation() const override;
    virtual void AssignTeamToEntity_Implementation(FGameplayTag inCombatTeam) override;

    // IGenericTeamAgentInterface - Read from TeamComponent
    virtual FGenericTeamId GetGenericTeamId() const override;
    virtual void SetGenericTeamId(const FGenericTeamId& TeamID) override;
    virtual ETeamAttitude::Type GetTeamAttitudeTowards(const AActor& OtherTeam) const override;

    /// <summary>
    /// /End Combat Team Entity
    /// </summary>

private:
    UFUNCTION()
    void HandleDeath();
};
