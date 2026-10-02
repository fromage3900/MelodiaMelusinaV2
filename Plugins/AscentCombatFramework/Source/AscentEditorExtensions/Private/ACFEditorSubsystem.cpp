// Copyright (C) Developed by Pask & OlssonDev, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ACFEditorSubsystem.h"
#include "ACFAssetAction.h"
#include "ACFAssetCreatorDataAsset.h"
#include "ACFEditorSettings.h"
#include "ACFEditorTypes.h"
#include "ACFPlacementDataAsset.h"
#include "AscentEditorExtensions.h"
#include "Actors/ACFCharacter.h"
#include "ACFAITypes.h"
#include "Data/ACFCharacterDataAsset.h"
#include "Components/ACFAbilitySystemComponent.h"
#include "Components/ACFTeamComponent.h"
#include "Components/ACFEquipmentComponent.h"
#include "Components/ACFEffectsManagerComponent.h"
#include "Components/ACFCombatBehaviourComponent.h"
#include "ACFGASAttributesComponent.h"
#include "ACFAIController.h"
#include "Components/SkeletalMeshComponent.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "AssetTools/FAssetTypeActions_AssetCreatorBase.h"
#include "Factory/ACFActorFactory.h"
#include "Factory/ACFBaseFactory.h"
#include "Framework/Notifications/NotificationManager.h"
#include "KismetCompilerModule.h"
#include "Runtime/Launch/Resources/Version.h"
#include "Widgets/Notifications/SNotificationList.h"
#include <AssetTypeActions/AssetTypeActions_DataAsset.h>
#include "Misc/ConfigCacheIni.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Interfaces/IPluginManager.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "AssetRegistry/AssetData.h"
#include "ACFEditorStyle.h"
#include "UObject/FindObjectFlags.h"

#define LOCTEXT_NAMESPACE "UAssetCreatorSubsystem"

void UACFEditorSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
	// Apply variant-specific config overrides before anything else loads
	ApplyVariantConfig();

	// Listen to when an asset has been deleted. So we can refresh the plugin in case the asset was a class of the plugin's API.
	FEditorDelegates::OnAssetsDeleted.AddUObject(this, &ThisClass::OnAssetsDeleted);

	// Listen to when an object has been modified. So we can refresh the categories.
	FCoreUObjectDelegates::OnObjectPropertyChanged.AddUObject(this, &ThisClass::OnAssetCreatorChanged);

	// We don't want to listen for new Assets before the editor is not opened.
	OnMapOpenedDelegate = FEditorDelegates::OnMapOpened.AddUObject(this, &ThisClass::OnEditorOpened);

	FAssetRegistryModule& AssetRegistryModule = FModuleManager::LoadModuleChecked<FAssetRegistryModule>("AssetRegistry");
	AssetRenamedHandle = AssetRegistryModule.Get().OnAssetRenamed().AddUObject(this, &ThisClass::OnAssetRenamed);

	Super::Initialize(Collection);
}

void UACFEditorSubsystem::Deinitialize()
{
	if (FModuleManager::Get().IsModuleLoaded("AssetRegistry"))
	{
		FAssetRegistryModule* AssetRegistryModule = FModuleManager::GetModulePtr<FAssetRegistryModule>("AssetRegistry");
		if (AssetRegistryModule && AssetRenamedHandle.IsValid())
		{
			AssetRegistryModule->Get().OnAssetRenamed().Remove(AssetRenamedHandle);
		}
	}
	Super::Deinitialize();
}

