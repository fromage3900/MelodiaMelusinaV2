// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ACFEditorFunctionLibrary.h"
#include "AscentEditor.h"
#include "ACFAbilitySet.h"
#include "ACFEditorSettings.h"
#include "ACFEditorSubsystem.h"
#include "Actions/ACFActionsSet.h"
#include "Actions/ACFActionAbility.h"
#include "Actors/ACFCharacter.h"
#include "Data/ACFCharacterDataAsset.h"
#include "Editor.h"
#include "AssetToolsModule.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "Engine/Blueprint.h"
#include "Engine/DataAsset.h"
#include "GameplayTagContainer.h"
#include "Kismet2/KismetEditorUtilities.h"
#include "UObject/UObjectGlobals.h"
#include <EditorAssetLibrary.h>
#include <ImageUtils.h>
#include <ObjectTools.h>
#include <UObject/Package.h>
#include <UObject/SavePackage.h>
#include <Interfaces/IPluginManager.h>
#include <Misc/Paths.h>
#include "HAL/FileManager.h"
#include "Misc/FileHelper.h"

static const FString DefaultMigrationFolder = TEXT("/Game/Migrated/AbilitySets");

UObject* UACFEditorFunctionLibrary::GetObjectCDO(TSubclassOf<UObject> AssetClass)
{
	if (!AssetClass) {
		UE_LOG(LogTemp, Warning, TEXT("Invalid class passed to GetObjectCDO"));
		return nullptr;
	}
	return AssetClass->GetDefaultObject();
}

UObject* UACFEditorFunctionLibrary::GetAssetCDO(UObject* Asset)
{
	if (!IsValid(Asset))
	{
		UE_LOG(LogTemp, Error, TEXT(
			"\n================ [ACF] GetAssetCDO FAILED ================\n"
			"REASON : Input asset is NULL or invalid.\n"
			"HOW TO FIX:\n"
			"  1) Make sure the asset pin in your Blueprint is connected.\n"
			"  2) Drag a valid asset (Blueprint, Class, or DataAsset) from\n"
			"     the Content Browser into the input pin.\n"
			"==========================================================\n"
		));
		return nullptr;
	}

	const FString AssetName = Asset->GetName();
	const FString AssetPath = Asset->GetPathName();

	// --- Direct UClass input -------------------------------------------------
	if (UClass* AsClass = Cast<UClass>(Asset))
	{
		if (!IsValid(AsClass) || AsClass->HasAnyFlags(RF_NeedLoad | RF_NeedPostLoad | RF_BeginDestroyed | RF_FinishDestroyed))
		{
			UE_LOG(LogTemp, Error, TEXT(
				"\n================ [ACF] GetAssetCDO FAILED ================\n"
				"REASON : Class '%s' is not fully loaded / is being destroyed.\n"
				"HOW TO FIX:\n"
				"  1) In the Content Browser, right-click the asset and choose\n"
				"     'Asset Actions' -> 'Reload'.\n"
				"  2) Retry the operation.\n"
				"==========================================================\n"
			), *AssetPath);
			return nullptr;
		}

		UObject* CDO = AsClass->GetDefaultObject(false);
		if (!IsValid(CDO))
		{
			UE_LOG(LogTemp, Error, TEXT(
				"\n================ [ACF] GetAssetCDO FAILED ================\n"
				"REASON : Class '%s' has no valid Class Default Object (CDO).\n"
				"HOW TO FIX:\n"
				"  1) If this is a native C++ class, recompile the project.\n"
				"  2) If this is a Blueprint-generated class, open the source\n"
				"     Blueprint, press Compile (Ctrl+F7) and Save (Ctrl+S).\n"
				"==========================================================\n"
			), *AssetPath);
			return nullptr;
		}
		return CDO;
	}

	// --- UBlueprint input ----------------------------------------------------
	if (UBlueprint* BP = Cast<UBlueprint>(Asset))
	{
		if (BP->HasAnyFlags(RF_NeedLoad | RF_NeedPostLoad))
		{
			UE_LOG(LogTemp, Error, TEXT(
				"\n================ [ACF] GetAssetCDO FAILED ================\n"
				"REASON : Blueprint '%s' is not fully loaded.\n"
				"HOW TO FIX:\n"
				"  1) In the Content Browser, right-click '%s' and choose\n"
				"     'Asset Actions' -> 'Reload'.\n"
				"  2) Double-click to open it, then press Compile (Ctrl+F7)\n"
				"     and Save (Ctrl+S).\n"
				"  3) Retry the operation.\n"
				"==========================================================\n"
			), *AssetPath, *AssetName);
			return nullptr;
		}

		if (BP->Status == BS_Error)
		{
			UE_LOG(LogTemp, Error, TEXT(
				"\n================ [ACF] GetAssetCDO FAILED ================\n"
				"REASON : Blueprint '%s' has COMPILATION ERRORS (Status: BS_Error).\n"
				"HOW TO FIX:\n"
				"  1) Double-click '%s' in the Content Browser to open it.\n"
				"  2) Open the Message Log (Window -> Developer Tools ->\n"
				"     Message Log) and fix every red error shown there.\n"
				"  3) Press Compile (Ctrl+F7). The status icon must turn\n"
				"     green (Up To Date).\n"
				"  4) Press Save (Ctrl+S).\n"
				"  5) Retry the operation.\n"
				"==========================================================\n"
			), *AssetPath, *AssetName);
			return nullptr;
		}

		UClass* GenClass = BP->GeneratedClass;
		if (!IsValid(GenClass))
		{
			// Fallback: skeleton class is usually available even on partially
			// loaded / never-compiled BPs.
			GenClass = BP->SkeletonGeneratedClass;
		}

		if (!IsValid(GenClass))
		{
			UE_LOG(LogTemp, Error, TEXT(
				"\n================ [ACF] GetAssetCDO FAILED ================\n"
				"REASON : Blueprint '%s' has NO GeneratedClass.\n"
				"         This usually means it has never been compiled,\n"
				"         the compilation failed, or the asset was loaded\n"
				"         only as a stub by the asset registry.\n"
				"HOW TO FIX:\n"
				"  1) Double-click '%s' in the Content Browser to open it.\n"
				"  2) Press the Compile button (top-left of the BP editor)\n"
				"     or Ctrl+F7. The icon must become green (Up To Date).\n"
				"  3) Press Save (Ctrl+S).\n"
				"  4) Close and re-open the editor IF the issue persists\n"
				"     (forces a clean reload of the generated class).\n"
				"  5) Retry the operation.\n"
				"==========================================================\n"
			), *AssetPath, *AssetName);
			return nullptr;
		}

		if (GenClass->HasAnyFlags(RF_NeedLoad | RF_NeedPostLoad | RF_BeginDestroyed | RF_FinishDestroyed))
		{
			UE_LOG(LogTemp, Error, TEXT(
				"\n================ [ACF] GetAssetCDO FAILED ================\n"
				"REASON : GeneratedClass of Blueprint '%s' is not fully\n"
				"         loaded or is being destroyed.\n"
				"HOW TO FIX:\n"
				"  1) Right-click '%s' in the Content Browser and choose\n"
				"     'Asset Actions' -> 'Reload'.\n"
				"  2) Open it, press Compile (Ctrl+F7), then Save (Ctrl+S).\n"
				"  3) Retry the operation.\n"
				"==========================================================\n"
			), *AssetPath, *AssetName);
			return nullptr;
		}

		// Use GetDefaultObject(false) so we never lazily create a CDO on a
		// class that is in a half-baked state -> avoids the original crash.
		UObject* CDO = GenClass->GetDefaultObject(false);
		if (!IsValid(CDO))
		{
			UE_LOG(LogTemp, Error, TEXT(
				"\n================ [ACF] GetAssetCDO FAILED ================\n"
				"REASON : Class Default Object (CDO) of Blueprint '%s' is\n"
				"         missing or invalid.\n"
				"HOW TO FIX:\n"
				"  1) Double-click '%s' in the Content Browser.\n"
				"  2) Press Compile (Ctrl+F7) - status MUST be green.\n"
				"  3) Press Save (Ctrl+S).\n"
				"  4) Retry the operation.\n"
				"==========================================================\n"
			), *AssetPath, *AssetName);
			return nullptr;
		}

		return CDO;
	}

	// --- Anything else (DataAsset, plain UObject instance, ...) --------------
	// Already a usable object: just return it.
	return Asset;
}

