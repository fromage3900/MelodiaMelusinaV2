// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "UObject/NoExportTypes.h"
#include <Abilities/GameplayAbility.h>
#include <AttributeSet.h>
#include <GameplayEffect.h>

#include "ACFRPGTypes.generated.h"

/**
 *
 */
USTRUCT(BlueprintType)
struct FGEModifier {
    GENERATED_BODY()

public:
    FGEModifier() { };

    FGEModifier(const FGameplayAttribute& inAtt, const float inValue)
    {
        Attribute = inAtt;
        Value = inValue;
    };

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = ACF)
    FGameplayAttribute Attribute;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = ACF)
    float Value = 0.f;

    FORCEINLINE bool operator==(const FGameplayAttribute& Other) const
    {
        return this->Attribute == Other;
    }

    FORCEINLINE bool operator!=(const FGameplayAttribute& Other) const
    {
        return this->Attribute != Other;
    }

    FORCEINLINE bool operator!=(const FGEModifier& Other) const
    {
        return this->Attribute != Other.Attribute;
    }

    FORCEINLINE bool operator==(const FGEModifier& Other) const
    {
        return this->Attribute == Other.Attribute;
    }
};

USTRUCT(BlueprintType)
struct FGameplayEffectConfig {
    GENERATED_BODY()

public:
    FGameplayEffectConfig()
    {
        Level = 1.f;
    };

    FGameplayEffectConfig(const TSubclassOf<UGameplayEffect>& inGE, const float inLevel)
    {
        Effect = inGE;
        Level = inLevel;
    };

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = ACF)
    TSubclassOf<UGameplayEffect> Effect;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = ACF)
    float Level;
};

USTRUCT(BlueprintType)
struct FAbilityConfig {
    GENERATED_BODY()

public:
    FAbilityConfig()
    {
        GameplayAbility = nullptr;
        AbilityLevel = 1;
        TriggeringTag = FGameplayTag();
    };

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = ACF)
    FGameplayTag TriggeringTag;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = ACF)
    TSubclassOf<UGameplayAbility> GameplayAbility;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = ACF)
    int32 AbilityLevel;

    FORCEINLINE bool operator!=(const FGameplayTag& Other) const
    {
        return TriggeringTag != Other;
    }

    FORCEINLINE bool operator==(const FGameplayTag& Other) const
    {
        return TriggeringTag == Other;
    }

    FORCEINLINE bool operator!=(const FAbilityConfig& Other) const
    {
        return TriggeringTag != Other.TriggeringTag;
    }

    FORCEINLINE bool operator==(const FAbilityConfig& Other) const
    {
        return TriggeringTag == Other.TriggeringTag;
    }
};

USTRUCT(BlueprintType)
struct FAbilityHandlers {
    GENERATED_BODY()

public:
    FAbilityHandlers() {

    };

    FAbilityHandlers(const FGameplayAbilitySpecHandle& inGaHandle, const FActiveGameplayEffectHandle& inGeHandle)
    {
        GAHandle = inGaHandle;
        GEHandle = inGeHandle;
    };

    UPROPERTY(BlueprintReadOnly, Category = ACF)
    FGameplayAbilitySpecHandle GAHandle;

    UPROPERTY(BlueprintReadOnly, Category = ACF)
    FActiveGameplayEffectHandle GEHandle;
};

UCLASS()
class ASCENTGASRUNTIME_API UACFRPGTypes : public UObject {
    GENERATED_BODY()
};
