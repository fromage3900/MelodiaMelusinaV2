// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "UObject/Interface.h"

#include "ALSSavableInterface.generated.h"


// This class does not need to be modified.
UINTERFACE(BlueprintType, Blueprintable)
class UALSSavableInterface : public UInterface {
    GENERATED_BODY()
};

/**
 *
 */
class ASCENTSAVESYSTEM_API IALSSavableInterface {
    GENERATED_BODY()

public:
    UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = ALS)
    void OnSaved();
    virtual void OnSaved_Implementation() {};

    UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = ALS)
    void OnLoaded();
    virtual void OnLoaded_Implementation() {};

    UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = ALS)
    bool ShouldBeIgnored();
    virtual bool ShouldBeIgnored_Implementation()
    {
        return false;
    }

    UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = ALS)
    TArray<UActorComponent*> GetComponentsToSave() const;
    virtual TArray<UActorComponent*> GetComponentsToSave_Implementation() const
    {
        return TArray<UActorComponent*>();
    }
};