bool UACFEditorFunctionLibrary::SaveObjectPackage(UObject* Object)
{
	if (!Object) {
		UE_LOG(LogTemp, Warning, TEXT("Invalid object passed to SaveObjectPackage"));
		return false;
	}

	// Get the actual package, not just the outermost
	UPackage* Package = Object->GetPackage();
	if (!Package) {
		UE_LOG(LogTemp, Error, TEXT("Object has no valid package"));
		return false;
	}

	// Check if package is valid and not transient
	if (Package->HasAnyFlags(RF_Transient) || Package->GetName().StartsWith(TEXT("/Temp/"))) {
		UE_LOG(LogTemp, Error, TEXT("Cannot save transient or temporary package: %s"), *Package->GetName());
		return false;
	}

	// Generate unique filename to avoid conflicts
	FString PackageName = Package->GetName();
	FString FilePath = FPackageName::LongPackageNameToFilename(PackageName, FPackageName::GetAssetPackageExtension());

	// Handle duplicate names by adding suffix
	FString UniqueFilePath = FilePath;
	int32 Counter = 1;
	while (FPaths::FileExists(UniqueFilePath)) {
		FString BaseName = FPaths::GetBaseFilename(FilePath);
		FString Directory = FPaths::GetPath(FilePath);
		FString Extension = FPaths::GetExtension(FilePath, true);

		UniqueFilePath = FPaths::Combine(Directory, FString::Printf(TEXT("%s_%d%s"), *BaseName, Counter, *Extension));
		Counter++;

		// Safety check to prevent infinite loop
		if (Counter > 1000) {
			UE_LOG(LogTemp, Error, TEXT("Too many duplicate files, aborting save"));
			return false;
		}
	}

	// Check if file is read-only
	if (FPaths::FileExists(UniqueFilePath) && IFileManager::Get().IsReadOnly(*UniqueFilePath)) {
		UE_LOG(LogTemp, Error, TEXT("Cannot save package: file is read-only -> %s"), *UniqueFilePath);
		return false;
	}

	// Mark package as dirty
	Package->MarkPackageDirty();

	// Setup save parameters correctly
	FSavePackageArgs SaveArgs;
	SaveArgs.TopLevelFlags = RF_Public | RF_Standalone;
	SaveArgs.SaveFlags = SAVE_NoError | SAVE_FromAutosave;
	SaveArgs.bForceByteSwapping = false;
	SaveArgs.bWarnOfLongFilename = true;

	// Ensure the directory exists
	FString Directory = FPaths::GetPath(UniqueFilePath);
	if (!IFileManager::Get().DirectoryExists(*Directory)) {
		IFileManager::Get().MakeDirectory(*Directory, true);
	}

	// Attempt to save
	bool bSaveResult = UPackage::SavePackage(Package, Object, *UniqueFilePath, SaveArgs);

	if (bSaveResult) {
		UE_LOG(LogTemp, Log, TEXT("Successfully saved package to: %s"), *UniqueFilePath);
	}
	else {
		UE_LOG(LogTemp, Error, TEXT("Failed to save package to: %s"), *UniqueFilePath);
	}

	return bSaveResult;
}

void UACFEditorFunctionLibrary::AddAttributeInitToDataTable(UDataTable* DataTable, FName RowName, const FAttributeInit& RowData)
{
	AddRowToDataTable(DataTable, RowName, RowData);
}

void UACFEditorFunctionLibrary::AddRowToDataTable(UDataTable* DataTable, FName RowName, const FTableRowBase& RowData)
{

	if (!DataTable || RowName.IsNone()) {
		return;
	}

	if (!DataTable->GetRowMap().Contains(RowName)) {
		DataTable->AddRow(RowName, RowData);

		DataTable->MarkPackageDirty();
		DataTable->PostEditChange();
		DataTable->Modify();

		FAssetRegistryModule::AssetCreated(DataTable);
	}
}

