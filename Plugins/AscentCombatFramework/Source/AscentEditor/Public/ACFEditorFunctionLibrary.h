// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "ACFEditorTypes.h"
#include "ACFGASTypes.h"
#include "CoreMinimal.h"
#include "GameplayTagContainer.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include <Engine/Texture2D.h>

#include "ACFEditorFunctionLibrary.generated.h"

class AACFCharacter;
class UACFAbilitySet;
class UACFActionsSet;
class UACFCharacterDataAsset;
class UBlueprint;
class UDataAsset;

/**
 *
 */
UCLASS()
class ASCENTEDITOR_API UACFEditorFunctionLibrary : public UBlueprintFunctionLibrary {
	GENERATED_BODY()

public:
	/** Retrieves all assets of a specific class from the content browser */
	UFUNCTION(BlueprintCallable, CallInEditor, Category = "ACF|Editor")
	static UObject* GetObjectCDO(TSubclassOf<UObject> AssetClass);

	/** Retrieves all assets of a specific class from the content browser */
	UFUNCTION(BlueprintCallable, CallInEditor, Category = "ACF|Editor")
	static UObject* GetAssetCDO(UObject* Asset);

	/** Retrieves all assets of a specific class from the content browser */
	UFUNCTION(BlueprintCallable, CallInEditor, Category = "ACF|Editor")
	static bool SaveObjectPackage(UObject* Object);

	UFUNCTION(BlueprintCallable, CallInEditor, Category = "ACF|Editor")
	static void AddAttributeInitToDataTable(UDataTable* DataTable, FName RowName, const FAttributeInit& RowData);

	static void AddRowToDataTable(UDataTable* DataTable, FName RowName, const FTableRowBase& RowData);

	/**
	 * Creates a new DataAsset in the Content Browser by copying data from a source DataAsset pointer.
	 * The DataAsset is saved to disk.
	 *
	 * @param SourceDataAsset The source DataAsset to copy from
	 * @param AssetName Name for the new asset
	 * @param PackagePath Content Browser path (e.g. "/Game/MyFolder")
	 * @param OutCreatedDataAsset Output: the created DataAsset on success (nullptr on failure)
	 * @return True if the DataAsset was successfully created and saved to disk, false otherwise
	 */
	UFUNCTION(BlueprintCallable, CallInEditor, Category = "ACF|Editor")
	static bool CreateDataAssetFromPointer(UDataAsset* SourceDataAsset, const FString& AssetName, const FString& PackagePath, UDataAsset*& OutCreatedDataAsset);

	/**
	 * Creates a new Blueprint in the Content Browser by copying data from a source UObject pointer.
	 * The Blueprint's CDO is populated with the source object's properties and saved to disk.
	 * Use CreateDataAssetFromPointer for DataAsset classes.
	 *
	 * @param SourceObject The source object to copy from (or Blueprint's CDO if SourceObject is a Blueprint)
	 * @param AssetName Name for the new Blueprint asset
	 * @param PackagePath Content Browser path (e.g. "/Game/MyFolder")
	 * @param OutCreatedBlueprint Output: the created Blueprint on success (nullptr on failure)
	 * @return True if the Blueprint was successfully created and saved to disk, false otherwise
	 */
	UFUNCTION(BlueprintCallable, CallInEditor, Category = "ACF|Editor")
	static bool CreateBlueprintFromPointer(UObject* SourceObject, const FString& AssetName, const FString& PackagePath, UBlueprint*& OutCreatedBlueprint);

	/** Wrapper for ACFEditorSettings::GetAssetCreatorDefaultClassByTag. Gets the default class for the given tag. */
	UFUNCTION(BlueprintCallable, CallInEditor, Category = "ACF|Editor|Asset Creator")
	static bool GetAssetCreatorDefaultClassByTag(FGameplayTag Tag, TSubclassOf<UObject>& OutClass);

	/** Wrapper for ACFEditorSettings::HasAssetCreatorDefaultClass. Returns true if a default class exists for the tag. */
	UFUNCTION(BlueprintCallable, CallInEditor, Category = "ACF|Editor|Asset Creator")
	static bool HasAssetCreatorDefaultClass(FGameplayTag Tag);

	/** Wrapper for ACFEditorSettings::GetAssetCreatorDefaultClassByIndex. Gets a default class by index. */
	UFUNCTION(BlueprintCallable, CallInEditor, Category = "ACF|Editor|Asset Creator")
	static bool GetAssetCreatorDefaultClassByIndex(int32 Index, FGameplayTag& OutTag, TSubclassOf<UObject>& OutClass);

	/** Wrapper for ACFEditorSettings::GetAssetCreatorDefaultClassesNum. Returns the number of default class entries. */
	UFUNCTION(BlueprintCallable, CallInEditor, Category = "ACF|Editor|Asset Creator")
	static int32 GetAssetCreatorDefaultClassesNum();

