// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

// Include necessary headers for loading and saving functionality.
#include "ALSFunctionLibrary.h"
#include "ALSLoadAndSaveComponent.h"
#include "ALSLoadTask.h"
#include "ALSSaveGameSettings.h"
#include "ALSSaveInfo.h"
#include "ALSSaveTask.h"
#include "CoreMinimal.h"
#include "Engine/GameInstance.h"
#include "Kismet/GameplayStatics.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include <Async/AsyncWork.h>
#include <Engine/World.h>

#include "ALSLoadAndSaveSubsystem.generated.h"

/**
 * Enumeration representing the current state of the loading/saving system.
 *
 * - EIdle: The system is idle and not performing any load or save operations.
 * - ESaving: The system is currently saving the game state.
 * - ELoading: The system is currently loading a saved game state.
 */
UENUM(BlueprintType)
enum class ELoadingState : uint8 {
    EIdle, // System is idle.
    ESaving, // System is in the process of saving.
    ELoading // System is in the process of loading.
};

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FALSOnLoadFinished, bool, bSuccess);

/**
 * The ALSLoadAndSaveSubsystem handles saving and loading of game world data.
 *
 * This subsystem is responsible for saving the entire game world to a save game,
 * loading game worlds from saved data, managing local player data during map travel,
 * and handling extra actors' serialization. It also provides utility functions for managing
 * save slots and metadata.
 */
UCLASS()
class ASCENTSAVESYSTEM_API UALSLoadAndSaveSubsystem : public UGameInstanceSubsystem {
    GENERATED_BODY()

public:
    /**
     * Initializes the subsystem instance.
     *
     * Called automatically during game instance initialization.
     *
     * @param Collection The subsystem collection that owns this subsystem.
     */
    virtual void Initialize(FSubsystemCollectionBase& Collection) override;

    /**
     * Deinitializes the subsystem instance.
     *
     * Called automatically during game instance shutdown.
     */
    virtual void Deinitialize() override;

    /**
     * Saves the entire game world into a save game slot.
     *
     * This function serializes the current game world state, including actors, local player data,
     * and optionally a screenshot, and writes the data to a save slot.
     *
     * @param slotName The name of the save slot.
     * @param saveCallback Callback function to be invoked when the save operation finishes.
     * @param bSaveLocalPlayer Whether to include the local player's data in the save.
     * @param bSaveScreenshot Whether to capture and save a screenshot of the current game state.
     * @param slotDescription Optional description of the save slot.
     */
    UFUNCTION(BlueprintCallable, Category = ALS)
    void SaveGameWorld(const FString& slotName, const FOnSaveFinished& saveCallback, const bool bSaveLocalPlayer = true,
        const bool bSaveScreenshot = true, const FString& slotDescription = "");

    /**
     * Saves the entire game world into the currently active save slot.
     *
     * This is similar to SaveGameWorld but uses the current active slot.
     *
     * @param saveCallback Callback function to be invoked when the save operation finishes.
     * @param bSaveLocalPlayer Whether to include the local player's data in the save.
     * @param bSaveScreenshot Whether to capture and save a screenshot of the current game state.
     * @param slotDescription Optional description of the save slot.
     */
    UFUNCTION(BlueprintCallable, Category = ALS)
    void SaveGameWorldInCurrentSlot(const FOnSaveFinished& saveCallback, const bool bSaveLocalPlayer = true,
        const bool bSaveScreenshot = true, const FString& slotDescription = "");

    /**
     * Loads a game world from the specified save slot and opens the saved map.
     *
     * @param slotName The name of the save slot to load.
     * @param loadCallback Callback function to be invoked when the load operation finishes.
     */
    UFUNCTION(BlueprintCallable, Category = ALS)
    void LoadGameWorld(const FString& slotName, const FOnLoadFinished& loadCallback, bool reloadPlayer = true);

    /**
     * Reloads the current level using the specified save slot.
     *
     * @param slotName The name of the save slot.
     * @param loadCallback Callback function to be invoked when the load operation finishes.
     * @param bReloadLocalPlayer Whether to reload the local player's data.
     */
    UFUNCTION(BlueprintCallable, Category = ALS)
    void LoadCurrentLevel(const FString& slotName, const FOnLoadFinished& loadCallback, bool bReloadLocalPlayer = true);

