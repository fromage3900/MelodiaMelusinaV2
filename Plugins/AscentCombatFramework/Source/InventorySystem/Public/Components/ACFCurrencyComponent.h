// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "Components/ActorComponent.h"
#include "CoreMinimal.h"
#include <GameplayTagContainer.h>

#include "ACFCurrencyComponent.generated.h"

/**
 * Dynamic multicast delegate called when the currency value changes.
 * @param newValue The new currency value after the change
 * @param variation The difference between the previous and new value
 */
DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FOnCurrencyValueChanged, float, newValue, float, variation);

/**
 * A component that handles the currency system for an Actor.
 */
UCLASS(ClassGroup = (ACF), Blueprintable, meta = (BlueprintSpawnableComponent))
class INVENTORYSYSTEM_API UACFCurrencyComponent : public UActorComponent {
    GENERATED_BODY()

public:
    /** Sets default values for this component's properties */
    UACFCurrencyComponent();

    /**
     * Adds the specified amount to the current currency.
     * @param amount The amount of currency to add
     */
    UFUNCTION(Server, Reliable, BlueprintCallable, Category = ACF)
    void AddCurrency(float amount);

    /**
     * Subtracts the specified amount from the current currency.
     * @param amount The amount of currency to remove
     */
    UFUNCTION(Server, Reliable, BlueprintCallable, Category = ACF)
    void RemoveCurrency(float amount);

    /**
     * Overrides the current currency value.
     * @param amount The new currency value to set
     */
    UFUNCTION(Server, Reliable, BlueprintCallable, Category = ACF)
    void SetCurrency(float amount);

    /**
     * Transfers a specified amount from another currency component to this one.
     * @param amount The amount of currency to gather
     * @param sourceComp The source component from which currency is gathered
     */
    UFUNCTION(Server, Reliable, BlueprintCallable, Category = ACF)
    void GatherCurrency(float amount, UACFCurrencyComponent* sourceComp);

    /**
     * Checks if the component has at least the specified amount of currency.
     * @param amount The amount to check against the current currency
     * @return True if the current currency is greater than or equal to the specified amount
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    FORCEINLINE bool HasEnoughCurrency(float amount) const
    {
        return CurrencyAmount >= amount;
    }

    /**
     * Returns the current amount of currency held by this component.
     * @return The current currency value
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    FORCEINLINE float GetCurrentCurrencyAmount() const
    {
        return CurrencyAmount;
    }

    /**
     * Event triggered whenever the currency value changes.
     * Useful for updating UI or triggering gameplay reactions.
     */
    UPROPERTY(BlueprintAssignable, Category = ACF)
    FOnCurrencyValueChanged OnCurrencyChanged;

    /**
     * Consumes the pending death-drop currency held by this component (applying
     * CurrencyDropVariation). The amount is returned, removed from CurrencyAmount,
     * and the component is marked as dropped so it won't drop again. Returns 0 if
     * drop-on-death is disabled, if the wallet has already been dropped, or if the
     * computed amount is too small to drop. Used by UACFEquipmentComponent to fold
     * the wallet into a single collapsed world item on death.
     */
    UFUNCTION(BlueprintCallable, Category = "ACF|Drop")
    float ConsumePendingDeathCurrencyDrop();

    /** Whether this component has already produced its death drop. */
    UFUNCTION(BlueprintPure, Category = "ACF|Drop")
    FORCEINLINE bool HasDroppedDeathCurrency() const { return bCurrencyDropped; }

protected:
    // Called when the game starts
    virtual void BeginPlay() override;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, ReplicatedUsing = OnRep_Currency, Category = ACF)
    float CurrencyAmount = 0.f;

    /*If set to true, the currency held by this component is dropped as a world item
    when the owner dies (or folded into the single collapsed drop produced by a
    sibling UACFEquipmentComponent when its CollapseDropInASingleWorldItem flag is on).*/
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|Drop")
    bool bDropCurrencyOnOwnerDeath = true;

    /*The randomic variation on the CurrencyAmount dropped on this owner death*/
    UPROPERTY(meta = (EditCondition = "bDropCurrencyOnOwnerDeath"), EditAnywhere, BlueprintReadWrite, Category = "ACF|Drop")
    float CurrencyDropVariation = 5.f;

    virtual void HandleCurrencyChanged();

private:
    UFUNCTION()
    void HandleStatReachedZero();

    bool bCurrencyDropped = false;

    UFUNCTION()
    void OnRep_Currency();

    void DispatchCurrencyChanged(float amount);
};
