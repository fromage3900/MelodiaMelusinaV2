// // Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "Components/ActorComponent.h"
#include "CoreMinimal.h"

#include "ALSLoadAndSaveComponent.generated.h"


// Forward declaration of UALSLoadAndSaveSubsystem to avoid unnecessary includes
class UALSLoadAndSaveSubsystem;

// Delegate for notifying when an actor is saved
DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnActorSaved);
// Delegate for notifying when an actor is loaded
DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnActorLoaded);

/**
 * A component for handling saving and loading of actors.
 *
 * This component provides functionality to save and load an actor's state
 * using the Ascent Combat Framework's save system.
 */
UCLASS(ClassGroup = (ACF), meta = (BlueprintSpawnableComponent))
class ASCENTSAVESYSTEM_API UALSLoadAndSaveComponent : public UActorComponent {
    GENERATED_BODY()

public:
    /**
     * Default constructor that sets up default values.
     */
    UALSLoadAndSaveComponent();

    /**
     * Saves the current state of the owning actor.
     * This function can be called from Blueprints.
     */
    UFUNCTION(BlueprintCallable, Category = ALS)
    void SaveActor();

    /**
     * Loads the previously saved state of the owning actor.
     * This function can be called from Blueprints.
     */
    UFUNCTION(BlueprintCallable, Category = ALS)
    void LoadActor();

    /**
     * Event triggered when the actor is successfully saved.
     */
    UPROPERTY(BlueprintAssignable, Category = ALS)
    FOnActorSaved OnActorSaved;

    /**
     * Event triggered when the actor is successfully loaded.
     */
    UPROPERTY(BlueprintAssignable, Category = ALS)
    FOnActorLoaded OnActorLoaded;

    /**
     * Handles logic for dispatching the OnActorLoaded event.
     * This function is responsible for notifying when an actor has been loaded.
     */
    void DispatchLoaded();

protected:
    /**
     * Called when the game starts or when the component is spawned.
     */
    virtual void BeginPlay() override;
    virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

    /**
     * Determines whether the actor should be automatically reloaded on start.
     * If set to true, the actor will attempt to load its previous state when the game starts.
     */
    UPROPERTY(EditAnywhere, Category = ALS)
    bool bAutoReload = true;

    /**
     * Per-actor policy for the load phase: when this actor exists in the level but the
     * loaded save game does NOT contain a record for it, decides whether to destroy it.
     *
     * Default is false (forward-compatible): actors added to a level after release are
     * preserved when older saves are loaded. Set to true to opt back into the legacy
     * behavior, where any savable actor missing from the save is considered "destroyed
     * at runtime" and removed on load.
     *
     * Actors that do not have this component fall back to
     * UALSSaveGameSettings::bDestroyActorsMissingInSaveByDefault.
     */
    UPROPERTY(EditAnywhere, Category = ALS)
    bool bDestroyIfMissingInSave = false;

public:
    /**
     * Returns the per-actor "destroy if missing in save" policy.
     */
    UFUNCTION(BlueprintCallable, Category = ALS)
    bool GetDestroyIfMissingInSave() const { return bDestroyIfMissingInSave; }

    /**
     * Sets the per-actor "destroy if missing in save" policy at runtime.
     */
    UFUNCTION(BlueprintCallable, Category = ALS)
    void SetDestroyIfMissingInSave(bool bNewValue) { bDestroyIfMissingInSave = bNewValue; }

private:
    UFUNCTION()
    void HandleSaveSystemLoadFinished(bool bSuccess);

    void TryAutoLoadActor();

    /**
     * Retrieves the save system subsystem.
     * This function provides access to the UALSLoadAndSaveSubsystem for saving and loading operations.
     *
     * @return A pointer to the save subsystem if available, otherwise nullptr.
     */
    UALSLoadAndSaveSubsystem* GetSaveSubsystem() const;
};
