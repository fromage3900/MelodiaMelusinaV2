// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/CheatManager.h"
#include <GameplayTagContainer.h>

#include "ACFCheatManager.generated.h"

struct FBaseItem;
class AACFCharacter;


/**
 *
 */
UCLASS()
class ASCENTCHEATMANAGER_API UACFCheatManager : public UCheatManager {
    GENERATED_BODY()

public:
    /** Discovers all available locations in the game world. */
    UFUNCTION(exec, Category = ACF)
    void DiscoverAllLocations();

    /** Grants the specified amount of experience points to the player.
     * @param Exps - The amount of experience to add.
     */
    UFUNCTION(exec, Category = ACF)
    void AddExp(float Exps);

    /** Adds the specified number of coins to the player's inventory.
     * @param Coins - The amount of coins to add.
     */
    UFUNCTION(exec, Category = ACF)
    void AddCurrency(float Coins);

    /** Advances the currently tracked quest by one step. */
    UFUNCTION(exec, Category = ACF)
    void ProceedInTrackedQuest();

    /** Starts all the quests defined in this cheat manager */
    UFUNCTION(exec, Category = ACF)
    void StartQuests();

    /** Adds the set of Items defined in this Cheat Manager to the local player's inventory. */
    UFUNCTION(exec, Category = ACF)
    void AddItemsToInventory();


protected:

    /*Items to be added to the inventory when the AddItemToInventory cheat is triggered*/
    UPROPERTY(EditDefaultsOnly, Category = ACF)
    TArray<FBaseItem> ItemsToAdd;

    /*Quests to start when the StartQuests cheat is triggered*/
    UPROPERTY(EditDefaultsOnly, Category = ACF)
    TArray<FGameplayTag> QuestsToStart;
    
};
