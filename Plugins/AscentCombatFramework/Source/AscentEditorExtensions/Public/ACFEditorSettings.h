// Copyright (C) Developed by Pask & OlssonDev, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "ACFAssetCreatorDataAsset.h"
#include "ACFEditorTypes.h"
#include "ACFPlacementDataAsset.h"
#include "CoreMinimal.h"
#include "GameplayTagContainer.h"

#include "ACFEditorSettings.generated.h"

/**
 * Editor settings for Ascent Combat Framework.
 */
UCLASS(config = Plugins, Defaultconfig, meta = (DisplayName = "Ascent Editor Settings"))
class ASCENTEDITOREXTENSIONS_API UACFEditorSettings : public UDeveloperSettings {
	GENERATED_BODY()

public:
	virtual void PostEditChangeProperty(struct FPropertyChangedEvent& PropertyChangedEvent) override;

	/** Returns the style set name used for placement mode icons. */
	FName GetStyleName() const { return StyleName; }

	/**
	 * Returns the merged placement tab configurations from all assets in PlacementEntriesAssets.
	 * Assets are iterated in order and their Categories arrays are appended, allowing plugin
	 * assets and project assets to coexist as separate entries in the list.
	 */
	TArray<FPlaceCategoryConfig> GetPlacementCategories() const;

	/** Returns true if asset scanning is limited to assigned folders only. */
	bool GetScanOnlyAssignedFolders() const { return ScanOnlyAssignedFolders; }

	/** Returns the list of paths to scan for assets when ScanOnlyAssignedFolders is enabled. */
	TArray<FString> GetAssetPaths() const { return AssetPaths; }

	/** Returns true if redirectors are auto-generated when assets are moved or renamed in the editor. */
	bool GetAutoGenerateRedirectors() const { return bAutoGenerateRedirectors; }

	/**
	 * Gets the default class associated with the given tag.
	 * @param Tag The GameplayTag key to look up (e.g. AssetCreator.DataAsset, AssetCreator.AbilitySet).
	 * @param OutClass The resolved class if found and valid.
	 * @return True if the tag exists and the class was successfully loaded, false otherwise.
	 */
	UFUNCTION(BlueprintCallable, Category = "ACF|Editor Settings")
	bool GetAssetCreatorDefaultClassByTag(FGameplayTag Tag, TSubclassOf<UObject>& OutClass) const;

	/**
	 * Checks if a default class exists for the given tag and is valid.
	 * @param Tag The GameplayTag key to look up.
	 * @return True if the tag exists and the associated class loads successfully.
	 */
	UFUNCTION(BlueprintCallable, Category = "ACF|Editor Settings")
	bool HasAssetCreatorDefaultClass(FGameplayTag Tag) const;

	/**
	 * Gets a default class by index (stable order, matches the array order in Project Settings).
	 * @param Index Zero-based index into the array.
	 * @param OutTag The tag at this index.
	 * @param OutClass The resolved class if valid.
	 * @return True if index is valid and class was loaded successfully.
	 */
	UFUNCTION(BlueprintCallable, Category = "ACF|Editor Settings")
	bool GetAssetCreatorDefaultClassByIndex(int32 Index, FGameplayTag& OutTag, TSubclassOf<UObject>& OutClass) const;

	/**
	 * Gets the UI display name for the given tag.
	 * @param Tag The GameplayTag key to look up.
	 * @param OutDisplayName The display name if the entry was found.
	 * @return True if the tag exists.
	 */
	UFUNCTION(BlueprintCallable, Category = "ACF|Editor Settings")
	bool GetAssetCreatorDisplayNameByTag(FGameplayTag Tag, FText& OutDisplayName) const;

	/**
	 * Returns the full FAssetCreatorDefaultClassEntry (Tag, Class, DisplayName, Description) for the given tag.
	 * @param Tag The GameplayTag key to look up.
	 * @param OutEntry The full entry struct if found.
	 * @return True if the tag exists.
	 */
	UFUNCTION(BlueprintCallable, Category = "ACF|Editor Settings")
	bool GetAssetCreatorEntryByTag(FGameplayTag Tag, FAssetCreatorDefaultClassEntry& OutEntry) const;

	/** Returns the number of entries in the active Asset Creator default-class list. */
	UFUNCTION(BlueprintCallable, Category = "ACF|Editor Settings")
	int32 GetAssetCreatorDefaultClassesNum() const;

	/**
	 * Returns all entries as a resolved tag->class map (entries with invalid classes are excluded).
	 * The TArray source order is preserved during iteration.
	 */
	UFUNCTION(BlueprintCallable, Category = "ACF|Editor Settings")
	TMap<FGameplayTag, TSubclassOf<UObject>> GetAssetCreatorDefaultClasses() const;

protected:
	/** Style set name for placement mode icons (e.g. "AscentEditorStyle"). */
	UPROPERTY(EditAnywhere, config, Category = "Placement Mode", meta = (DisplayName = "Style Name"))
	FName StyleName = "AscentEditorStyle";

	/**
	 * List of data assets that each contribute placement tabs to the Place Actors panel.
	 * All assets are merged in order: plugin assets first, then project-specific assets.
	 * This allows separating plugin-provided tabs from sample/project-specific tabs.
	 */
	UPROPERTY(EditAnywhere, config, Category = "Placement Mode",
		meta = (DisplayName = "Placement Entries Assets"))
	TArray<TSoftObjectPtr<UACFPlacementDataAsset>> PlacementEntriesAssets;

	/** If true, the plugin only scans the folders listed in AssetPaths for Assets/AssetActions/AssetFactory. */
	UPROPERTY(EditDefaultsOnly, config, Category = "Asset Scanning", meta = (DisplayName = "Scan Only Assigned Folders"))
	bool ScanOnlyAssignedFolders = false;

	/** Paths to scan when ScanOnlyAssignedFolders is enabled. Leave empty to scan all content. */
	UPROPERTY(EditDefaultsOnly, config, Category = "Asset Scanning", meta = (EditCondition = "ScanOnlyAssignedFolders", DisplayName = "Asset Paths"))
	TArray<FString> AssetPaths;

	/**
	 * Data asset that drives the Asset Creator default-class table.
	 * Create a UACFAssetCreatorDataAsset in your project, populate its DefaultClasses,
	 * then assign it here.
	 */
	UPROPERTY(EditAnywhere, config, Category = "Asset Creator",
		meta = (DisplayName = "Asset Creator Config Asset"))
	TSoftObjectPtr<UACFAssetCreatorDataAsset> AssetCreatorConfigAsset;

	/**
	 * When enabled, automatically appends a PackageRedirects entry to
	 * DefaultAscentCombatFramework.ini and BaseAscentCombatFramework.ini whenever an asset is moved or renamed in the editor.
	 * Disabled by default to avoid unintended INI modifications.
	 */
	UPROPERTY(EditAnywhere, config, Category = "Redirectors",
		meta = (DisplayName = "Auto-Generate Redirectors on Asset Move"))
	bool bAutoGenerateRedirectors = false;

private:
	/** Returns a copy of whichever Asset Creator entry list is currently active. */
	TArray<FAssetCreatorDefaultClassEntry> GetActiveAssetCreatorEntries() const;
};