bool UACFEditorFunctionLibrary::CreateDataAssetFromPointer(UDataAsset* SourceDataAsset, const FString& AssetName, const FString& PackagePath, UDataAsset*& OutCreatedDataAsset)
{
	OutCreatedDataAsset = nullptr;

	if (!SourceDataAsset)
	{
		UE_LOG(LogTemp, Warning, TEXT("CreateDataAssetFromPointer: SourceDataAsset is null"));
		return false;
	}

	UClass* AssetClass = SourceDataAsset->GetClass();
	if (!AssetClass->IsChildOf(UDataAsset::StaticClass()))
	{
		UE_LOG(LogTemp, Warning, TEXT("CreateDataAssetFromPointer: Source object is not a DataAsset"));
		return false;
	}

	FAssetToolsModule& AssetToolsModule = FModuleManager::Get().LoadModuleChecked<FAssetToolsModule>("AssetTools");
	FString UniquePackageName;
	FString UniqueAssetName;
	AssetToolsModule.Get().CreateUniqueAssetName(PackagePath / AssetName, TEXT(""), UniquePackageName, UniqueAssetName);

	UDataAsset* NewAsset = Cast<UDataAsset>(AssetToolsModule.Get().CreateAsset(
		UniqueAssetName,
		PackagePath,
		AssetClass,
		nullptr
	));

	if (!NewAsset)
	{
		return false;
	}

	UEngine::CopyPropertiesForUnrelatedObjects(SourceDataAsset, NewAsset);
	NewAsset->MarkPackageDirty();
	FAssetRegistryModule::AssetCreated(NewAsset);

	const bool bSaved = SaveObjectPackage(NewAsset);
	if (bSaved)
	{
		OutCreatedDataAsset = NewAsset;
		UE_LOG(LogTemp, Log, TEXT("DataAsset successfully created and saved: %s"), *UniqueAssetName);
	}
	else
	{
		UE_LOG(LogTemp, Warning, TEXT("DataAsset created but failed to save to disk: %s"), *UniqueAssetName);
	}
	return bSaved;
}

bool UACFEditorFunctionLibrary::CreateBlueprintFromPointer(UObject* SourceObject, const FString& AssetName, const FString& PackagePath, UBlueprint*& OutCreatedBlueprint)
{
	OutCreatedBlueprint = nullptr;

	if (!SourceObject)
	{
		UE_LOG(LogTemp, Warning, TEXT("CreateBlueprintFromPointer: SourceObject is null"));
		return false;
	}

	UClass* AssetClass = SourceObject->GetClass();

	// Handle Blueprint: use GeneratedClass and its CDO
	if (UBlueprint* BlueprintAsset = Cast<UBlueprint>(SourceObject))
	{
		if (BlueprintAsset->GeneratedClass)
		{
			AssetClass = BlueprintAsset->GeneratedClass;
			SourceObject = BlueprintAsset->GeneratedClass->GetDefaultObject();
		}
	}

	if (AssetClass->IsChildOf(UDataAsset::StaticClass()))
	{
		UE_LOG(LogTemp, Warning, TEXT("CreateBlueprintFromPointer: Use CreateDataAssetFromPointer for DataAsset classes"));
		return false;
	}

	if (!FKismetEditorUtilities::CanCreateBlueprintOfClass(AssetClass))
	{
		UE_LOG(LogTemp, Warning, TEXT("CreateBlueprintFromPointer: Class %s cannot be used to create a Blueprint"), *AssetClass->GetName());
		return false;
	}

	FAssetToolsModule& AssetToolsModule = FModuleManager::Get().LoadModuleChecked<FAssetToolsModule>("AssetTools");
	FString UniquePackageName;
	FString UniqueAssetName;
	AssetToolsModule.Get().CreateUniqueAssetName(PackagePath / AssetName, TEXT(""), UniquePackageName, UniqueAssetName);

	UPackage* Package = CreatePackage(*UniquePackageName);
	UBlueprint* NewBlueprint = FKismetEditorUtilities::CreateBlueprint(
		AssetClass,
		Package,
		FName(*UniqueAssetName),
		BPTYPE_Normal,
		UBlueprint::StaticClass(),
		UBlueprintGeneratedClass::StaticClass()
	);

	if (!NewBlueprint || !NewBlueprint->GeneratedClass)
	{
		return false;
	}

	UObject* DestObject = NewBlueprint->GeneratedClass->GetDefaultObject();
	UEngine::CopyPropertiesForUnrelatedObjects(SourceObject, DestObject);
	NewBlueprint->MarkPackageDirty();
	FAssetRegistryModule::AssetCreated(NewBlueprint);

	const bool bSaved = SaveObjectPackage(NewBlueprint);
	if (bSaved)
	{
		OutCreatedBlueprint = NewBlueprint;
		UE_LOG(LogTemp, Log, TEXT("Blueprint successfully created and saved: %s"), *UniqueAssetName);
	}
	else
	{
		UE_LOG(LogTemp, Warning, TEXT("Blueprint created but failed to save to disk: %s"), *UniqueAssetName);
	}
	return bSaved;
}

bool UACFEditorFunctionLibrary::GetAssetCreatorDefaultClassByTag(FGameplayTag Tag, TSubclassOf<UObject>& OutClass)
{
	if (const UACFEditorSettings* Settings = GetDefault<UACFEditorSettings>())
	{
		return Settings->GetAssetCreatorDefaultClassByTag(Tag, OutClass);
	}
	OutClass = nullptr;
	return false;
}

bool UACFEditorFunctionLibrary::HasAssetCreatorDefaultClass(FGameplayTag Tag)
{
	if (const UACFEditorSettings* Settings = GetDefault<UACFEditorSettings>())
	{
		return Settings->HasAssetCreatorDefaultClass(Tag);
	}
	return false;
}

bool UACFEditorFunctionLibrary::GetAssetCreatorDefaultClassByIndex(int32 Index, FGameplayTag& OutTag, TSubclassOf<UObject>& OutClass)
{
	if (const UACFEditorSettings* Settings = GetDefault<UACFEditorSettings>())
	{
		return Settings->GetAssetCreatorDefaultClassByIndex(Index, OutTag, OutClass);
	}
	OutTag = FGameplayTag();
	OutClass = nullptr;
	return false;
}

int32 UACFEditorFunctionLibrary::GetAssetCreatorDefaultClassesNum()
{
	if (const UACFEditorSettings* Settings = GetDefault<UACFEditorSettings>())
	{
		return Settings->GetAssetCreatorDefaultClassesNum();
	}
	return 0;
}

TMap<FGameplayTag, TSubclassOf<UObject>> UACFEditorFunctionLibrary::GetAssetCreatorDefaultClasses()
{
	if (const UACFEditorSettings* Settings = GetDefault<UACFEditorSettings>())
	{
		return Settings->GetAssetCreatorDefaultClasses();
	}
	return TMap<FGameplayTag, TSubclassOf<UObject>>();
}

bool UACFEditorFunctionLibrary::GetAssetCreatorDisplayNameByTag(FGameplayTag Tag, FText& OutDisplayName)
{
	if (const UACFEditorSettings* Settings = GetDefault<UACFEditorSettings>())
	{
		return Settings->GetAssetCreatorDisplayNameByTag(Tag, OutDisplayName);
	}
	return false;
}

