// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "ACFAITypes.h"
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"

#include "ACFAIWaveMaster.generated.h"

class UACFAIWavesMasterComponent;

UCLASS(BlueprintType, Blueprintable)
class AIFRAMEWORK_API AACFAIWaveMaster : public AActor {
    GENERATED_BODY()

public:
    // Sets default values for this actor's properties
    AACFAIWaveMaster();

protected:
    // Called when the game starts or when spawned
    virtual void BeginPlay() override;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = ACF)
    TObjectPtr<UACFAIWavesMasterComponent> wavesComp;

 
};