    /**
     * Loads a specified level from the provided save slot.
     *
     * @param slotName The name of the save slot.
     * @param levelName The name of the level to load.
     * @param loadCallback Callback function to be invoked when the load operation finishes.
     * @param bReloadLocalPlayer Whether to reload the local player's data.
     */
    UFUNCTION(BlueprintCallable, Category = ALS)
    void LoadLevelFromSaveGame(const FString& slotName, const FString& levelName, const FOnLoadFinished& loadCallback, bool bReloadLocalPlayer);

    /**
     * Saves the current Player Controller and Pawn in a temporary slot.
     *
     * Useful during map travel to preserve the player's state.
     *
     * @return True if the operation succeeded, false otherwise.
     */
    UFUNCTION(BlueprintCallable, Category = ALS)
    bool TravelLocalPlayer();

    /**
     * Loads the player data from the temporary travel slot.
     *
     * Must be called after TravelLocalPlayer has been executed.
     *
     * @return True if the operation succeeded, false otherwise.
     */
    UFUNCTION(BlueprintCallable, Category = ALS)
    bool LoadTraveledPlayer();

    /**
     * Deletes the specified save slot.
     *
     * @param tempSlot The name of the slot to delete.
     */
    void DeleteSlot(const FString tempSlot);

    /**
     * Saves the local player's state to the specified slot.
     *
     * @param slotName The name of the slot.
     * @return True if the operation succeeded, false otherwise.
     */
    UFUNCTION(BlueprintCallable, Category = ALS)
    bool SaveLocalPlayer(const FString& slotName);

    /**
     * Saves the specified actor.
     *
     * @param actorToSave The actor to serialize and save.
     * @return True if the operation succeeded, false otherwise.
     */
    UFUNCTION(BlueprintCallable, Category = ALS)
    bool SaveActor(AActor* actorToSave);

    /**
     * Loads the specified actor.
     *
     * @param actorToLoad The actor that will be loaded.
     * @return True if the operation succeeded, false otherwise.
     */
    UFUNCTION(BlueprintCallable, Category = ALS)
    bool LoadActor(AActor* actorToLoad);

    /**
     * Loads the local player's state from the specified slot.
     *
     * @param slotName The name of the slot.
     * @param bReloadTransform Whether to reload the player's transform.
     * @return True if the operation succeeded, false otherwise.
     */
    UFUNCTION(BlueprintCallable, Category = ALS)
    bool LoadLocalPlayer(const FString& slotName, bool bReloadTransform);

    /**
     * Saves a player (Player Controller & Pawn) to the specified slot.
     *
     * Useful for multiplayer games.
     *
     * @param slotName The name of the slot.
     * @param playerID The identifier for the player.
     * @param playerToSave The Player Controller to save.
     * @return True if the operation succeeded, false otherwise.
     */
    UFUNCTION(BlueprintCallable, Category = ALS)
    bool SavePlayer(const FString& slotName, const FString& playerID, APlayerController* playerToSave);

    /**
     * Creates or updates the save slot information.
     *
     * @param slotName The name of the slot.
     * @return True if the operation succeeded, false otherwise.
     */
    bool CreateOrUpdateSlotInfo(const FString& slotName);

    /**
     * Removes the save slot information.
     *
     * @param slotName The name of the slot to remove.
     * @return True if the operation succeeded, false otherwise.
     */
    UFUNCTION(BlueprintCallable, Category = ALS)
    bool RemoveSlotInfo(const FString& slotName);

    /**
     * Loads a player (Player Controller & Pawn) from the specified slot.
     *
     * Useful for multiplayer games.
     *
     * @param slotName The name of the slot.
     * @param playerID The identifier for the player.
     * @param playerToLoad The Player Controller to load.
     * @param bReloadTransform Whether to reload the player's transform.
     * @return True if the operation succeeded, false otherwise.
     */
    UFUNCTION(BlueprintCallable, Category = ALS)
    bool LoadPlayer(const FString& slotName, const FString& playerID, APlayerController* playerToLoad, bool bReloadTransform);

