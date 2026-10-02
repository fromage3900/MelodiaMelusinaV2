// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "ACFGASTypes.h"
#include "ACFRPGTypes.h"
#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include <AttributeSet.h>
#include <GameplayTagContainer.h>

#include "ACFRPGFunctionLibrary.generated.h"

class UACFDifficultyManagerComponent;

/**
 *
 */
UCLASS()
class ASCENTGASRUNTIME_API UACFRPGFunctionLibrary : public UBlueprintFunctionLibrary {
    GENERATED_BODY()

public:
    /**
     * Attempts to extract the float values of the modifiers from a single GameplayEffect.
     *
     * @param effectClass The configuration of the GameplayEffect to inspect.
     * @param outModifiers The array that will be filled with extracted modifiers.
     * @return true if at least one modifier was extracted successfully, false otherwise.
     */
    UFUNCTION(BlueprintCallable, Category = ACF)
    static bool TryGetModifiersFromGameplayEffect(const FGameplayEffectConfig& effectClass, TArray<FGEModifier>& outModifiers);

    /**
     * Attempts to extract the float values of the modifiers from multiple GameplayEffects.
     *
     * @param effects The list of GameplayEffect configurations to inspect.
     * @param outModifiers The array that will be filled with extracted modifiers.
     * @return true if at least one modifier was extracted successfully, false otherwise.
     */
    UFUNCTION(BlueprintCallable, Category = ACF)
    static bool TryGetModifiersFromGameplayEffects(const TArray<FGameplayEffectConfig>& effects, TArray<FGEModifier>& outModifiers);

    /**
     * Applies the specified GameplayEffect to the target Actor's Ability System Component.
     *
     * @param effect The GameplayEffect configuration to apply.
     * @param targetActor The actor who will receive the effect.
     * @return The handle to the applied GameplayEffect, or an invalid handle if application failed.
     */
    UFUNCTION(BlueprintCallable, Category = ACF)
    static FActiveGameplayEffectHandle AddGameplayEffectToActor(FGameplayEffectConfig effect, AActor* targetActor);

    /**
     * Attempts to remove the specified active GameplayEffect from the target Actor's Ability System Component.
     *
     * @param effect The handle of the active GameplayEffect to remove.
     * @param targetActor The actor from whom the effect should be removed.
     */
    UFUNCTION(BlueprintCallable, Category = ACF)
    static void RemovesActiveGameplayEffectFromActor(const FActiveGameplayEffectHandle& effect, AActor* targetActor);

    /**
     * Adds a loose gameplay tag to the Ability System Component of the given actor.
     * This tag will be considered by the GAS for ability activation checks and tag queries.
     *
     * @param TargetActor The actor that owns the ASC.
     * @param TagToAdd The gameplay tag to add.
     */
    UFUNCTION(BlueprintCallable, Category = ACF)
    static void AddGameplayTagToActor(AActor* TargetActor, const FGameplayTag& TagToAdd);

    /**
     * Remove a loose gameplay tag to the Ability System Component of the given actor.
     * This tag will be considered by the GAS for ability activation checks and tag queries.
     *
     * @param TargetActor The actor that owns the ASC.
     * @param TagToAdd The gameplay tag to add.
     */
    UFUNCTION(BlueprintCallable, Category = ACF)
    static void RemoveGameplayTagFromActor(AActor* TargetActor, const FGameplayTag& TagToRemove);

    // ========== Difficulty Scaling ==========

    /** Returns the Difficulty Manager component from the GameState. */
    UFUNCTION(BlueprintPure, meta = (WorldContext = "WorldContextObject"), Category = "ACF|Difficulty")
    static UACFDifficultyManagerComponent* GetDifficultyManager(const UObject* WorldContextObject);

    /** Returns the current game difficulty level tag from the GameState. */
    UFUNCTION(BlueprintPure, meta = (WorldContext = "WorldContextObject"), Category = "ACF|Difficulty")
    static FGameplayTag GetCurrentDifficultyLevel(const UObject* WorldContextObject);

