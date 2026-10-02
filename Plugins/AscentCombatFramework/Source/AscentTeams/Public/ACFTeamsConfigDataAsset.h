// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include <GenericTeamAgentInterface.h>
#include <GameplayTagContainer.h>

#include "ACFTeamsConfigDataAsset.generated.h"




USTRUCT(BlueprintType)
struct FTeamConfig {
    GENERATED_BODY()

public:

    UPROPERTY(EditAnywhere, BlueprintReadWrite, meta = (Categories = "Teams"), Category = ACF)
    FGameplayTag TeamTag;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = ACF)
    FText DisplayName;

    UPROPERTY(EditAnywhere, meta = (Categories = "Teams"), BlueprintReadOnly, Category = ACF)
    TMap<FGameplayTag, TEnumAsByte<ETeamAttitude::Type>> Relationship;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = ACF)
    TArray<TEnumAsByte<ECollisionChannel>> DamageCollisionsChannel;
};


UCLASS()
class ASCENTTEAMS_API UACFTeamsConfigDataAsset : public UPrimaryDataAsset {
    GENERATED_BODY()

public:
    UACFTeamsConfigDataAsset();
     
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = ACF)
    TMap<FGenericTeamId, FTeamConfig> TeamsConfig;

};