    /**
     * Sets the current load type.
     *
     * @param inLoadType The load type to set.
     */
    UFUNCTION(BlueprintCallable, Category = ALS)
    void SetLoadType(ELoadType inLoadType)
    {
        loadType = inLoadType;
    }

    /**
     * Checks if the current load type indicates a new game.
     *
     * @return True if this is a new game, false otherwise.
     */
    UFUNCTION(BlueprintPure, Category = ALS)
    bool IsNewGame() const
    {
        return bIsNewGame;
    }

    UFUNCTION(BlueprintCallable, Category = ALS)
    void SetNewGame(bool newGame)
    {
        bIsNewGame = newGame;
        StartPlaytimeTracking();
    }

    /**
     * Retrieves the current load type.
     *
     * @return The current ELoadType value.
     */
    UFUNCTION(BlueprintPure, Category = ALS)
    ELoadType GetLoadType() const
    {
        return loadType;
    }

    UFUNCTION(BlueprintPure, Category = ALS)
    /**
     * Retrieves the start play time.
     *
     * @return The start play time as a FDateTime.
     */
    FDateTime GetStartPlayTime() const
    {
        return StartPlayTime;
    }

    UFUNCTION(BlueprintCallable, Category = ALS)
    class UALSSaveGame* GetOrCreateCurrentSaveGame();

    /**
     * Attempts to retrieve save metadata for the specified slot.
     *
     * @param slotName The name of the slot.
     * @param outSaveMetadata Output parameter to store the save metadata.
     * @return True if metadata was successfully retrieved, false otherwise.
     */
    UFUNCTION(BlueprintCallable, Category = ALS)
    bool TryGetSaveMetadata(const FString& slotName, FALSSaveMetadata& outSaveMetadata) const;

    /**
     * Initializes playtime tracking at the start of a session
     */
    UFUNCTION(BlueprintCallable, Category = ALS)
    void StartPlaytimeTracking()
    {
        StartPlayTime = FDateTime::Now();
    }

    /**
     * Loads an existing save game from the specified slot or creates a new one if it doesn't exist.
     *
     * @param slotName The name of the slot.
     * @return Pointer to the UALSSaveGame object.
     */
    UFUNCTION(BlueprintCallable, Category = ALS)
    class UALSSaveGame* LoadOrCreateSaveGame(const FString& slotName);

    /**
     * Loads existing save information or creates new save info if none exists.
     *
     * @return Pointer to the UALSSaveInfo object.
     */
    UFUNCTION(BlueprintCallable, Category = ALS)
    class UALSSaveInfo* LoadOrCreateSaveInfo();

    /**
     * Retrieves metadata for all save games.
     *
     * @return An array of FALSSaveMetadata containing information about each save.
     */
    UFUNCTION(BlueprintPure, Category = ALS)
    TArray<FALSSaveMetadata> GetAllSaveGames() const;

    /**
     * Checks whether there is at least one save game available.
     *
     * @return True if there is any save game, false otherwise.
     */
    UFUNCTION(BlueprintPure, Category = ALS)
    bool HasAnySaveGame() const;

    /**
     * Gets the number of the current active save slot.
     *
     * @return The current slot number.
     */
    UFUNCTION(BlueprintPure, Category = ALS)
    int32 GetCurrentSlotNum() const;

    /**
     * Gets the maximum number of save slots allowed.
     *
     * @return The maximum number of save slots.
     */
    UFUNCTION(BlueprintPure, Category = ALS)
    int32 GetMaxSlotsNum() const;

    /**
     * Checks if a new save slot can be added.
     *
     * @return True if a new slot can be added, false otherwise.
     */
    UFUNCTION(BlueprintPure, Category = ALS)
    bool CanAddNewSlot() const;

    /**
     * Checks whether the provided slot name is unique.
     *
     * @param slotName The slot name to check.
     * @return True if the slot name is unique, false otherwise.
     */
    UFUNCTION(BlueprintCallable, Category = ALS)
    bool IsSlotNameUnique(const FString& slotName) const;

