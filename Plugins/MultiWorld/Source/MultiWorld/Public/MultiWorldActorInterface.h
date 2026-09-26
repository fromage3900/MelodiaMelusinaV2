// Copyright 2019-2020 UNAmedia. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"

#include "MultiWorldHandle.h"

#include "MultiWorldActorInterface.generated.h"

/**
 * See IMultiWorldActorInterface. This class is needed by the UE5 reflection system.
 */
UINTERFACE(BlueprintType)
class MULTIWORLD_API UMultiWorldActorInterface : public UInterface
{
    GENERATED_BODY()
};

/**
 * Actors can implement this interface to be notified 
 * when the local player has entered/exited the world where they live.
 */
class MULTIWORLD_API IMultiWorldActorInterface : public IInterface
{
    GENERATED_BODY()

public:

    /**
    Invoked when the local player has entered the world where this actor lives.
    */
    UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = "MultiWorld|Actor")
    void OnEnteringWorld();

    /**
    Invoked when the local player has exited the world where this actor lives.
    */
    UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = "MultiWorld|Actor")
    void OnExitingWorld();

    /**
    Invoked before this actor is transferred to a new world.
    */
    UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = "MultiWorld|Actor")
    void OnPreTransferredToWorld(UWorld* OldWorld, UWorld* NewWorld);

    /**
    Invoked after this actor is transferred to a new world.
    */
    UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = "MultiWorld|Actor")
    void OnPostTransferredToWorld(UWorld* OldWorld, UWorld* NewWorld);
};
