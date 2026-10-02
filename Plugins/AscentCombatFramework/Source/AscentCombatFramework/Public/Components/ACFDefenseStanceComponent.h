// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "ARSTypes.h"
#include "Components/ACFEquipmentComponent.h"
#include "Components/ActorComponent.h"
#include "CoreMinimal.h"
#include "GameplayTagContainer.h"
#include "Game/ACFDamageType.h"
#include "Game/ACFTypes.h"

#include "ACFDefenseStanceComponent.generated.h"

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnDefenseStanceChanged, bool, bIsDefending);
DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnCounterAttackTriggered);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnDamageBlocked, const FACFDamageEvent&, blockedDamage);

UCLASS(ClassGroup = (ACF), Blueprintable, meta = (BlueprintSpawnableComponent))
class ASCENTCOMBATFRAMEWORK_API UACFDefenseStanceComponent : public UActorComponent {
    GENERATED_BODY()

public:
    // Sets default values for this component's properties
    UACFDefenseStanceComponent();

    /*Starts the Defense stance stance. During Defense stance, this character will try to block all the incoming damages*/
    UFUNCTION(Server, Reliable, BlueprintCallable, Category = ACF)
    void StartDefending();

    /*Interrupt the Defense stance stance. During Defense stance, this character will try to block all the incoming damages*/
    UFUNCTION(Server, Reliable, BlueprintCallable, Category = ACF)
    void StopDefending();

    /*Tries to block the provided damage, returns the Block Action executed*/
    UFUNCTION(BlueprintCallable, Category = ACF)
    virtual bool TryBlockIncomingDamage(const FACFDamageEvent& damageEvent, float damageToBlock, FGameplayTag& outAction);

    /*Returns true if the provided damage can be blocked*/
    UFUNCTION(BlueprintPure, Category = ACF)
    virtual bool CanBlockDamage(const FACFDamageEvent& damageEvent) const;

    UFUNCTION(BlueprintPure, Category = ACF)
    virtual bool CanStartDefensePosition() const;

    UFUNCTION(BlueprintPure, Category = ACF)
    bool IsInDefensePosition() const
    {
        return bIsInDefensePosition;
    }

    UFUNCTION(BlueprintPure, Category = ACF)
    FGameplayTag GetBlockAction() const
    {
        return ActionToBeTriggeredOnBlock;
    }

    UFUNCTION(BlueprintPure, Category = ACF)
    FGameplayAttribute GetDamagedAttribute() const
    {
        return DamagedAttribute;
    }

    UPROPERTY(BlueprintAssignable, Category = ACF)
    FOnDefenseStanceChanged OnDefenseStanceChanged;

    UPROPERTY(BlueprintAssignable, Category = ACF)
    FOnCounterAttackTriggered OnCounterAttackTriggered;

    UPROPERTY(BlueprintAssignable, Category = ACF)
    FOnDamageBlocked OnDamageBlocked;

    UFUNCTION(BlueprintPure, Category = ACF)
    class UACFBlockComponent* GetCurrentBlockComp() const { return currentBlockComp; }

    // Enables the counter-attack window
    UFUNCTION(BlueprintPure, Category = ACF)
    float GetDamagedStatisticMultiplier() const;

    UFUNCTION(BlueprintCallable, Category = ACF)
    void EnableCounterAttackWindow()
    {
        bCounterGate = true;
    }

    // Disables the counter-attack window
    UFUNCTION(BlueprintCallable, Category = ACF)
    void DisableCounterAttackWindow()
    {
        bCounterGate = false;
    }

    // Initiates the parry
    UFUNCTION(BlueprintCallable, Category = ACF)
    virtual void StartParry();

    // Stops the parry
    UFUNCTION(BlueprintCallable, Category = ACF)
    virtual void StopParry();

    // Determines if the parry action can currently be performed.
    UFUNCTION(BlueprintPure, Category = ACF)
    virtual bool CanParry() const;

    // Checks if the character is currently in a parrying state
    UFUNCTION(BlueprintPure, Category = ACF)
    bool IsParrying() const
    {
        return bParryGate;
    }