    /**
     * Retrieves the screenshot associated with a given save.
     *
     * @param saveName The name of the save slot.
     * @return Pointer to the UTexture2D object representing the screenshot.
     */
    UFUNCTION(BlueprintCallable, Category = ALS)
    UTexture2D* GetScreenshotForSave(const FString& saveName) const;

    /**
     * Retrieves the current system loading state.
     *
     * @return The current ELoadingState.
     */
    UFUNCTION(BlueprintPure, Category = ALS)
    ELoadingState GetSystemState() const
    {
        return systemState;
    }

    /**
     * Retrieves the name of the current save slot.
     *
     * @return The current save slot name.
     */
    UFUNCTION(BlueprintPure, Category = ALS)
    FString GetCurrentSaveName() const
    {
        return currentSaveSlot;
    }

    /**
     * Retrieves the default save name.
     *
     * @return The default save name as a FString.
     */
    UFUNCTION(BlueprintPure, Category = ALS)
    FString GetDefaultSaveName() const;

    /**
     * Gets the current save game object.
     *
     * @return Pointer to the current UALSSaveGame.
     */
    UFUNCTION(BlueprintPure, Category = ALS)
    class UALSSaveGame* GetCurrentSaveGame() const
    {
        return currentSavegame;
    }

    UPROPERTY(BlueprintAssignable, Category = ALS)
    FALSOnLoadFinished OnLoadFinished;

    /**
     * Finalizes the save operation.
     *
     * Should be called once all asynchronous save tasks have been completed.
     *
     * @param bSuccess Indicates whether the save operation was successful.
     */
    void FinishSaveWork(const bool bSuccess);

    /**
     * Finalizes the load operation.
     *
     * Should be called once all asynchronous load tasks have been completed.
     *
     * @param bSuccess Indicates whether the load operation was successful.
     */
    void FinishLoadWork(const bool bSuccess);

private:
    // The current load type determining how data is reloaded.
    ELoadType loadType = ELoadType::EDontReload;

    // Flag indicating whether a load operation is currently in progress.
    bool bIsLoading;

    // Flag indicating whether this is a new or a loaded game
    bool bIsNewGame = true;
    /**
     * Handler called when the world loading has finished.
     *
     * @param world The world context.
     */
    UFUNCTION()
    void HandleLoadingFinished(UWorld* world);

    /**
     * Handler called when the load operation has completed.
     *
     * @param SaveSlot The name of the save slot.
     * @param UserIndex The user index associated with the save.
     * @param LoadedSaveData The loaded save game data.
     */
    UFUNCTION()
    void HandleLoadCompleted(const FString& SaveSlot, const int32 UserIndex, USaveGame* LoadedSaveData);

    /**
     * Performs an asynchronous load of the save game.
     *
     * @param savegameName The name of the save game to load.
     */
    void AsyncLoadSaveGame(const FString& savegameName);

    /**
     * Serializes the provided object into FALSObjectData.
     *
     * @param objectToSerialize The object to serialize.
     * @param outData Output parameter to store the serialized data.
     */
    void SerializeObject(UObject* objectToSerialize, FALSObjectData& outData);

    /**
     * Deserializes the provided data into the given settings object.
     *
     * @param settingsObject The object to populate with deserialized data.
     * @param objectData The data to deserialize.
     */
    void DeserializeObject(UObject* settingsObject, const FALSObjectData& objectData);

    // Internal callback for load finished event.
    FOnLoadFinished onLoadedCallbackInternal;

    // Internal callback for save finished event.
    FOnSaveFinished onSaveFinishedInternal;

    // The current state of the system (idle, saving, or loading).
    UPROPERTY()
    ELoadingState systemState;

    // The name of the currently active save slot.
    FString currentSaveSlot;

    // If the current save should reload player
    bool bReloadPlayer;

    bool bSaveScreen;

    // The current save game object.
    UPROPERTY()
    TObjectPtr<class UALSSaveGame> currentSavegame;

    UPROPERTY()
    FDateTime StartPlayTime = FDateTime(0.f);

