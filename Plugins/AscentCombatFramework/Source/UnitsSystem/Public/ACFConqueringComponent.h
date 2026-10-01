// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "Components/ActorComponent.h"
#include "CoreMinimal.h"
#include "GameplayTagContainer.h"

#include "ACFConqueringComponent.generated.h"

DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FOnAssaultPointConquerStateChanged, const FGameplayTag&, assaultPoint, const EConqueredState&, newState);

UCLASS(ClassGroup = (ACF), meta = (BlueprintSpawnableComponent))
class UNITSSYSTEM_API UACFConqueringComponent : public UActorComponent {
    GENERATED_BODY()

public:
    // Sets default values for this component's properties
    UACFConqueringComponent();

protected:
    // Called when the game starts
    virtual void BeginPlay() override;

public:
    UFUNCTION( Server, Reliable, Category = ACF)
    void SetConqueringState(const FGameplayTag& point, const EConqueredState& newState);

    UFUNCTION(BlueprintPure, Category = ACF)
    EConqueredState GetConqueringStateForPoint(const FGameplayTag& point) const;

    UFUNCTION(BlueprintPure, Category = ACF)
    bool IsAnyConquerInProgress() const;

    UFUNCTION(BlueprintPure, Category = ACF)
    class AACFAssaultPoint* GetAssaultPoint(const FGameplayTag& poin) const;

    UPROPERTY(BlueprintAssignable, Category = ACF)
    FOnAssaultPointConquerStateChanged OnConquerStateChanged;

private:

    bool bConquerInProgress = false;
};
