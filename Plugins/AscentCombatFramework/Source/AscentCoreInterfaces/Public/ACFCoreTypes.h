// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "GenericTeamAgentInterface.h"
#include <Engine/DataTable.h>
#include <GameplayTagContainer.h>

#include "ACFCoreTypes.generated.h"

/**
 *
 */



USTRUCT(BlueprintType)
struct FACFStruct {

    GENERATED_BODY()

public:
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = ACF)
    FGameplayTag TagName;

    FORCEINLINE bool operator!=(const FGameplayTag& Other) const
    {
        return TagName != Other;
    }

    FORCEINLINE bool operator==(const FGameplayTag& Other) const
    {
        return TagName == Other;
    }

    FORCEINLINE bool operator!=(const FACFStruct& Other) const
    {
        return TagName != Other.TagName;
    }

    FORCEINLINE bool operator==(const FACFStruct& Other) const
    {
        return TagName == Other.TagName;
    }
};

UENUM(BlueprintType)
enum class EACFDirection : uint8 {
    Front = 0,
    Back = 1,
    Left = 2,
    Right = 3,
    FrontRight = 4,
    BackRight = 5,
    BackLeft = 6,
    FrontLeft = 7
};

UCLASS()
class ASCENTCOREINTERFACES_API UACFCoreTypes : public UObject {
    GENERATED_BODY()
};
