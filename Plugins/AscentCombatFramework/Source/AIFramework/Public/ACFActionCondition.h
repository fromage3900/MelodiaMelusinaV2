// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "GameplayTagContainer.h"

#include "ACFActionCondition.generated.h"


 class APawn;


/**
 *  Defining custom conditions for AI Behaviours
 */

UENUM(BlueprintType)
enum class EConditionType : uint8 {
    EBelow UMETA(DisplayName = "Is Below"),
    EEqual UMETA(DisplayName = "Is Nearly Equal"),
    EAbove UMETA(DisplayName = "Is Above"),
};

UCLASS(Blueprintable, BlueprintType, abstract, EditInlineNew, HideCategories = ("DoNotShow"), CollapseCategories, AutoExpandCategories = ("ACF"))
class AIFRAMEWORK_API UACFActionCondition : public UObject {
    GENERATED_BODY()
public:
    UFUNCTION(BlueprintNativeEvent, Category = ACF)
    bool IsConditionMet(const APawn* character);
    virtual bool IsConditionMet_Implementation(const APawn* character) { return true; }
};

UCLASS(NotBlueprintable, BlueprintType, EditInlineNew, HideCategories = ("DoNotShow"), CollapseCategories, AutoExpandCategories = ("ACF"))
class AIFRAMEWORK_API UACFORActionCondition : public UACFActionCondition {
    GENERATED_BODY()

protected:
    UACFORActionCondition() { }

    UPROPERTY(Instanced, EditDefaultsOnly, Category = "Conditions")
    TArray<UACFActionCondition*> OrConditions;

    virtual bool IsConditionMet_Implementation(const APawn* character) override
    {
        for (auto& cond : OrConditions) {
            if (cond->IsConditionMet(character))
                return true;
        }
        return false;
    }
};

UCLASS(NotBlueprintable, BlueprintType, EditInlineNew, HideCategories = ("DoNotShow"), CollapseCategories, AutoExpandCategories = ("ACF"))
class AIFRAMEWORK_API UACFANDActionCondition : public UACFActionCondition {
    GENERATED_BODY()

public:
    UACFANDActionCondition() { }

    UPROPERTY(Instanced, EditDefaultsOnly, Category = "Conditions")
    TArray<UACFActionCondition*> AndConditions;

    virtual bool IsConditionMet_Implementation(const APawn* character) override
    {
        for (auto& cond : AndConditions) {
            if (!cond->IsConditionMet(character))
                return false;
        }
        return true;
    }
};

UCLASS(NotBlueprintable, BlueprintType, EditInlineNew, HideCategories = ("DoNotShow"), CollapseCategories, AutoExpandCategories = ("ACF"))
class AIFRAMEWORK_API UACFDistanceActionCondition : public UACFActionCondition {
    GENERATED_BODY()

public:
    UACFDistanceActionCondition() { }

protected:
    UPROPERTY(EditDefaultsOnly, Category = "Conditions")
    EConditionType ConditionType;

    UPROPERTY(EditDefaultsOnly, Category = "Conditions")
    float Distance;

    UPROPERTY(EditDefaultsOnly, meta = (EditCondition = "ConditionType == EConditionType::EEqual"), Category = "Conditions")
    float NearlyEqualAcceptance = 25.f;

public:
    virtual bool IsConditionMet_Implementation(const APawn* character) override;

    void SetContidionConfig(const EConditionType condType, const float inDistance, const float acceptance = 25.f)
    {
        ConditionType = condType;
        Distance = inDistance;
        NearlyEqualAcceptance = acceptance;
    }

    float GetDistance() const
    {
        return Distance;
    }
};

UCLASS(NotBlueprintable, BlueprintType, EditInlineNew, HideCategories = ("DoNotShow"), CollapseCategories, AutoExpandCategories = ("ACF"))
class AIFRAMEWORK_API UACFStatisticActionCondition : public UACFActionCondition {
    GENERATED_BODY()

public:
    UACFStatisticActionCondition() { StatisticValuePercentage = 50.f; }

    UPROPERTY(EditDefaultsOnly, Category = "Conditions")
    EConditionType ConditionType;

    UPROPERTY(EditDefaultsOnly, Category = "Conditions")
    FGameplayTag StatisticTag;

    UPROPERTY(EditDefaultsOnly, meta = (ClampMin = "0.0", ClampMax = "100.0", UIMin = "0.0", UIMax = "100.0"), Category = "Conditions")
    float StatisticValuePercentage;

    UPROPERTY(EditDefaultsOnly, meta = (EditCondition = "ConditionType == EConditionType::EEqual"), Category = "Conditions")
    float NearlyEqualAcceptance = 5.f;

    virtual bool IsConditionMet_Implementation(const APawn* character) override;
};
