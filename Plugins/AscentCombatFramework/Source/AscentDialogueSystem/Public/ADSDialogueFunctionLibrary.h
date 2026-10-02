// // Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include <GameplayTagContainer.h>

#include "ADSDialogueFunctionLibrary.generated.h"

/**
 * Blueprint function library for global dialogue-related utility functions.
 * Provides helper methods to access the Dialogue Master, replace variables in dialogue text,
 * and extract information from tags or actor references.
 */
UCLASS()
class ASCENTDIALOGUESYSTEM_API UADSDialogueFunctionLibrary : public UBlueprintFunctionLibrary {
    GENERATED_BODY()

public:
    /**
     * Retrieves the local Dialogue Master component for the current world context.
     *
     * @param WorldContextObject The world context used to resolve the current world.
     * @return The Dialogue Master component if found, nullptr otherwise.
     */
    UFUNCTION(BlueprintPure, meta = (WorldContext = "WorldContextObject"), Category = ADS)
    static class UADSDialogueMasterComponent* GetLocalDialogueMaster(const UObject* WorldContextObject);

    /**
     * Replaces dialogue variables inside a text with their current values from the Dialogue Master.
     *
     * @param WorldContextObject The world context used to resolve the Dialogue Master.
     * @param inString The input textto be edited
     * @return The text with variables replaced by their current values in the dialgoue master.
     */
    UFUNCTION(BlueprintPure, meta = (WorldContext = "WorldContextObject"), Category = ADS)
    static FText ReplaceDialogueVariablesInText(const UObject* WorldContextObject, const FText& inString);

    /**
     * Extracts the last part of a GameplayTag's string representation.
     *
     * Example: "Dialogue.NPC.Carl" -> "Carl".
     *
     * @param inTag The GameplayTag to process.
     * @return The last substring of the tag.
     */
    UFUNCTION(BlueprintPure, Category = ADS)
    static FString ExtractLastStringFromGameplayTag(const FGameplayTag& inTag);

    /**
     * Extracts the actor name from a soft object reference.
     *
     * @param actorSoftRef The soft reference to an actor.
     * @return The name of the actor referenced by the soft pointer.
     */
    UFUNCTION(BlueprintPure, Category = ADS)
    static FString ExtractActorNameFromSoftRef(const TSoftObjectPtr<AActor>& actorSoftRef);

    /**
     * Returns the list of available voice IDs for use in the dialogue system.
     *
     * @return An array of strings containing the IDs of all available voices.
     */
    UFUNCTION(BlueprintPure, Category = ADS)
    static TArray<FString> GetAvailableVoiceNames();
   
};