bool UACFEditorFunctionLibrary::GetAssetCreatorEntryByTag(FGameplayTag Tag, FAssetCreatorDefaultClassEntry& OutEntry)
{
	if (const UACFEditorSettings* Settings = GetDefault<UACFEditorSettings>())
	{
		return Settings->GetAssetCreatorEntryByTag(Tag, OutEntry);
	}
	return false;
}

bool UACFEditorFunctionLibrary::CreateCharacterDataAssetFromCharacter(AACFCharacter* Character, const FString& AssetName, const FString& PackagePath, UACFCharacterDataAsset*& OutCreatedDataAsset)
{
	OutCreatedDataAsset = nullptr;

	if (!Character)
	{
		UE_LOG(LogTemp, Warning, TEXT("CreateCharacterDataAssetFromCharacter: Character is null"));
		return false;
	}

	UACFEditorSubsystem* EditorSubsystem = GEditor ? GEditor->GetEditorSubsystem<UACFEditorSubsystem>() : nullptr;
	if (!EditorSubsystem)
	{
		UE_LOG(LogTemp, Warning, TEXT("CreateCharacterDataAssetFromCharacter: UACFEditorSubsystem not available"));
		return false;
	}

	FString CharacterDataAssetName = AssetName;
	if (const UBlueprint* CharacterBlueprint = Cast<UBlueprint>(Character->GetClass()->ClassGeneratedBy))
	{
		CharacterDataAssetName = FString::Printf(TEXT("DA_%s"), *CharacterBlueprint->GetName());
	}

	UACFCharacterDataAsset* TempDataAsset = NewObject<UACFCharacterDataAsset>(GetTransientPackage(), UACFCharacterDataAsset::StaticClass());
	if (!EditorSubsystem->FillCharacterDataFromCharacter(Character, TempDataAsset))
	{
		UE_LOG(LogTemp, Warning, TEXT("CreateCharacterDataAssetFromCharacter: FillCharacterDataFromCharacter failed"));
		return false;
	}

	UDataAsset* CreatedDataAsset = nullptr;
	const bool bSuccess = CreateDataAssetFromPointer(TempDataAsset, CharacterDataAssetName, PackagePath, CreatedDataAsset);
	OutCreatedDataAsset = Cast<UACFCharacterDataAsset>(CreatedDataAsset);
	return bSuccess;
}

UACFAbilitySet* UACFEditorFunctionLibrary::CreateAbilitySetAsset(const FString& AssetName, const FString& FolderPath)
{
	FString PackagePath = FolderPath / AssetName;
	PackagePath = PackagePath.Replace(TEXT("//"), TEXT("/"));

	if (!FPackageName::IsValidLongPackageName(PackagePath)) {
		UE_LOG(LogTemp, Error, TEXT("Invalid package path: %s"), *PackagePath);
		return nullptr;
	}

	UPackage* Package = CreatePackage(*PackagePath);
	if (!Package) {
		UE_LOG(LogTemp, Error, TEXT("Failed to create package: %s"), *PackagePath);
		return nullptr;
	}

	UACFAbilitySet* NewAsset = NewObject<UACFAbilitySet>(Package, UACFAbilitySet::StaticClass(), *AssetName, RF_Public | RF_Standalone);
	if (!NewAsset) {
		UE_LOG(LogTemp, Error, TEXT("Failed to instantiate asset: %s"), *AssetName);
		return nullptr;
	}

	FAssetRegistryModule::AssetCreated(NewAsset);
	Package->MarkPackageDirty();

	const FString PackageFilename = FPackageName::LongPackageNameToFilename(PackagePath, FPackageName::GetAssetPackageExtension());
	FSavePackageArgs args;
	args.SaveFlags = EObjectFlags::RF_Public | RF_Standalone;
	const bool bSuccess = UPackage::SavePackage(Package, NewAsset, *PackageFilename, args);

	if (!bSuccess) {
		UE_LOG(LogTemp, Warning, TEXT("Asset was created but failed to save: %s"), *PackagePath);
	}

	return NewAsset;
}

bool UACFEditorFunctionLibrary::ConvertActionsSetsToAbilitySets(UACFActionsSet* SourceSet, const FString& FolderPath)
{

	if (!SourceSet) {
		UE_LOG(LogTemp, Warning, TEXT("Null ActionSet found, skipping."));
		return false;
	}

	const FString SourceName = SourceSet->GetName();
	FString NewAssetName = FString::Printf(TEXT("AS_%s"), *SourceName);
	NewAssetName = NewAssetName.Replace(TEXT("_Default_"), TEXT(""), ESearchCase::IgnoreCase);
	NewAssetName = NewAssetName.Replace(TEXT("_C"), TEXT(""), ESearchCase::IgnoreCase);
	NewAssetName = NewAssetName.Replace(TEXT("_AS"), TEXT(""), ESearchCase::IgnoreCase);
	UACFAbilitySet* NewSet = UACFEditorFunctionLibrary::CreateAbilitySetAsset(NewAssetName, FolderPath);

	if (!NewSet) {
		UE_LOG(LogTemp, Error, TEXT("Failed to create ability set for %s"), *SourceName);
		return false;
	}

	for (const FActionState& ActionState : SourceSet->GetActionsRef()) {
		if (!IsValid(ActionState.Action)) {
			continue;
		}

		FActionAbilityConfig NewConfig;
		NewConfig.TriggeringTag = ActionState.TagName;
		NewConfig.AbilityLevel = 1;

		UObject* DuplicatedObject = StaticDuplicateObject(ActionState.Action, NewSet);
		UACFActionAbility* DuplicatedAction = Cast<UACFActionAbility>(DuplicatedObject);
		NewConfig.Action = DuplicatedAction;
		NewConfig.Action->SetAnimMontage(ActionState.MontageAction);
		NewSet->ActionAbilities.Add(NewConfig);
	}

	NewSet->MarkPackageDirty();
	UE_LOG(LogTemp, Log, TEXT("Created AbilitySet %s with %d actions"), *NewAssetName, NewSet->ActionAbilities.Num());
	return UACFEditorFunctionLibrary::SaveObjectPackage(NewSet);
}

FString UACFEditorFunctionLibrary::GetProjectConfigDirectory()
{
	// Get the project's Config directory path
	return FPaths::ProjectConfigDir();
}