void UACFEditorSubsystem::ApplyVariantConfig()
{
	TSharedPtr<IPlugin> Plugin = IPluginManager::Get().FindPlugin(PluginName);
	if (!Plugin.IsValid())
	{
		return;
	}

	// Parse raw .uplugin JSON to read the custom "ACFVariant" field written by ACFPackager
	FString JsonContent;
	if (!FFileHelper::LoadFileToString(JsonContent, *Plugin->GetDescriptorFileName()))
	{
		return;
	}

	TSharedPtr<FJsonObject> JsonObj;
	TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(JsonContent);
	if (!FJsonSerializer::Deserialize(Reader, JsonObj) || !JsonObj.IsValid())
	{
		return;
	}

	FString VariantName;
	if (!JsonObj->TryGetStringField(TEXT("ACFVariant"), VariantName) || VariantName.IsEmpty())
	{
		// No variant field: full source build or non-packaged install — nothing to apply
		return;
	}

	const FString ConfigDir = FPaths::Combine(Plugin->GetBaseDir(), TEXT("Config"));
	const FString VariantDir = FPaths::Combine(ConfigDir, VariantName);

	if (!IFileManager::Get().DirectoryExists(*VariantDir))
	{
		UE_LOG(LogTemp, Warning, TEXT("ACF: Variant config folder not found: %s"), *VariantDir);
		return;
	}

	TArray<FString> VariantIniFiles;
	IFileManager::Get().FindFiles(VariantIniFiles, *FPaths::Combine(VariantDir, TEXT("*.ini")), true, false);

	for (const FString& IniFileName : VariantIniFiles)
	{
		const FString VariantFilePath = FPaths::Combine(VariantDir, IniFileName);
		const FString DestFilePath    = FPaths::Combine(ConfigDir, IniFileName);

		// Read the variant .ini and merge every key into GConfig under the flat config path
		FConfigFile VariantConfig;
		VariantConfig.Read(VariantFilePath);

		for (const auto& SectionPair : VariantConfig)
		{
			for (const auto& KVP : SectionPair.Value)
			{
				GConfig->SetString(*SectionPair.Key, *KVP.Key.ToString(), *KVP.Value.GetSavedValue(), DestFilePath);
			}
		}

		UE_LOG(LogTemp, Log, TEXT("ACF: Applied variant config [%s] -> %s"), *VariantName, *IniFileName);
	}
}

void UACFEditorSubsystem::OnEditorOpened(const FString& FileName, bool bAsTemplate)
{
	FEditorDelegates::OnMapOpened.Remove(OnMapOpenedDelegate);
	IAssetRegistry* AssetRegistry = &FModuleManager::LoadModuleChecked<FAssetRegistryModule>(AssetRegistryConstants::ModuleName).Get();

	// Listen to when an asset has been added so we can keep those in memory if they're an UACFAssetAction or UACFBaseFactory.
	AssetRegistry->OnAssetAdded().AddUObject(this, &ThisClass::OnAssetCreated);

	// When we start the editor, just refresh the whole plugin.
	RefreshAll();
}

void UACFEditorSubsystem::OnAssetCreated(const FAssetData& AssetData)
{
	UClass* AssetAction = nullptr;
	if (GetClassFromBlueprint(AssetData, UACFAssetAction::StaticClass(), AssetAction)) {
		AssetActions.AddUnique(AssetAction);
		return;
	}

	UClass* Factory = nullptr;
	if (GetClassFromBlueprint(AssetData, UACFBaseFactory::StaticClass(), Factory)) {
		Factories.AddUnique(Factory);
		return;
	}
}

void UACFEditorSubsystem::OnAssetsDeleted(const TArray<UClass*>& AssetsToDelete)
{
	// Just refresh everything when an asset has been deleted.
	RefreshAll();
}

UACFAssetAction* UACFEditorSubsystem::GetAssetAction(UClass* AssetActionClass)
{
	if (AssetActionClass && AssetActionClass->IsChildOf(UACFAssetAction::StaticClass())) {
		UACFAssetAction* AssetAction = CastChecked<UACFAssetAction>(AssetActionClass->GetDefaultObject());
		return AssetAction->AssetActionSettings.IsValid() ? AssetAction : nullptr;
	}
	return nullptr;
}

