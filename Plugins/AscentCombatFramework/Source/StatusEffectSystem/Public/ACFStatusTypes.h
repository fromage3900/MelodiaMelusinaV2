// // Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "UObject/NoExportTypes.h"
#include <GameplayTagContainer.h>
#include <Engine/Texture2D.h>

#include "ACFStatusTypes.generated.h"

class UACFBaseStatusEffect;

/**
 *
 */
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnStatusEffectChanged, FGameplayTag, StatusTag);

DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnAnyStatusChanged);

USTRUCT(BlueprintType)
struct FStatusEffect {
    GENERATED_BODY()

public:
    FStatusEffect()
    {
        effectInstance = nullptr;
        StatusTag = FGameplayTag();
        StatusIcon = nullptr;
    }

    FStatusEffect(const FGameplayTag& status)
    {
        effectInstance = nullptr;
        StatusTag = status;
        StatusIcon = nullptr;
    }

    FStatusEffect(UACFBaseStatusEffect* inEffect);

    UPROPERTY(BlueprintReadOnly, Category = ACF)
    UACFBaseStatusEffect* effectInstance;

    UPROPERTY(BlueprintReadOnly, Category = ACF)
    FGameplayTag StatusTag;

    UPROPERTY(BlueprintReadOnly, Category = ACF)
    UTexture2D* StatusIcon;

    FORCEINLINE bool operator==(const FStatusEffect& Other) const { return this->StatusTag == Other.StatusTag; }
    FORCEINLINE bool operator!=(const FStatusEffect& Other) const { return this->StatusTag != Other.StatusTag; }

    FORCEINLINE bool operator==(const FGameplayTag& OtherTag) const { return this->StatusTag == OtherTag; }
    FORCEINLINE bool operator!=(const FGameplayTag& OtherTag) const { return this->StatusTag != OtherTag; }
};

UCLASS()
class STATUSEFFECTSYSTEM_API UACFStatusTypes : public UObject {
    GENERATED_BODY()
};