FString UACFEditorFunctionLibrary::GetPluginConfigDirectory(const FString& PluginName)
{
	// Get the plugin's Config directory path
	TSharedPtr<IPlugin> Plugin = IPluginManager::Get().FindPlugin(PluginName);
	if (!Plugin.IsValid())
	{
		UE_LOG(LogTemp, Error, TEXT("Plugin '%s' not found"), *PluginName);
		return FString();
	}

	return FPaths::Combine(Plugin->GetBaseDir(), TEXT("Config"));
}

bool UACFEditorFunctionLibrary::ReadPluginConfigFile(const FString& PluginName, const FString& ConfigFileName, TArray<FString>& OutLines)
{
	FString PluginConfigDir = GetPluginConfigDirectory(PluginName);
	if (PluginConfigDir.IsEmpty())
	{
		return false;
	}

	FString ConfigFilePath = FPaths::Combine(PluginConfigDir, ConfigFileName);

	// Check if file exists
	if (!FPaths::FileExists(ConfigFilePath))
	{
		UE_LOG(LogTemp, Warning, TEXT("Config file not found: %s"), *ConfigFilePath);
		return false;
	}

	// Read the entire file
	if (!FFileHelper::LoadFileToStringArray(OutLines, *ConfigFilePath))
	{
		UE_LOG(LogTemp, Error, TEXT("Failed to read config file: %s"), *ConfigFilePath);
		return false;
	}

	UE_LOG(LogTemp, Log, TEXT("Successfully read config file: %s (%d lines)"), *ConfigFilePath, OutLines.Num());
	return true;
}

bool UACFEditorFunctionLibrary::MergeConfigSection(const FString& ProjectConfigPath, const FString& SectionName, const TArray<FString>& SectionLines, bool bAppendIfExists)
{
	// Read existing project config file
	TArray<FString> ExistingLines;
	bool bFileExists = FPaths::FileExists(ProjectConfigPath);

	if (bFileExists)
	{
		if (!FFileHelper::LoadFileToStringArray(ExistingLines, *ProjectConfigPath))
		{
			UE_LOG(LogTemp, Error, TEXT("Failed to read existing config file: %s"), *ProjectConfigPath);
			return false;
		}
	}

	// Find if section already exists
	int32 SectionStartIndex = INDEX_NONE;
	int32 SectionEndIndex = INDEX_NONE;
	FString SectionHeader = FString::Printf(TEXT("[%s]"), *SectionName);

	for (int32 i = 0; i < ExistingLines.Num(); i++)
	{
		FString Line = ExistingLines[i].TrimStartAndEnd();

		if (Line.Equals(SectionHeader, ESearchCase::IgnoreCase))
		{
			SectionStartIndex = i;
		}
		else if (SectionStartIndex != INDEX_NONE && Line.StartsWith(TEXT("[")))
		{
			// Found the next section
			SectionEndIndex = i;
			break;
		}
	}

	// If section doesn't exist or we want to append
	if (SectionStartIndex == INDEX_NONE || bAppendIfExists)
	{
		// Add section at the end if it doesn't exist
		if (SectionStartIndex == INDEX_NONE)
		{
			if (ExistingLines.Num() > 0)
			{
				ExistingLines.Add(TEXT("")); // Add blank line before new section
			}
			ExistingLines.Add(SectionHeader);
		}

		// Add all section lines
		for (const FString& Line : SectionLines)
		{
			ExistingLines.Add(Line);
		}
	}

	// Write the modified content back
	if (!FFileHelper::SaveStringArrayToFile(ExistingLines, *ProjectConfigPath))
	{
		UE_LOG(LogTemp, Error, TEXT("Failed to write config file: %s"), *ProjectConfigPath);
		return false;
	}

	UE_LOG(LogTemp, Log, TEXT("Successfully merged section [%s] into: %s"), *SectionName, *ProjectConfigPath);
	return true;
}

bool UACFEditorFunctionLibrary::ExtractSectionFromLines(const TArray<FString>& Lines, const FString& SectionName, TArray<FString>& OutSectionLines)
{
	OutSectionLines.Empty();
	const FString SectionHeader = FString::Printf(TEXT("[%s]"), *SectionName);
	bool bInsideSection = false;

	for (const FString& Line : Lines)
	{
		const FString Trimmed = Line.TrimStartAndEnd();

		if (Trimmed.Equals(SectionHeader, ESearchCase::IgnoreCase))
		{
			bInsideSection = true;
			continue;
		}

		if (bInsideSection)
		{
			if (Trimmed.StartsWith(TEXT("[")) && Trimmed.EndsWith(TEXT("]")))
			{
				break;
			}
			OutSectionLines.Add(Line);
		}
	}

	return bInsideSection;
}

bool UACFEditorFunctionLibrary::ReplaceConfigSectionInFile(const FString& ConfigFilePath, const FString& SectionName, const TArray<FString>& NewSectionLines)
{
	TArray<FString> FileLines;
	const bool bFileExists = FPaths::FileExists(ConfigFilePath);

	if (bFileExists)
	{
		if (!FFileHelper::LoadFileToStringArray(FileLines, *ConfigFilePath))
		{
			UE_LOG(LogTemp, Error, TEXT("ReplaceConfigSectionInFile: failed to read '%s'"), *ConfigFilePath);
			return false;
		}
	}

	const FString SectionHeader = FString::Printf(TEXT("[%s]"), *SectionName);

	int32 SectionStartIndex = INDEX_NONE;
	int32 SectionEndIndex = INDEX_NONE;

	for (int32 i = 0; i < FileLines.Num(); ++i)
	{
		const FString Trimmed = FileLines[i].TrimStartAndEnd();

		if (Trimmed.Equals(SectionHeader, ESearchCase::IgnoreCase))
		{
			SectionStartIndex = i;
		}
		else if (SectionStartIndex != INDEX_NONE && SectionEndIndex == INDEX_NONE
			&& Trimmed.StartsWith(TEXT("[")) && Trimmed.EndsWith(TEXT("]")))
		{
			SectionEndIndex = i;
			break;
		}
	}

	TArray<FString> Result;

	if (SectionStartIndex != INDEX_NONE)
	{
		if (SectionEndIndex == INDEX_NONE)
		{
			SectionEndIndex = FileLines.Num();
		}

		for (int32 i = 0; i < SectionStartIndex; ++i)
		{
			Result.Add(FileLines[i]);
		}

		Result.Add(SectionHeader);
		for (const FString& Line : NewSectionLines)
		{
			Result.Add(Line);
		}

		for (int32 i = SectionEndIndex; i < FileLines.Num(); ++i)
		{
			Result.Add(FileLines[i]);
		}
	}
	else
	{
		Result = FileLines;
		if (Result.Num() > 0)
		{
			Result.Add(TEXT(""));
		}
		Result.Add(SectionHeader);
		for (const FString& Line : NewSectionLines)
		{
			Result.Add(Line);
		}
	}

	if (!FFileHelper::SaveStringArrayToFile(Result, *ConfigFilePath))
	{
		UE_LOG(LogTemp, Error, TEXT("ReplaceConfigSectionInFile: failed to write '%s'"), *ConfigFilePath);
		return false;
	}

	UE_LOG(LogTemp, Log, TEXT("ReplaceConfigSectionInFile: section [%s] replaced in '%s'"), *SectionName, *ConfigFilePath);
	return true;
}