    /**
     * Sets the current game difficulty level on the GameState.
     * Triggers OnDifficultyChanged and causes affected attribute components to reinitialize.
     * Server-only.
     */
    UFUNCTION(BlueprintCallable, BlueprintAuthorityOnly, meta = (WorldContext = "WorldContextObject"), Category = "ACF|Difficulty")
    static void SetDifficultyLevel(const UObject* WorldContextObject, const FGameplayTag& NewDifficultyLevel);

    /**
     * Returns the Difficulty Scaling DataTable configured in Project Settings (Ascent GAS Settings).
     */
    UFUNCTION(BlueprintPure, Category = "ACF|Difficulty")
    static UDataTable* GetDifficultyScalingTable();

    /**
     * Looks up the DataTable row for the given difficulty level.
     * @param DifficultyLevel The difficulty tag to look up.
     * @param OutScaling The resulting row data if found.
     * @return True if a matching row was found.
     */
    UFUNCTION(BlueprintCallable, Category = "ACF|Difficulty")
    static bool TryGetDifficultyScaling(const FGameplayTag& DifficultyLevel, FACFDifficultyScaling& OutScaling);

    /**
     * Returns the multiplier for a specific GAS attribute at a given difficulty level.
     * Returns 1.0 if no scaling is defined for that attribute or difficulty.
     */
    UFUNCTION(BlueprintPure, Category = "ACF|Difficulty")
    static float GetDifficultyMultiplierForAttribute(const FGameplayTag& DifficultyLevel, const FGameplayAttribute& Attribute);

    // ========== Difficulty UI Conversions ==========

    /**
     * Returns the 0-based index of the given difficulty tag within the DataTable row order.
     * Returns INDEX_NONE (-1) if the tag is not found or the table is not configured.
     * Useful for driving spinner / combo-box widgets that work with integer indices.
     */
    UFUNCTION(BlueprintPure, Category = "ACF|Difficulty")
    static int32 DifficultyTagToIndex(const FGameplayTag& DifficultyTag);

    /**
     * Returns the difficulty tag at the given 0-based DataTable row index.
     * Returns an invalid tag if the index is out of range or the table is not configured.
     */
    UFUNCTION(BlueprintPure, Category = "ACF|Difficulty")
    static FGameplayTag DifficultyTagAtIndex(int32 Index);

    /**
     * Returns the localized display name (UIName) for the given difficulty tag as defined in
     * the DifficultyScaling DataTable. Falls back to the leaf segment of the tag string
     * (e.g. "Normal" from "ACF.Difficulty.Normal") when UIName is empty.
     */
    UFUNCTION(BlueprintPure, Category = "ACF|Difficulty")
    static FText GetDifficultyDisplayName(const FGameplayTag& DifficultyTag);

    /**
     * Returns the localized description (UIDescription) for the given difficulty tag as defined in
     * the DifficultyScaling DataTable. Returns empty text when no description is configured.
     */
    UFUNCTION(BlueprintPure, Category = "ACF|Difficulty")
    static FText GetDifficultyDescription(const FGameplayTag& DifficultyTag);

    /**
     * Returns an ordered array of all difficulty tags from the DataTable.
     * By default, the order matches the DataTable row order and is consistent with DifficultyTagToIndex.
     * If bSortByCoefficient is true, tags are sorted by their average attribute multiplier.
     * Useful for populating spinners, combo boxes, or any list-based UI selector.
     */
    UFUNCTION(BlueprintPure, Category = "ACF|Difficulty")
    static TArray<FGameplayTag> GetAllDifficultyTags(bool bSortByCoefficient = false);

    /** Returns all localized difficulty display names, optionally sorted by average attribute multiplier. */
    UFUNCTION(BlueprintPure, Category = "ACF|Difficulty")
    static TArray<FText> GetAllDifficultyDisplayNames(bool bSortByCoefficient = false);

    /** Returns all localized difficulty descriptions, optionally sorted by average attribute multiplier. */
    UFUNCTION(BlueprintPure, Category = "ACF|Difficulty")
    static TArray<FText> GetAllDifficultyDescriptions(bool bSortByCoefficient = false);
};
