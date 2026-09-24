// Copyright 2019-2020 UNAmedia. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Engine/World.h"

#include "MultiWorldHandle.generated.h"

/**
 * Wrap an UWorld. The main purpose for this is to distinct Worlds
 * handled by the plugin from the main world handled by the Engine.
 * Handles are created only by the FMultiWorldManager subsystem
 * and are used as argument of its API. 
 */
USTRUCT(BlueprintType)
struct MULTIWORLD_API FMultiWorldHandle
{
    GENERATED_BODY()

    FMultiWorldHandle() = default;

    /** the equality operator */
    bool operator==(const FMultiWorldHandle& Other) const
    {
        return World == Other.World;
    }

    /** the inequality operator */
    bool operator!=(const FMultiWorldHandle& Other) const
    {
        return !operator==(Other);
    }

    /**
     * Return the WorldContextObject for this world.
     * Note that the pointer can be nullptr 
       if the handle is invalid or the world already disposed.
     */
    UObject* GetWorldContextObject() const { return World; }

    /**
     * Return the pointer to the world.
     * Note that the pointer can be nullptr 
       if the handle is invalid or the world already disposed.
     */
    UWorld* GetWorld() const { return World; }

private:

    UPROPERTY(Transient)
    UWorld* World = nullptr;

    FMultiWorldHandle(UWorld* InWorld) : World(InWorld) { }

    bool IsValid() const { return World != nullptr; }
    bool IsActivated() const { return World && World->bIsWorldInitialized; }

    friend class UMultiWorldManager;
};