bool UACFEditorFunctionLibrary::ReplaceConfigSectionFromPlugin(const FString& ConfigFileName, const FString& SectionName)
{
	const FString PluginName = FAscentEditorModule::GetPluginName();

	TArray<FString> PluginLines;
	if (!ReadPluginConfigFile(PluginName, ConfigFileName, PluginLines))
	{
		UE_LOG(LogTemp, Error, TEXT("ReplaceConfigSectionFromPlugin: could not read '%s' from plugin '%s'"), *ConfigFileName, *PluginName);
		return false;
	}

	TArray<FString> SectionBody;
	if (!ExtractSectionFromLines(PluginLines, SectionName, SectionBody))
	{
		UE_LOG(LogTemp, Warning, TEXT("ReplaceConfigSectionFromPlugin: section [%s] not found in plugin's '%s'"), *SectionName, *ConfigFileName);
		return false;
	}

	const FString ProjectConfigPath = FPaths::Combine(GetProjectConfigDirectory(), ConfigFileName);
	return ReplaceConfigSectionInFile(ProjectConfigPath, SectionName, SectionBody);
}

bool UACFEditorFunctionLibrary::CopyPluginConfigToProject(const TArray<FString>& filesToCopy, const FString& PluginName)
{
	for (const FString& file : filesToCopy) {

		TArray<FString> PluginConfigLines;
		if (!ReadPluginConfigFile(PluginName, file, PluginConfigLines))
		{
			UE_LOG(LogTemp, Error, TEXT("Failed to read DefaultPlugins.ini from plugin '%s'"), *PluginName);
			return false;
		}

		// Get project config path
		const FString ProjectConfigPath = FPaths::Combine(GetProjectConfigDirectory(), file);

		// Simply overwrite the entire file
		if (!FFileHelper::SaveStringArrayToFile(PluginConfigLines, *ProjectConfigPath))
		{
			UE_LOG(LogTemp, Error, TEXT("Failed to write DefaultPlugins.ini to project Config folder"));
			return false;
		}

	}

	UE_LOG(LogTemp, Log, TEXT("Successfully copied files from plugin '%s' to project"), *PluginName);
	return true;
}

bool UACFEditorFunctionLibrary::AddCollisionSettingsToProject(const FString& PluginName)
{
	// Read collision settings from plugin's DefaultEngine.ini
	TArray<FString> PluginEngineConfig;
	if (!ReadPluginConfigFile(PluginName, TEXT("DefaultEngine.ini"), PluginEngineConfig))
	{
		UE_LOG(LogTemp, Warning, TEXT("No DefaultEngine.ini found in plugin '%s', skipping collision settings"), *PluginName);
		return false;
	}

	// Extract collision-related sections
	TArray<FString> CollisionProfileSettings;
	TArray<FString> CollisionChannelSettings;
	bool bInCollisionProfiles = false;
	bool bInCollisionChannels = false;

	for (const FString& Line : PluginEngineConfig)
	{
		FString TrimmedLine = Line.TrimStartAndEnd();

		// Check for section headers
		if (TrimmedLine.Equals(TEXT("[/Script/Engine.CollisionProfile]"), ESearchCase::IgnoreCase))
		{
			bInCollisionProfiles = true;
			bInCollisionChannels = false;
			continue;
		}
		else if (TrimmedLine.Equals(TEXT("[/Script/Engine.PhysicsSettings]"), ESearchCase::IgnoreCase))
		{
			bInCollisionChannels = true;
			bInCollisionProfiles = false;
			continue;
		}
		else if (TrimmedLine.StartsWith(TEXT("[")))
		{
			// New section started
			bInCollisionProfiles = false;
			bInCollisionChannels = false;
			continue;
		}

		// Add lines to appropriate arrays
		if (bInCollisionProfiles)
		{
			CollisionProfileSettings.Add(Line);
		}
		else if (bInCollisionChannels)
		{
			CollisionChannelSettings.Add(Line);
		}
	}

	// Get project's DefaultEngine.ini path
	FString ProjectEnginePath = FPaths::Combine(GetProjectConfigDirectory(), TEXT("DefaultEngine.ini"));

	// Merge collision profile settings
	bool bSuccess = true;
	if (CollisionProfileSettings.Num() > 0)
	{
		bSuccess &= MergeConfigSection(ProjectEnginePath, TEXT("/Script/Engine.CollisionProfile"), CollisionProfileSettings, true);
	}

	// Merge collision channel settings
	if (CollisionChannelSettings.Num() > 0)
	{
		bSuccess &= MergeConfigSection(ProjectEnginePath, TEXT("/Script/Engine.PhysicsSettings"), CollisionChannelSettings, true);
	}

	if (bSuccess)
	{
		UE_LOG(LogTemp, Log, TEXT("Successfully added collision settings to project from plugin '%s'"), *PluginName);
	}
	else
	{
		UE_LOG(LogTemp, Warning, TEXT("Partially failed to add collision settings to project from plugin '%s'"), *PluginName);
	}

	return bSuccess;
}

