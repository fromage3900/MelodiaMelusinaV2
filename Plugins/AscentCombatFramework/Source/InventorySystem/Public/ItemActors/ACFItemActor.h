// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"

#include "ACFItemActor.generated.h"

class UAbilitySystemComponent;
struct FActiveGameplayEffectHandle;
class UGameplayEffect;
class UACFItem;

UCLASS()
class INVENTORYSYSTEM_API AACFItemActor : public AActor {
    GENERATED_BODY()

public:
    // Sets default values for this actor's properties
    AACFItemActor();

    /**
     *  Sets the owning Pawn of this item.
     * @param inOwner The Pawn who owns this item. Must be valid.
     */
    void SetItemOwner(APawn* inOwner)
    {
        check(inOwner); // Ensure at runtime
        ItemOwner = inOwner;
    }

    UFUNCTION(BlueprintPure, Category = ACF)
    UACFItem* GetItemDefinition() const
    {
        return ItemDefinition;
    }

    /**
     *  Gets the owning Pawn of this item.
     * @return A valid pointer to the Pawn that owns this item.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    FORCEINLINE class APawn* GetItemOwner() const { return ItemOwner; }

    UPROPERTY(BlueprintReadOnly, Category = ACF)
    UACFItem* ItemDefinition;

    virtual void InitItemActor(APawn* inOwner, UACFItem* inItemDefinition);
    virtual bool IsFullyInit() const;

protected:
    UFUNCTION(BlueprintNativeEvent, Category = ACF)
    void InitItemFromDefinition(UACFItem* inItemDefinition);
    // virtual void InitItemFromDefinition_Implementation(UACFItem* inItemDefinition) override;

    // Called when the game starts or when spawned
    virtual void BeginPlay() override;
    /**
     *  The Pawn that owns this item. Must always be valid after initialization.
     */
    UPROPERTY(ReplicatedUsing = OnRep_ItemOwner)
    APawn* ItemOwner = nullptr;

    UFUNCTION()
    virtual void OnRep_ItemOwner();

    void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const;
    /**
     *  Adds a gameplay modifier to the owning Pawn using GAS.
     * @param gameplayModifier The gameplay effect class to apply.
     * @param geLevel The level of the gameplay effect (default is 1).
     * @return The handle to the active gameplay effect.
     */
    FActiveGameplayEffectHandle AddGASModifierToOwner(const TSubclassOf<UGameplayEffect>& gameplayModifier, const float geLevel = 1.f);
    /**
     *  Removes a previously applied gameplay modifier from the owning Pawn.
     * @param modifierHandle The handle of the active gameplay effect to remove.
     */
    void RemoveGASModifierToOwner(const FActiveGameplayEffectHandle& modifierHandle);

    UAbilitySystemComponent* GetAbilityComponent() const;
};