    /*Determines whether this attack is counterable*/
    UFUNCTION(BlueprintCallable, Category = ACF)
    virtual bool CanCounterAttack(const FACFDamageEvent& incomingDamage);

    /*Tries to counter the incoming damage*/
    UFUNCTION(BlueprintCallable, Category = ACF)
    virtual bool TryCounterAttack(const FACFDamageEvent& incomingDamage, FGameplayTag& outCounterAction);

    UFUNCTION(BlueprintPure, Category = ACF)
    FGameplayTag GetActionToBeTriggeredOnParry() const { return ActionToBeTriggeredOnParry; }

    UFUNCTION(BlueprintCallable, Category = ACF)
    void SetActionToBeTriggeredOnParry(FGameplayTag val) { ActionToBeTriggeredOnParry = val; }

protected:
    // Called when the game starts
    virtual void BeginPlay() override;

    /*To start go in DefenseMode, minimum value of the DamagedStatistic to start defense mode*/
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = ACF)
    float MinimumDamageStatisticToStartBlocking = 5.f;

    //**ACTIONS**//

    /*Action triggered on the owner of this component when the defence is broken*/
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly,meta = (Categories = "Actions"), Category = ACF)
    FGameplayTag ActionToBeTriggeredOnDefenceBreak;

    /*Action triggered on the owner of this component when an hit is successfully blocked*/
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, meta = (Categories = "Actions"),Category = ACF)
    FGameplayTag ActionToBeTriggeredOnBlock;

    /*Priority of the Action triggered on the owner of this component when an hit is successfully blocked*/
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = ACF)
    EActionPriority ActionToBeTriggeredOnBlockPriority = EActionPriority::EMedium;

    /** If the character is performing one of these actions (current action tag matches), incoming damage cannot be blocked. Empty = no restriction from active actions. */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, meta = (Categories = "Actions"), Category = ACF)
    TArray<FGameplayTag> ActionsThatPreventBlocking;

    /*Action triggered on the owner of this component when an hit is successfully parried*/
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, meta = (Categories = "Actions"), Category = ACF)
    FGameplayTag ActionToBeTriggeredOnParry;

    /*Action triggered on the owner of this component when an hit is successfully countered*/
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, meta = (Categories = "Actions"),Category = ACF)
    FGameplayTag CounterAttackAction;

    /*LocomotionState to be activated while blocking*/
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = ACF)
    ELocomotionState LocomotionStateWhileBlocking;

    /*Damage received during Defense will be  removed from this Attribute.
    When this Attribute reaches 0, defense will be broken
    Usually, damaged statistic is Stamina*/
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "ACF|GAS")
    FGameplayAttribute DamagedAttribute;


    UFUNCTION(BlueprintPure, Category = ACF)
    virtual class UACFBlockComponent* TryGetBestBlockComp() const;

    UFUNCTION()
    void OnRep_DefPos();

    UFUNCTION(BlueprintPure, Category = ACF)
    class UARSStatisticsComponent* GetStatisticsComponent() const { return statComp; }

    UFUNCTION(BlueprintPure, Category = ACF)
    class UACFCharacterMovementComponent* GetCharacterMovementComponent() const { return locComp; }

    UPROPERTY(ReplicatedUsing = OnRep_DefPos)
    bool bIsInDefensePosition = false;

    UPROPERTY(Replicated)
    bool bCounterGate = false;

    UPROPERTY(Replicated)
    bool bParryGate = false;

    TObjectPtr<class UARSStatisticsComponent> statComp;
    TObjectPtr<class UACFCharacterMovementComponent> locComp;
    TObjectPtr<class UACFBlockComponent> currentBlockComp;

    UFUNCTION()
    void HandleEquipmentChanged(const FEquipment& Equipment);

    bool IsAttackBlocked(AActor* Receiver, AActor* Attacker, float inMaxBlockAngleDegrees) const;
    FActiveGameplayEffectHandle defendingModifierHandle;

    UAbilitySystemComponent* GetAbilityComponent() const;
    FActiveGameplayEffectHandle AddGASModifierToOwner(const TSubclassOf<UGameplayEffect>& gameplayModifier, float level = 1.f);
    void RemoveGASModifierToOwner(const FActiveGameplayEffectHandle& modifierHandle);
};