bool UACFEditorSubsystem::GetClassFromBlueprint(const FAssetData AssetData, UClass* ClassToFind, UClass*& GeneratedClass)
{
	if (AssetData.IsValid() && ClassToFind) {
		FAssetDataTagMapSharedView::FFindTagResult Result = AssetData.TagsAndValues.FindTag(TEXT("NativeParentClass"));
		if (Result.IsSet()) {
			const FString ClassObjectPath = FPackageName::ExportTextPathToObjectPath(Result.GetValue());
			if (UClass* ParentClass = FindObjectSafe<UClass>(nullptr, *ClassObjectPath, EFindObjectFlags::ExactClass)) {
				if (ParentClass->IsChildOf(ClassToFind)) {
					// TODO: Loading these assets could cause problems on projects with a large number of them.
					UBlueprint* BP = CastChecked<UBlueprint>(AssetData.GetAsset());
					// Can be not valid if a class has just recently been deleted.
					if (IsValid(BP->GeneratedClass)) {
						GeneratedClass = BP->GeneratedClass;
						return true;
					}
				}
			}
		}
	}

	return false;
}

void UACFEditorSubsystem::RefreshPlacementMode()
{
	if (GEditor) {
		IPlacementModeModule& PlacementModeModule = IPlacementModeModule::Get();

		for (auto RegisteredPlaceableItem : RegisteredPlaceableItems) {
			PlacementModeModule.UnregisterPlaceableItem(*RegisteredPlaceableItem);
		}
		RegisteredPlaceableItems.Empty();

		for (FPlacementCategoryInfo CategoryInfo : RegisteredPlaceableItemCategories) {
			PlacementModeModule.UnregisterPlacementCategory(CategoryInfo.UniqueHandle);
		}
		RegisteredPlaceableItemCategories.Empty();

		for (UActorFactory* ActorFactory : ActorFactories) {
			GEditor->ActorFactories.Remove(ActorFactory);
		}
		ActorFactories.Empty();

		const UACFEditorSettings* settings = GetEditorSettings();

		if (!settings) {
			return;
		}

		const TArray<FPlaceCategoryConfig> AllCategories = settings->GetPlacementCategories();

		for (const FPlaceCategoryConfig& category : AllCategories)
		{
			const FName CategoryName = category.CategoryName;
			FPlacementCategoryInfo PlacementCategoryInfo = FPlacementCategoryInfo(
				FText::FromName(CategoryName),
				CategoryName, "PM" + CategoryName.ToString(),
				category.SortOrder);

			FSlateIcon NewIcon(settings->GetStyleName(), category.IconName);
			PlacementCategoryInfo.DisplayIcon = NewIcon;
			PlacementModeModule.RegisterPlacementCategory(PlacementCategoryInfo);
			RegisteredPlaceableItemCategories.Add(PlacementCategoryInfo);

			for (const FAssetActionConfig& placeable : category.Entries)
			{
				const TSubclassOf<AActor> placeClass = placeable.AssetClass.LoadSynchronous();
				if (placeClass)
				{
					FPlaceableItem NewPlaceableItem;
					NewPlaceableItem.Factory = MakeActorFactoryFromClass(placeClass);
					NewPlaceableItem.AssetData = placeClass.Get();
					NewPlaceableItem.bAlwaysUseGenericThumbnail = true;
					NewPlaceableItem.AssetTypeColorOverride = placeable.AssetColor;
					NewPlaceableItem.DisplayName = placeable.ClassNameOverride.IsEmpty() ? placeable.AssetClass->GetDisplayNameText() : placeable.ClassNameOverride;
					RegisteredPlaceableItems.Add(PlacementModeModule.RegisterPlaceableItem(PlacementCategoryInfo.UniqueHandle, MakeShared<FPlaceableItem>(NewPlaceableItem)));
				}
			}
		}


		PlacementModeModule.RegenerateItemsForCategory(FBuiltInPlacementCategories::AllClasses());
	}
}