	/** Wrapper for ACFEditorSettings::GetAssetCreatorDefaultClasses. Returns the full tag->class dictionary (resolved). */
	UFUNCTION(BlueprintCallable, CallInEditor, Category = "ACF|Editor|Asset Creator")
	static TMap<FGameplayTag, TSubclassOf<UObject>> GetAssetCreatorDefaultClasses();

	/** Wrapper for ACFEditorSettings::GetAssetCreatorDisplayNameByTag. Gets the UI display name for the given tag. */
	UFUNCTION(BlueprintCallable, CallInEditor, Category = "ACF|Editor|Asset Creator")
	static bool GetAssetCreatorDisplayNameByTag(FGameplayTag Tag, FText& OutDisplayName);

	/** Wrapper for ACFEditorSettings::GetAssetCreatorEntryByTag. Returns the full FAssetCreatorDefaultClassEntry (Tag, Class, DisplayName, Description) for the given tag. */
	UFUNCTION(BlueprintCallable, CallInEditor, Category = "ACF|Editor|Asset Creator")
	static bool GetAssetCreatorEntryByTag(FGameplayTag Tag, FAssetCreatorDefaultClassEntry& OutEntry);

	/**
	 * Creates a UACFCharacterDataAsset from an ACFCharacter: extracts data from all components, creates the asset, and saves to disk.
	 * Uses UACFEditorSubsystem::FillCharacterDataFromCharacter and CreateDataAssetFromPointer.
	 * @param Character The source ACFCharacter
	 * @param AssetName Fallback name for the new asset; Blueprint-backed characters use DA_<BlueprintName>
	 * @param PackagePath Content Browser path (e.g. "/Game/Characters")
	 * @param OutCreatedDataAsset The created and saved UACFCharacterDataAsset
	 * @return True if successful
	 */
	UFUNCTION(BlueprintCallable, CallInEditor, Category = "ACF|Editor")
	static bool CreateCharacterDataAssetFromCharacter(class AACFCharacter* Character, const FString& AssetName, const FString& PackagePath, class UACFCharacterDataAsset*& OutCreatedDataAsset);

	/**
	 * Migrates all given ActionsSets into AbilitySets.
	 * Each resulting AbilitySet will be created in the folder /Game/Migrated/AbilitySets/
	 * and will include a 1:1 copy of all action data (including instanced UACFActionAbility).
	 *
	 * @param SourceSets The list of UACFActionsSet assets to migrate.
	 */
	UFUNCTION(CallInEditor, BlueprintCallable, Category = "ACF|Migration")
	static bool ConvertActionsSetsToAbilitySets(UACFActionsSet* SourceSet, const FString& FolderPath = "/Game/Migrated");

	static UACFAbilitySet* CreateAbilitySetAsset(const FString& FolderPath, const FString& AssetName);


	/**
	 * List of files that will need to be copied completely
	 * This ensures all plugin settings are properly configured in the project.
	 *
	 * @param PluginName The name of the plugin (e.g., "AscentCombatFramework")
	 * @return True if the file was successfully copied, false otherwise
	 */
	UFUNCTION(BlueprintCallable, CallInEditor, Category = "ACF|Project Setup")
	static bool CopyPluginConfigToProject(const TArray<FString>& filesToCopy, const FString& PluginName = "AscentCombatFramework");

	/**
	 * Adds collision channel and profile settings from the plugin to the project's DefaultEngine.ini.
	 * This configures custom collision channels needed by ACF systems.
	 *
	 * @param PluginName The name of the plugin to read collision settings from
	 * @return True if collision settings were successfully added, false otherwise
	 */
	UFUNCTION(BlueprintCallable, CallInEditor, Category = "ACF|Project Setup")
	static bool AddCollisionSettingsToProject(const FString& PluginName = "AscentCombatFramework");

	/**
	 * Adds gameplay tag settings from the plugin to the project's DefaultGameplayTags.ini.
	 * This ensures all ACF gameplay tags are properly registered in the project.
	 *
	 * @param PluginName The name of the plugin to read tag settings from
	 * @return True if tag settings were successfully added, false otherwise
	 */
	UFUNCTION(BlueprintCallable, CallInEditor, Category = "ACF|Project Setup")
	static bool AddGameplayTagSettingsToProject(const FString& PluginName = "AscentCombatFramework");

	/**
	 * Adds default game user settings from the plugin to the project's DefaultGameUserSettings.ini.
	 * This configures default game options like graphics quality, controls, etc.
	 *
	 * @param PluginName The name of the plugin to read user settings from
	 * @return True if user settings were successfully added, false otherwise
	 */
	UFUNCTION(BlueprintCallable, CallInEditor, Category = "ACF|Project Setup")
	static bool AddGameUserSettingsToProject(const FString& PluginName = "AscentCombatFramework");