bool UACFEditorFunctionLibrary::AddGameplayTagSettingsToProject(const FString& PluginName)
{
	// Read gameplay tag settings from plugin's DefaultGameplayTags.ini
	TArray<FString> PluginTagsConfig;
	if (!ReadPluginConfigFile(PluginName, TEXT("DefaultGameplayTags.ini"), PluginTagsConfig))
	{
		UE_LOG(LogTemp, Warning, TEXT("No DefaultGameplayTags.ini found in plugin '%s', skipping gameplay tag settings"), *PluginName);
		return false;
	}

	// Extract gameplay tag sections
	TMap<FString, TArray<FString>> TagSections;
	FString CurrentSection;

	for (const FString& Line : PluginTagsConfig)
	{
		FString TrimmedLine = Line.TrimStartAndEnd();

		// Check if this is a section header
		if (TrimmedLine.StartsWith(TEXT("[")) && TrimmedLine.EndsWith(TEXT("]")))
		{
			// Extract section name (remove brackets)
			CurrentSection = TrimmedLine.Mid(1, TrimmedLine.Len() - 2);
			TagSections.Add(CurrentSection, TArray<FString>());
		}
		else if (!CurrentSection.IsEmpty())
		{
			// Add line to current section
			TagSections[CurrentSection].Add(Line);
		}
	}

	// Get project's DefaultGameplayTags.ini path
	FString ProjectTagsPath = FPaths::Combine(GetProjectConfigDirectory(), TEXT("DefaultGameplayTags.ini"));

	// Merge all tag sections
	bool bSuccess = true;
	for (const auto& Section : TagSections)
	{
		if (Section.Value.Num() > 0)
		{
			bSuccess &= MergeConfigSection(ProjectTagsPath, Section.Key, Section.Value, true);
		}
	}

	if (bSuccess)
	{
		UE_LOG(LogTemp, Log, TEXT("Successfully added gameplay tag settings to project from plugin '%s'"), *PluginName);
	}
	else
	{
		UE_LOG(LogTemp, Warning, TEXT("Partially failed to add gameplay tag settings to project from plugin '%s'"), *PluginName);
	}

	return bSuccess;
}

bool UACFEditorFunctionLibrary::AddGameUserSettingsToProject(const FString& PluginName)
{
	// Read game user settings from plugin's DefaultGameUserSettings.ini
	TArray<FString> PluginUserSettingsConfig;
	if (!ReadPluginConfigFile(PluginName, TEXT("DefaultGameUserSettings.ini"), PluginUserSettingsConfig))
	{
		UE_LOG(LogTemp, Warning, TEXT("No DefaultGameUserSettings.ini found in plugin '%s', skipping game user settings"), *PluginName);
		return false;
	}

	// Extract ACF-specific settings sections
	TMap<FString, TArray<FString>> UserSettingsSections;
	FString CurrentSection;

	for (const FString& Line : PluginUserSettingsConfig)
	{
		FString TrimmedLine = Line.TrimStartAndEnd();

		// Check if this is a section header
		if (TrimmedLine.StartsWith(TEXT("[")) && TrimmedLine.EndsWith(TEXT("]")))
		{
			// Extract section name (remove brackets)
			CurrentSection = TrimmedLine.Mid(1, TrimmedLine.Len() - 2);
			UserSettingsSections.Add(CurrentSection, TArray<FString>());
		}
		else if (!CurrentSection.IsEmpty())
		{
			// Add line to current section
			UserSettingsSections[CurrentSection].Add(Line);
		}
	}

	// Get project's DefaultGameUserSettings.ini path
	FString ProjectUserSettingsPath = FPaths::Combine(GetProjectConfigDirectory(), TEXT("DefaultGameUserSettings.ini"));

	// Merge all user settings sections
	bool bSuccess = true;
	for (const auto& Section : UserSettingsSections)
	{
		if (Section.Value.Num() > 0)
		{
			bSuccess &= MergeConfigSection(ProjectUserSettingsPath, Section.Key, Section.Value, true);
		}
	}

	if (bSuccess)
	{
		UE_LOG(LogTemp, Log, TEXT("Successfully added game user settings to project from plugin '%s'"), *PluginName);
	}
	else
	{
		UE_LOG(LogTemp, Warning, TEXT("Partially failed to add game user settings to project from plugin '%s'"), *PluginName);
	}

	return bSuccess;
}

bool UACFEditorFunctionLibrary::AddEngineClassSettingsToProject(const FString& PluginName)
{
	TArray<FString> PluginEngineConfig;
	if (!ReadPluginConfigFile(PluginName, TEXT("DefaultEngine.ini"), PluginEngineConfig))
	{
		UE_LOG(LogTemp, Warning, TEXT("No DefaultEngine.ini found in plugin '%s', skipping engine class settings"), *PluginName);
		return false;
	}

	TArray<FString> EngineClassLines;
	bool bInEngineSection = false;

	for (const FString& Line : PluginEngineConfig)
	{
		FString TrimmedLine = Line.TrimStartAndEnd();

		if (TrimmedLine.Equals(TEXT("[/Script/Engine.Engine]"), ESearchCase::IgnoreCase))
		{
			bInEngineSection = true;
			continue;
		}
		else if (TrimmedLine.StartsWith(TEXT("[")))
		{
			bInEngineSection = false;
			continue;
		}

		if (bInEngineSection)
		{
			if (TrimmedLine.StartsWith(TEXT("GameUserSettingsClassName=")) ||
				TrimmedLine.StartsWith(TEXT("GameViewportClientClassName=")))
			{
				EngineClassLines.Add(Line);
			}
		}
	}

	if (EngineClassLines.Num() == 0)
	{
		UE_LOG(LogTemp, Warning, TEXT("No engine class settings found in plugin '%s'"), *PluginName);
		return false;
	}

	FString ProjectEnginePath = FPaths::Combine(GetProjectConfigDirectory(), TEXT("DefaultEngine.ini"));
	bool bSuccess = ReplaceConfigSectionInFile(ProjectEnginePath, TEXT("/Script/Engine.Engine"), EngineClassLines);

	if (bSuccess)
	{
		UE_LOG(LogTemp, Log, TEXT("Successfully added engine class settings to project from plugin '%s'"), *PluginName);
	}
	else
	{
		UE_LOG(LogTemp, Warning, TEXT("Failed to add engine class settings to project from plugin '%s'"), *PluginName);
	}

	return bSuccess;
}

FString UACFEditorFunctionLibrary::GetFullSampleSplashDirectory()
{
	return FPaths::Combine(FPaths::ProjectContentDir(), TEXT("FullSample"), TEXT("Splash"));
}

FString UACFEditorFunctionLibrary::GetPluginName()
{
	return FAscentEditorModule::GetPluginName();
}

FString UACFEditorFunctionLibrary::GetPluginNameForModule(const FString& ModuleName)
{
	return FAscentEditorModule::GetPluginNameForModule(ModuleName);
}

FString UACFEditorFunctionLibrary::GetPluginFriendlyName()
{
	return FAscentEditorModule::GetPluginFriendlyName();
}