void UACFEditorSubsystem::RefreshActions()
{
	RefreshPlacementMode();
	RefreshAssetTypeActions();
}

void UACFEditorSubsystem::RefreshAll()
{
	AssetActions = GatherAllAssetsOfClass(UACFAssetAction::StaticClass());
	Factories = GatherAllAssetsOfClass(UACFBaseFactory::StaticClass());

	RefreshActions();
}

void UACFEditorSubsystem::RefreshAssetTypeActions()
{
	IAssetTools& AssetTools = FModuleManager::LoadModuleChecked<FAssetToolsModule>("AssetTools").Get();

	// Unregister all of the AssetTypeActions first before we register new ones.
	for (int32 i = AssetTypeActions.Num(); i--;) {
		UnregisterAssetTypeAction(AssetTools, AssetTypeActions[i]);
	}

	AssetActionsInst.Empty();
	/*
   const UACFEditorSettings* settings = GetEditorSettings();

   const TArray<FMainCategoryConfig> contentConfig = settings->GetContentBrowserConfig();

   for (const auto& mainCat : contentConfig) {
	   uint32 Category = AssetTools.RegisterAdvancedAssetCategory(mainCat.MainCategoryName,
		   FText::Format(LOCTEXT("AssetCreatorCategory", "{0}"),
			   FText::FromName(mainCat.MainCategoryName)));
	   for (const FAssetActionConfig& entry : mainCat.Entries) {
		   if (IsValid(entry.AssetClass.Get())) {

			   FAssetActionSettings newSettings(entry, mainCat.MainCategoryName, false, FText::FromString(""));
			   UACFAssetAction* newAction = MakeActorAction(newSettings);
			   UACFBaseFactory* factory = MakeFactory(newAction);

			   RegisterAssetTypeAction(AssetTools, MakeShareable(new FAssetTypeActions_AssetCreatorBase(newSettings, Category)));
		   }
	   }
	   for (const auto& subCat : mainCat.SubCategories) {
		   for (const FAssetActionConfig& entry : subCat.Entries) {
			   if (IsValid(entry.AssetClass.Get())) {
				   FAssetActionSettings newSettings(entry, mainCat.MainCategoryName, true, FText::FromName(subCat.CategoryName));
				   UACFAssetAction* newAction = MakeActorAction(newSettings);
				   UACFBaseFactory* factory = MakeFactory(newAction);

				   RegisterAssetTypeAction(AssetTools, MakeShareable(new FAssetTypeActions_AssetCreatorBase(newSettings, Category)));
			   }
		   }
	   }
   }

   for (UClass* Class : AssetActions) {
	   if (UACFAssetAction* AssetAction = GetAssetAction(Class)) {
		   AssetActionsInst.AddUnique(AssetAction);
	   }
   }

   for (auto AssetAction : AssetActionsInst) {
	   if (AssetAction) {
		   uint32 Category = AssetTools.RegisterAdvancedAssetCategory(AssetAction->AssetActionSettings.CategoryName,
			   FText::Format(LOCTEXT("AssetCreatorCategory", "{0}"),
				   FText::FromName(AssetAction->AssetActionSettings.CategoryName)));

		   RegisterAssetTypeAction(AssetTools, MakeShareable(new FAssetTypeActions_AssetCreatorBase(AssetAction->AssetActionSettings, Category)));
	   }
   }
   */
   // Register all the valid AssetActions.
	for (UClass* Class : AssetActions) {
		if (UACFAssetAction* AssetAction = GetAssetAction(Class)) {
			uint32 Category = AssetTools.RegisterAdvancedAssetCategory(AssetAction->AssetActionSettings.CategoryName,
				FText::Format(LOCTEXT("AssetCreatorCategory", "{0}"),
					FText::FromName(AssetAction->AssetActionSettings.CategoryName)));

			if (AssetAction->AssetActionSettings.AssetClass->IsChildOf(UDataAsset::StaticClass())) {
				// Use data asset factory logic
				TSharedRef<FAssetTypeActions_ACFDataAsset> Action = MakeShareable(new FAssetTypeActions_ACFDataAsset(AssetAction->AssetActionSettings.AssetClass, AssetAction->AssetActionSettings, Category));
				RegisterAssetTypeAction(AssetTools, Action);
			}
			else {
				// Use blueprint factory logic
				RegisterAssetTypeAction(AssetTools, MakeShareable(new FAssetTypeActions_AssetCreatorBase(AssetAction->AssetActionSettings, Category)));
			}
		}
	}
}

