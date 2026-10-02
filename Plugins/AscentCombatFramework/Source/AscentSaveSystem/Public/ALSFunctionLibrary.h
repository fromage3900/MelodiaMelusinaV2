// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"

#include "ALSFunctionLibrary.generated.h"

struct FALSActorData;

/**
 *
 */
UCLASS()
class ASCENTSAVESYSTEM_API UALSFunctionLibrary : public UBlueprintFunctionLibrary {
    GENERATED_BODY()

public:
    /**
     * Attempts to save a screenshot with the given file name and dimensions.
     *
     * @param fileName The desired name of the screenshot file.
     * @param width The width of the screenshot in pixels. Default is 640.
     * @param height The height of the screenshot in pixels. Default is 480.
     * @return true if the screenshot was successfully saved, false otherwise.
     */
    UFUNCTION(BlueprintCallable, Category = ALS)
    static bool TrySaveScreenshot(const FString& fileName, const int32 width = 640, const int32 height = 480);

    /**
     * Retrieves a previously saved screenshot by its file name.
     *
     * @param fileName The name of the screenshot file to retrieve.
     * @return A pointer to the UTexture2D representation of the screenshot, or nullptr if not found.
     */
    UFUNCTION(BlueprintCallable, Category = ALS)
    static UTexture2D* GetScreenshotByName(const FString& fileName);

    /**
     * Determines if a given actor should be saved.
     *
     * @param actor The actor to check.
     * @return true if the actor should be saved, false otherwise.
     */
    UFUNCTION(BlueprintCallable, Category = ALS)
    static bool ShouldSaveActor(AActor* actor);

    /**
     * Resolves the "destroy if missing in save" policy for a given actor.
     *
     * Resolution order:
     *  1. If the actor has a UALSLoadAndSaveComponent, its bDestroyIfMissingInSave wins.
     *  2. Otherwise, fall back to UALSSaveGameSettings::bDestroyActorsMissingInSaveByDefault.
     *
     * @param Actor The actor being evaluated during the load phase.
     * @return true if the actor should be destroyed when missing from the loaded save.
     */
    UFUNCTION(BlueprintCallable, Category = ALS)
    static bool ShouldDestroyActorIfMissingInSave(const AActor* Actor);

    /**
     * Checks if the game is a new game (no loaded savegame).
     *
     * @param WorldContextObject The context object used to determine the game world.
     * @return true if it is a new game, false otherwise.
     */
    UFUNCTION(BlueprintCallable, meta = (WorldContext = "WorldContextObject"), Category = ALS)
    static bool IsNewGame(const UObject* WorldContextObject);

    /**
     * Converts a given time in seconds to a formatted time string (HH:MM).
     *
     * @param TotalSeconds The total number of seconds to convert.
     * @return A formatted time string in the format HH:MM.
     */
    UFUNCTION(BlueprintCallable, Category = ALS)
    static FString FromSecondsToTimeString(int32 TotalSeconds, bool bIncludeSeconds = true);

    static bool IsSpecialActor(const UObject* WorldContextObject, const AActor* actor);

    static void ExecuteFunctionsOnSavableComponents(const AActor* actorOwner, const FName& functionName);

    static void ExecuteFunctionsOnSavableActor(AActor* actorOwner, const FName& functionName);

    static void DeserializeActor(AActor* Actor, const FALSActorData& Record);

    static void FullDeserializeActor(AActor* Actor, const FALSActorData& Record, bool bLoadTransform);

    static void DeserializeActorComponents(AActor* Actor, const FALSActorData& ActorRecord);

    static FALSActorData SerializeActor(AActor* actor);

    static void SerializeComponents(const AActor* Actor, FALSActorData& ActorRecord);

	static bool GenerateScreenshot(const FString& FileName, int32 NewWidth = 640, int32 NewHeight = 480);
    static FString ConstructScreenshotPath(const FString& fileName);
};