	/**
	 * Adds mandatory ACF engine class overrides to the project's DefaultEngine.ini.
	 * Sets GameUserSettingsClassName and GameViewportClientClassName under [/Script/Engine.Engine].
	 *
	 * @param PluginName The name of the plugin to read engine settings from
	 * @return True if engine class settings were successfully added, false otherwise
	 */
	UFUNCTION(BlueprintCallable, CallInEditor, Category = "ACF|Project Setup")
	static bool AddEngineClassSettingsToProject(const FString& PluginName = "AscentCombatFramework");

	/**
	 * Replaces a specific section in a project config .ini file with the same section
	 * read from the plugin's config .ini file. If the section does not exist in the
	 * project config it will be appended. Useful for deploying ACF U default configs.
	 *
	 * @param ConfigFileName  The config file name (e.g. "DefaultEngine.ini")
	 * @param SectionName     The INI section to replace (e.g. "/Script/Engine.CollisionProfile")
	 * @return True if the section was successfully replaced or added
	 */
	UFUNCTION(BlueprintCallable, CallInEditor, Category = "ACF|Project Setup")
	static bool ReplaceConfigSectionFromPlugin(const FString& ConfigFileName, const FString& SectionName);

	/**
	 * Performs all ACF project setup steps in one call:
	 * - Copies DefaultPlugins.ini, DefaultGameplayTags.ini, DefaultInput.ini
	 * - Adds collision profiles and physics surface settings
	 * - Adds gameplay tag settings
	 * - Adds mandatory engine class overrides (GameUserSettingsClassName, GameViewportClientClassName)
	 * - Copies editor splash images from FullSample/Splash to Content/Splash (if FullSample is installed)
	 *
	 * @param PluginName The name of the plugin to configure
	 * @return True if all setup steps completed successfully, false otherwise
	 */
	UFUNCTION(BlueprintCallable, CallInEditor, Category = "ACF|Project Setup")
	static bool SetupACFProjectConfiguration(const FString& PluginName = "AscentCombatFramework");

	/**
	 * Copies all editor splash images from Content/FullSample/Splash to Content/Splash.
	 * The Unreal Editor uses Content/Splash for the editor splash (e.g. EdSplash*.png).
	 * If FullSample/Splash does not exist this step is silently skipped (not an error).
	 *
	 * @return True if copy succeeded or FullSample/Splash was not found; false on copy failure.
	 */
	UFUNCTION(BlueprintCallable, CallInEditor, Category = "ACF|Project Setup")
	static bool AddFullSampleEditorSplashToProject();

	/**
	 * Returns the name of the plugin that contains the AscentEditor module (this module).
	 * Use when the module may live in different plugins (e.g. AscentCombatFramework, ACFUltimate).
	 */
	UFUNCTION(BlueprintCallable, CallInEditor, Category = "ACF|Editor")
	static FString GetPluginName();

	/**
	 * Returns the name of the plugin that contains the given module.
	 * @param ModuleName Module name to look up (e.g. "AscentEditor", "AscentMapsEditor")
	 * @return Plugin name, or empty string if not found
	 */
	UFUNCTION(BlueprintCallable, CallInEditor, Category = "ACF|Editor")
	static FString GetPluginNameForModule(const FString& ModuleName);

	/**
	 * Returns the friendly name of the plugin (from .uplugin FriendlyName).
	 * Use to distinguish ACF / ACF J / ACF Ultimate in editor widgets (e.g. for logo).
	 * @return Friendly name (e.g. "Ascent Combat Framework Ultimate") or plugin name if not found
	 */
	UFUNCTION(BlueprintCallable, CallInEditor, Category = "ACF|Editor")
	static FString GetPluginFriendlyName();

private:
	// Helper function to read an INI file from the plugin's Config folder
	static bool ReadPluginConfigFile(const FString& PluginName, const FString& ConfigFileName, TArray<FString>& OutLines);

	// Helper function to append or merge sections into a project config file
	static bool MergeConfigSection(const FString& ProjectConfigPath, const FString& SectionName, const TArray<FString>& SectionLines, bool bAppendIfExists = true);

	// Helper: replaces an entire section (header + body) in a config file, or appends it if missing
	static bool ReplaceConfigSectionInFile(const FString& ConfigFilePath, const FString& SectionName, const TArray<FString>& NewSectionLines);

	// Helper: extracts the body lines of a specific section from raw INI lines (excludes the header)
	static bool ExtractSectionFromLines(const TArray<FString>& Lines, const FString& SectionName, TArray<FString>& OutSectionLines);

	// Helper function to get the project's Config directory path
	static FString GetProjectConfigDirectory();

	// Helper function to get the plugin's Config directory path
	static FString GetPluginConfigDirectory(const FString& PluginName);

	// Helper function to get the FullSample Splash directory path (Content/FullSample/Splash)
	static FString GetFullSampleSplashDirectory();
};