void UACFEditorSubsystem::OnAssetCreatorChanged(UObject* Object, FPropertyChangedEvent& ChangedEvent)
{
	// Refresh when any of our settings or data-asset overrides are modified.
	UClass* Class = Object->GetClass();
	if (Class->IsChildOf(UACFAssetAction::StaticClass())
		|| Class->IsChildOf(UACFBaseFactory::StaticClass())
		|| Class == UACFEditorSettings::StaticClass()
		|| Class->IsChildOf(UACFPlacementDataAsset::StaticClass())
		|| Class->IsChildOf(UACFAssetCreatorDataAsset::StaticClass()))
	{
		RefreshActions();
	}
}

void UACFEditorSubsystem::RegisterAssetTypeAction(IAssetTools& AssetTools, TSharedRef<IAssetTypeActions> Action)
{
	AssetTools.RegisterAssetTypeActions(Action);
	AssetTypeActions.Add(Action);
}

void UACFEditorSubsystem::UnregisterAssetTypeAction(IAssetTools& AssetTools, TSharedRef<IAssetTypeActions> Action)
{
	AssetTools.UnregisterAssetTypeActions(Action);
	AssetTypeActions.Remove(Action);
}

bool UACFEditorSubsystem::HasFactory(UClass* Class)
{
	if (Class) {
		UClass* BlueprintClass = nullptr;
		UClass* BlueprintGeneratedClass = nullptr;

		IKismetCompilerInterface& KismetCompilerModule = FModuleManager::LoadModuleChecked<IKismetCompilerInterface>("KismetCompiler");
		KismetCompilerModule.GetBlueprintTypesForClass(Class, BlueprintClass, BlueprintGeneratedClass);

		if (const UBlueprint* Blueprint = Cast<UBlueprint>(GetDefault<UObject>(BlueprintClass))) {
			if (!Blueprint->SupportedByDefaultBlueprintFactory()) {
				FNotificationInfo Info(NSLOCTEXT("AssetCreatorEditor", "FAscentEditorExtensions", "Selected class can't be used. The class doesn't support to be created in a default Blueprint Factory."));
				Info.ExpireDuration = 4.0f;
				FSlateNotificationManager::Get().AddNotification(Info);
				return true;
			}
		}
	}

	return false;
}

UACFActorFactory* UACFEditorSubsystem::MakeActorFactory(UACFAssetAction* AssetAction)
{
	UACFActorFactory* NewFactory = nullptr;
	if (IsValid(AssetAction)) {
		NewFactory = NewObject<UACFActorFactory>(GetTransientPackage(), UACFActorFactory::StaticClass());
		NewFactory->AssetAction = AssetAction;
		NewFactory->NewActorClass = AssetAction->AssetActionSettings.AssetClass.Get();
		ActorFactories.Add(NewFactory);
	}
	return NewFactory;
}

UACFBaseFactory* UACFEditorSubsystem::MakeFactory(UACFAssetAction* AssetAction)
{
	UACFBaseFactory* NewFactory = nullptr;
	if (IsValid(AssetAction)) {
		NewFactory = NewObject<UACFBaseFactory>(GetTransientPackage(), UACFBaseFactory::StaticClass());
		NewFactory->ParentClass = AssetAction->AssetActionSettings.AssetClass;
		NewFactory->UseClassPicker = true;
		NewFactory->DefaultAssetName = "NewAsset";
		BaseFactories.Add(NewFactory);
	}
	return NewFactory;
}