    UPROPERTY()
    FALSPlayerData TravelingPlayer;

    bool CreatePlayerData(FALSPlayerData& outData);
    bool RestorePlayerData(const FALSPlayerData& inData, bool bReloadTransform);
};

/**
 * Static helper function to finalize the save operation.
 *
 * This function retrieves the UALSLoadAndSaveSubsystem instance from the Game Instance
 * and calls FinishSaveWork with the provided success flag.
 *
 * @param WorldContextObject Context object to get the world.
 * @param bSuccess Indicates whether the save operation was successful.
 */
static void GFinishSave(UWorld* WorldContextObject, bool bSuccess)
{
    UGameplayStatics::GetGameInstance(WorldContextObject)
        ->GetSubsystem<UALSLoadAndSaveSubsystem>()
        ->FinishSaveWork(bSuccess);
}

/**
 * Static helper function to finalize the load operation.
 *
 * This function performs several operations:
 *   - Destroys actors that need to be removed.
 *   - Spawns new actors based on the provided spawn data.
 *   - Updates transforms for saved actors.
 *   - Dispatches loaded events on loadable components.
 *
 * After processing, it calls FinishLoadWork on the subsystem.
 *
 * @param WorldContextObject Context object to get the world.
 * @param ToBeSpawned Array of actor data representing actors to be spawned.
 * @param SavedActors Map of existing actors and their loaded data.
 * @param ToBeDestroyed Array of actors to be destroyed.
 * @param wpActors Array of load and save components that need to be notified after loading.
 * @param bSuccess Indicates whether the load operation was successful.
 */
static void GFinishLoad(UWorld* WorldContextObject,
    TArray<FALSActorData> ToBeSpawned,
    TMap<AActor*, FALSActorLoaded> SavedActors,
    TArray<AActor*> ToBeDestroyed,
    TArray<UALSLoadAndSaveComponent*> wpActors,
    bool bSuccess)
{
    // Retrieve save settings from the default mutable settings.
    const UALSSaveGameSettings* saveSettings = GetMutableDefault<UALSSaveGameSettings>();

    // If the load was successful and save settings are available, process the loaded data.
    if (bSuccess && saveSettings) {
        // Destroy actors that are marked for removal.
        for (const auto& actor : ToBeDestroyed) {
            actor->Destroy();
        }

        // Spawn new actors based on the saved actor data.
    
        for (const auto& Record : ToBeSpawned) {
            FActorSpawnParameters SpawnInfo {};
            SpawnInfo.Name = Record.alsName;
            // The spawn transform already applies the full saved placement, scale included.
            AActor* spawnedActor = WorldContextObject->SpawnActor(Record.Class, &Record.Transform, SpawnInfo);
            if (spawnedActor) {
                // Deserialize data, re-apply location/rotation and fire the
                // OnLoaded/OnComponentLoaded hooks in one place.
                UALSFunctionLibrary::FullDeserializeActor(spawnedActor, Record, /*bLoadTransform=*/true);
            }
        }

        // Update transforms and dispatch load events for existing saved actors (their
        // data blob was already deserialized by the load task). Only location/rotation
        // are restored: these actors already exist in the level, so their scale is
        // authored data and re-applying it deforms scaled actors.
        for (const auto& actorRec : SavedActors) {
            if (!actorRec.Key) {
                continue;
            }
            actorRec.Key->SetActorLocationAndRotation(actorRec.Value.transform.GetLocation(), actorRec.Value.transform.GetRotation(), false, nullptr, ETeleportType::TeleportPhysics);

            UALSFunctionLibrary::ExecuteFunctionsOnSavableActor(actorRec.Key,
                saveSettings->GetOnComponentLoadedFunctionName());
        }

        // Dispatch the loaded event on all loadable components.
        for (const auto& comp : wpActors) {
            comp->DispatchLoaded();
        }
    }

    // Finalize the load operation in the subsystem.
    UGameplayStatics::GetGameInstance(WorldContextObject)
        ->GetSubsystem<UALSLoadAndSaveSubsystem>()
        ->FinishLoadWork(bSuccess);
}
