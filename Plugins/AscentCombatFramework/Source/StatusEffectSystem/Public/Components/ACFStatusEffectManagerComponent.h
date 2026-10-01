// // Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include <GameplayTagContainer.h>
#include "ACFStatusTypes.h"
#include <Components/ActorComponent.h>

#include "ACFStatusEffectManagerComponent.generated.h"



UCLASS(ClassGroup = (ACF), Blueprintable, meta = (BlueprintSpawnableComponent))
class STATUSEFFECTSYSTEM_API UACFStatusEffectManagerComponent : public UActorComponent {
    GENERATED_BODY()

public:
    UACFStatusEffectManagerComponent();

    // Called every frame
    virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

    UFUNCTION(BlueprintPure, Category = "ACF")
    bool IsAffectedByStatusEffect(FGameplayTag StatusEffectTag);

    UFUNCTION(BlueprintPure, Category = "ACF")
    TArray<FStatusEffect> GetActiveEffects() const {
        return StatusEffects;
    }

    UFUNCTION(BlueprintCallable,  Category = "ACF")
    void AddStatusEffect(UACFBaseStatusEffect* StatusEffect, AActor* instigator = nullptr);

    UFUNCTION(BlueprintCallable, Server, Reliable,Category = "ACF")
    void RemoveStatusEffect(FGameplayTag StatusEffectTag);

    UFUNCTION(BlueprintCallable, Server, Reliable,Category = "ACF")
    void CreateAndApplyStatusEffect(TSubclassOf<UACFBaseStatusEffect> StatusEffectToConstruct, AActor* instigator = nullptr);

    UPROPERTY(BlueprintAssignable, Category = "ACF")
    FOnStatusEffectChanged OnStatusStarted;

    UPROPERTY(BlueprintAssignable, Category = "ACF")
    FOnStatusEffectChanged OnStatusRemoved;

    UPROPERTY(BlueprintAssignable, Category = "ACF")
    FOnStatusEffectChanged OnStatusRetriggered;

   UPROPERTY(BlueprintAssignable, Category = "ACF")
    FOnAnyStatusChanged OnAnyStatusChanged;
    

protected:
    friend class UACFBaseStatusEffect;


    // Called when the game starts
    virtual void BeginPlay() override;

   // virtual void CreateAndApplyStatusEffect_Implementation(TSubclassOf<UACFBaseStatusEffect> StatusEffectToConstruct);

private:

    UPROPERTY(ReplicatedUsing = OnRep_StatusEffects)
    TArray<FStatusEffect> StatusEffects;

    UFUNCTION()
    void OnRep_StatusEffects();

    TObjectPtr<class UARSStatisticsComponent> StatisticComp;

    TObjectPtr<class ACharacter> CharacterOwner;

    UFUNCTION()
    void Internal_RemoveStatusEffect(FGameplayTag StatusEffectTag);
 
 };