UACFAssetAction* UACFEditorSubsystem::MakeActorAction(const FAssetActionSettings& assetSetting)
{
	UACFAssetAction* NewAction = nullptr;
	if (IsValid(assetSetting.AssetClass.Get())) {
		NewAction = NewObject<UACFAssetAction>(GetTransientPackage(), UACFAssetAction::StaticClass());
		NewAction->AssetActionSettings = assetSetting;
		AssetActionsInst.Add(NewAction);
	}
	return NewAction;
}

UACFActorFactory* UACFEditorSubsystem::MakeActorFactoryFromClass(TSubclassOf<AActor> AssetClass)
{
	UACFActorFactory* NewFactory = nullptr;
	if (IsValid(AssetClass)) {
		NewFactory = NewObject<UACFActorFactory>(GetTransientPackage(), UACFActorFactory::StaticClass());
		/*  NewFactory->AssetAction = AssetAction;*/
		NewFactory->NewActorClass = AssetClass.Get();
		ActorFactories.Add(NewFactory);
	}
	return NewFactory;
}

UACFEditorSettings* UACFEditorSubsystem::GetEditorSettings() const
{
	return GetMutableDefault<UACFEditorSettings>();
}



TArray<UClass*> UACFEditorSubsystem::GatherAllAssetsOfClass(UClass* Class)
{
	TArray<UClass*> Classes;

	// Search native classes
	for (TObjectIterator<UClass> ClassIt; ClassIt; ++ClassIt) {
		if (!ClassIt->IsNative() || !ClassIt->IsChildOf(Class)) {
			continue;
		}

		// Ignore classes that are Abstract, HideDropdown, and Deprecated.
		if (ClassIt->HasAnyClassFlags(CLASS_Abstract | CLASS_HideDropDown | CLASS_Deprecated | CLASS_NewerVersionExists)) {
			continue;
		}

		Classes.AddUnique(*ClassIt);
	}

	// Search Blueprint classes.
	{
		FAssetRegistryModule& AssetRegistryModule = FModuleManager::LoadModuleChecked<FAssetRegistryModule>(TEXT("AssetRegistry"));
		IAssetRegistry& AssetRegistry = AssetRegistryModule.Get();

		TArray<FString> ContentPaths;
		ContentPaths.Add(TEXT("/Game"));
		AssetRegistry.ScanPathsSynchronous(ContentPaths);

		FARFilter Filter;
#if ENGINE_MAJOR_VERSION == 5 && ENGINE_MINOR_VERSION >= 1
		Filter.ClassPaths.Add(UBlueprint::StaticClass()->GetClassPathName());
#else
		Filter.ClassNames.Add(UBlueprint::StaticClass()->GetFName());
#endif
		Filter.bRecursiveClasses = true;
		Filter.bRecursivePaths = true;

		TArray<FAssetData> AssetList;
		AssetRegistry.GetAssets(Filter, AssetList);

		for (FAssetData& Asset : AssetList) {
			UClass* GeneratedClass = nullptr;
			;
			if (GetClassFromBlueprint(Asset, Class, GeneratedClass)) {
				Classes.AddUnique(GeneratedClass);
			}
		}
	}

	return Classes;
}