bool UACFEditorFunctionLibrary::AddFullSampleEditorSplashToProject()
{
	const FString SourceDir = GetFullSampleSplashDirectory();
	const FString DestDir = FPaths::Combine(FPaths::ProjectContentDir(), TEXT("Splash"));

	if (!FPaths::DirectoryExists(SourceDir))
	{
		UE_LOG(LogTemp, Log, TEXT("FullSample/Splash not found at '%s', skipping editor splash setup."), *SourceDir);
		return true; // Optional step – not an error
	}

	IFileManager& FileManager = IFileManager::Get();

	// Supported editor splash formats (Unreal looks for e.g. EdSplash*.png in Content/Splash)
	TArray<FString> Extensions = { TEXT("*.png"), TEXT("*.jpg"), TEXT("*.jpeg"), TEXT("*.bmp") };
	int32 CopiedCount = 0;

	for (const FString& Ext : Extensions)
	{
		TArray<FString> Files;
		FileManager.FindFiles(Files, *FPaths::Combine(SourceDir, Ext), true, false);

		for (const FString& FileName : Files)
		{
			const FString SrcPath = FPaths::Combine(SourceDir, FileName);
			const FString DstPath = FPaths::Combine(DestDir, FileName);

			if (!FileManager.DirectoryExists(*DestDir))
			{
				if (!FileManager.MakeDirectory(*DestDir, true))
				{
					UE_LOG(LogTemp, Error, TEXT("Failed to create directory: %s"), *DestDir);
					return false;
				}
			}

			if (FileManager.Copy(*DstPath, *SrcPath, true, true))
			{
				CopiedCount++;
				UE_LOG(LogTemp, Log, TEXT("Copied editor splash: %s -> %s"), *FileName, *DestDir);
			}
			else
			{
				UE_LOG(LogTemp, Error, TEXT("Failed to copy %s to %s"), *SrcPath, *DstPath);
				return false;
			}
		}
	}

	if (CopiedCount > 0)
	{
		UE_LOG(LogTemp, Log, TEXT("✓ Editor splash: copied %d file(s) from FullSample/Splash to Content/Splash"), CopiedCount);
	}
	else
	{
		UE_LOG(LogTemp, Warning, TEXT("FullSample/Splash is empty (no .png/.jpg/.bmp). No editor splash files copied."));
	}

	return true;
}

bool UACFEditorFunctionLibrary::SetupACFProjectConfiguration(const FString& PluginName)
{
	UE_LOG(LogTemp, Log, TEXT("========================================"));
	UE_LOG(LogTemp, Log, TEXT("Starting ACF Project Configuration Setup"));
	UE_LOG(LogTemp, Log, TEXT("Plugin: %s"), *PluginName);
	UE_LOG(LogTemp, Log, TEXT("========================================"));

	bool bSuccess = true;
	int32 SuccessCount = 0;
	int32 TotalSteps = 5;

	// Step 1: Copy plugin config files (gameplay-only, no rendering/quality settings)
	UE_LOG(LogTemp, Log, TEXT("[1/%d] Copying plugin config files..."), TotalSteps);
	const TArray<FString> FilesToCopy = { TEXT("DefaultPlugins.ini"), TEXT("DefaultGameplayTags.ini"), TEXT("DefaultInput.ini") };
	if (CopyPluginConfigToProject(FilesToCopy, PluginName))
	{
		SuccessCount++;
		UE_LOG(LogTemp, Log, TEXT("✓ Plugin config files copied successfully"));
	}
	else
	{
		bSuccess = false;
		UE_LOG(LogTemp, Error, TEXT("✗ Failed to copy plugin config files"));
	}

	// Step 2: Add collision settings
	UE_LOG(LogTemp, Log, TEXT("[2/%d] Adding collision settings..."), TotalSteps);
	if (AddCollisionSettingsToProject(PluginName))
	{
		SuccessCount++;
		UE_LOG(LogTemp, Log, TEXT("✓ Collision settings added successfully"));
	}
	else
	{
		bSuccess = false;
		UE_LOG(LogTemp, Error, TEXT("✗ Failed to add collision settings"));
	}

	// Step 3: Add gameplay tag settings
	UE_LOG(LogTemp, Log, TEXT("[3/%d] Adding gameplay tag settings..."), TotalSteps);
	if (AddGameplayTagSettingsToProject(PluginName))
	{
		SuccessCount++;
		UE_LOG(LogTemp, Log, TEXT("✓ Gameplay tag settings added successfully"));
	}
	else
	{
		bSuccess = false;
		UE_LOG(LogTemp, Error, TEXT("✗ Failed to add gameplay tag settings"));
	}

	// Step 4: Add mandatory engine class overrides (GameUserSettingsClassName, GameViewportClientClassName)
	UE_LOG(LogTemp, Log, TEXT("[4/%d] Adding engine class settings..."), TotalSteps);
	if (AddEngineClassSettingsToProject(PluginName))
	{
		SuccessCount++;
		UE_LOG(LogTemp, Log, TEXT("✓ Engine class settings added successfully"));
	}
	else
	{
		bSuccess = false;
		UE_LOG(LogTemp, Error, TEXT("✗ Failed to add engine class settings"));
	}

	// Step 5: Copy editor splash from FullSample/Splash to Content/Splash (optional – skipped if FullSample/Splash not found)
	UE_LOG(LogTemp, Log, TEXT("[5/%d] Applying FullSample editor splash (FullSample/Splash -> Content/Splash)..."), TotalSteps);
	if (AddFullSampleEditorSplashToProject())
	{
		SuccessCount++;
		UE_LOG(LogTemp, Log, TEXT("✓ Editor splash applied"));
	}
	else
	{
		bSuccess = false;
		UE_LOG(LogTemp, Error, TEXT("✗ Failed to apply editor splash"));
	}

	// Summary
	UE_LOG(LogTemp, Log, TEXT("========================================"));
	UE_LOG(LogTemp, Log, TEXT("ACF Project Configuration Complete"));
	UE_LOG(LogTemp, Log, TEXT("Success: %d/%d steps"), SuccessCount, TotalSteps);

	if (bSuccess)
	{
		UE_LOG(LogTemp, Log, TEXT("Status: ✓ ALL CONFIGURATIONS APPLIED"));
		UE_LOG(LogTemp, Log, TEXT("NOTE: You may need to restart the editor for all changes to take effect."));
	}
	else
	{
		UE_LOG(LogTemp, Warning, TEXT("Status: ⚠ PARTIAL CONFIGURATION"));
		UE_LOG(LogTemp, Warning, TEXT("Some configurations failed. Check the log above for details."));
	}

	UE_LOG(LogTemp, Log, TEXT("========================================"));

	return bSuccess;
}