bool UACFEditorSubsystem::FillCharacterDataFromCharacter(AACFCharacter* Character, UACFCharacterDataAsset* OutDataAsset)
{
	if (!Character || !OutDataAsset)
	{
		return false;
	}

	// Basic info
	OutDataAsset->ChatacterName = Character->GetCharacterName();
	OutDataAsset->CharacterPortrait = Character->GetCharacterPortrait();

	// Team
	if (UACFTeamComponent* TeamComp = Character->FindComponentByClass<UACFTeamComponent>())
	{
		OutDataAsset->Team = TeamComp->GetTeam();
	}

	// Attributes / Leveling
	if (UACFGASAttributesComponent* AttrComp = Character->FindComponentByClass<UACFGASAttributesComponent>())
	{
		OutDataAsset->LevelingType = AttrComp->GetLevelingType();
		OutDataAsset->CharacterRow = AttrComp->GetCharacterRow();
		OutDataAsset->AttributesByLevelCurve = AttrComp->GetAttributesByLevelCurve();
		OutDataAsset->bAffectedByDifficultyLevel = AttrComp->IsAffectedByDifficultyLevel();
		OutDataAsset->ExpForNextLevelCurve = AttrComp->GetExpForNextLevelCurve();
		OutDataAsset->ExpToGiveOnDeath = AttrComp->GetExpToGiveOnDeath();
		OutDataAsset->ExpToGiveOnDeathByCurrentLevel = AttrComp->GetExpToGiveOnDeathByCurrentLevel();
	}

	// Abilities
	if (UACFAbilitySystemComponent* AbilityComp = Character->FindComponentByClass<UACFAbilitySystemComponent>())
	{
		OutDataAsset->DefaultAbilitySet = AbilityComp->GetDefaultAbilitySet();
		OutDataAsset->MovesetAbilities = AbilityComp->GetMovesetAbilities();
	}

	// Equipment / Inventory
	if (UACFEquipmentComponent* EquipComp = Character->FindComponentByClass<UACFEquipmentComponent>())
	{
		OutDataAsset->StartingItems = EquipComp->GetStartingItems();
		OutDataAsset->Currency = EquipComp->GetCurrentCurrencyAmount();
	}

	// Effects config (for ACFEffectsManagerComponent)
	if (UACFEffectsManagerComponent* EffectsComp = Character->FindComponentByClass<UACFEffectsManagerComponent>())
	{
		OutDataAsset->CharacterEffectsConfig = EffectsComp->GetCharacterEffectsConfig();
	}

	// Meshes - extract from skeletal mesh components
	TArray<USkeletalMeshComponent*> SkeletalComponents;
	Character->GetComponents<USkeletalMeshComponent>(SkeletalComponents);

	const UACFEquipmentComponent* EquipCompForMain = Character->FindComponentByClass<UACFEquipmentComponent>();
	OutDataAsset->MeshComponents.Empty();
	for (USkeletalMeshComponent* SkelComp : SkeletalComponents)
	{
		if (!SkelComp || !SkelComp->GetSkeletalMeshAsset())
		{
			continue;
		}

		FSkeletalMeshComponentData MeshData;
		MeshData.SkeletalMesh = SkelComp->GetSkeletalMeshAsset();
		MeshData.AnimInstance = SkelComp->GetAnimClass();

		// Component tag: main mesh uses NAME_None
		if (EquipCompForMain && SkelComp == EquipCompForMain->GetMainMesh())
		{
			MeshData.ComponentTag = NAME_None;
		}
		else if (SkelComp->ComponentTags.Num() > 0)
		{
			MeshData.ComponentTag = SkelComp->ComponentTags[0];
		}
		else
		{
			MeshData.ComponentTag = NAME_None;
		}

		// Material overrides
		const int32 NumMaterials = SkelComp->GetNumMaterials();
		MeshData.MaterialOverrides.SetNum(NumMaterials);
		for (int32 i = 0; i < NumMaterials; i++)
		{
			UMaterialInterface* Mat = SkelComp->GetMaterial(i);
			if (Mat)
			{
				MeshData.MaterialOverrides[i].Material = Mat;
				if (MeshData.SkeletalMesh && MeshData.SkeletalMesh->GetMaterials().IsValidIndex(i))
				{
					MeshData.MaterialOverrides[i].SlotName = MeshData.SkeletalMesh->GetMaterials()[i].MaterialSlotName;
				}
			}
		}

		OutDataAsset->MeshComponents.Add(MeshData);
	}

	return true;
}

namespace
{
	static const FString CoreRedirectsSection(TEXT("[CoreRedirects]"));
	static const TArray<FString> ACFRedirectConfigFileNames = {
		TEXT("DefaultAscentCombatFramework.ini"),
		TEXT("BaseAscentCombatFramework.ini")
	};

	FString ObjectPathToPackagePath(const FString& ObjectPath)
	{
		int32 DotIndex;
		if (ObjectPath.FindLastChar(TEXT('.'), DotIndex))
		{
			return ObjectPath.Left(DotIndex);
		}
		return ObjectPath;
	}
}

void UACFEditorSubsystem::OnAssetRenamed(const FAssetData& AssetData, const FString& OldObjectPath)
{
	const UACFEditorSettings* Settings = GetDefault<UACFEditorSettings>();
	if (!Settings || !Settings->GetAutoGenerateRedirectors())
	{
		return;
	}

	const FString OldPackageName = ObjectPathToPackagePath(OldObjectPath);
	const FString NewPackageName = AssetData.GetSoftObjectPath().GetLongPackageName();
	if (OldPackageName.IsEmpty() || NewPackageName.IsEmpty() || OldPackageName.Equals(NewPackageName, ESearchCase::CaseSensitive))
	{
		return;
	}

	WritePackageRedirectToConfig(OldPackageName, NewPackageName);
}

void UACFEditorSubsystem::WritePackageRedirectToConfig(const FString& OldPackageName, const FString& NewPackageName)
{
	TSharedPtr<IPlugin> Plugin = IPluginManager::Get().FindPlugin(PluginName);
	if (!Plugin.IsValid())
	{
		return;
	}

	const FString RedirectLine = FString::Printf(TEXT("+PackageRedirects=(OldName=\"%s\", NewName=\"%s\")"), *OldPackageName, *NewPackageName);

	for (const FString& ConfigFileName : ACFRedirectConfigFileNames)
	{
		const FString ConfigPath = FPaths::Combine(Plugin->GetBaseDir(), TEXT("Config"), ConfigFileName);
		TArray<FString> Lines;
		if (!FFileHelper::LoadFileToStringArray(Lines, *ConfigPath))
		{
			Lines.Add(CoreRedirectsSection);
		}

		bool bAlreadyExists = false;
		for (const FString& Line : Lines)
		{
			if (Line.Contains(OldPackageName) && Line.Contains(TEXT("PackageRedirects")))
			{
				bAlreadyExists = true;
				break;
			}
		}
		if (bAlreadyExists)
		{
			continue;
		}

		int32 InsertIndex = INDEX_NONE;
		bool bInCoreRedirects = false;
		for (int32 i = 0; i < Lines.Num(); ++i)
		{
			if (Lines[i].StartsWith(TEXT("[")))
			{
				if (bInCoreRedirects)
				{
					InsertIndex = i;
					break;
				}
				bInCoreRedirects = Lines[i].Equals(CoreRedirectsSection, ESearchCase::CaseSensitive);
			}
			else if (bInCoreRedirects)
			{
				InsertIndex = i + 1;
			}
		}

		if (InsertIndex == INDEX_NONE)
		{
			if (bInCoreRedirects)
			{
				InsertIndex = Lines.Num();
			}
			else
			{
				Lines.Add(CoreRedirectsSection);
				InsertIndex = Lines.Num();
			}
		}

		Lines.Insert(RedirectLine, InsertIndex);

		if (!FFileHelper::SaveStringArrayToFile(Lines, *ConfigPath))
		{
			UE_LOG(LogTemp, Warning, TEXT("ACF: Failed to write redirect to %s"), *ConfigPath);
		}
	}
}

#undef LOCTEXT_NAMESPACE