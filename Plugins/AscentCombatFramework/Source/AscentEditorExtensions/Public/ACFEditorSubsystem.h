// Copyright (C) Developed by Pask & OlssonDev, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Factory/ACFActorFactory.h"
#include "IAssetTools.h"
#include "IPlacementModeModule.h"
#include "UObject/Object.h"
#include "ACFEditorTypes.h"

#include "ACFEditorSubsystem.generated.h"

class UACFEditorSettings;
class UACFAssetAction;
class UAssetCreator_ActorFactory;
class UACFBaseFactory;
class AACFCharacter;
class UACFCharacterDataAsset;

UCLASS()
class ASCENTEDITOREXTENSIONS_API UACFEditorSubsystem : public UEditorSubsystem {
	GENERATED_BODY()

	// USubsystem interface implementation
	virtual void Initialize(FSubsystemCollectionBase& Collection) override;

	virtual void Deinitialize() override;
	// End of implementation

public:
	// Check if class already has a factory
	static bool HasFactory(UClass* Class);

	// Gather all derived classes from the given class, including blueprints.
	TArray<UClass*> GatherAllAssetsOfClass(UClass* Class);

	/**
	 * Extracts data from an ACFCharacter's components and fills a UACFCharacterDataAsset.
	 * @param Character The source character (must be valid)
	 * @param OutDataAsset The data asset to fill (must be allocated, e.g. NewObject)
	 * @return True if the fill was successful
	 */
	UFUNCTION(BlueprintCallable, Category = "ACF|Editor")
	bool FillCharacterDataFromCharacter(AACFCharacter* Character, UACFCharacterDataAsset* OutDataAsset);

	/** Refreshes place actors menu and content browser categories (e.g. after settings change). */
	void RefreshAll();

private:
	void OnEditorOpened(const FString& FileName, bool bAsTemplate);

	// Reads "ACFVariant" from the .uplugin JSON and merges the matching
	// Config/<variant>/*.ini files into GConfig at editor startup.
	void ApplyVariantConfig();

	// Refreshes both place actors menu and the categories in the content browser
	void RefreshActions();

	void RefreshAssetTypeActions();

	void RefreshPlacementMode();

	// When a Asset Creator has changed its properties.
	void OnAssetCreatorChanged(UObject* Object, FPropertyChangedEvent& ChangedEvent);

	void OnAssetCreated(const FAssetData& AssetData);
	void OnAssetsDeleted(const TArray<UClass*>& AssetsToDelete);

	void OnAssetRenamed(const FAssetData& AssetData, const FString& OldObjectPath);
	void WritePackageRedirectToConfig(const FString& OldPackageName, const FString& NewPackageName);

	UACFAssetAction* GetAssetAction(UClass* AssetActionClass);

	// Find the class from a Blueprint asset.
	bool GetClassFromBlueprint(const FAssetData Class, UClass* ClassToFind, UClass*& GeneratedClass);

	// Register category in content browser
	void RegisterAssetTypeAction(IAssetTools& AssetTools, TSharedRef<IAssetTypeActions> Action);

	// Unregister category in content browser
	void UnregisterAssetTypeAction(IAssetTools& AssetTools, TSharedRef<IAssetTypeActions> Action);

	// Make a Actor Factory from a Asset Action
	UACFActorFactory* MakeActorFactory(UACFAssetAction* AssetAction);

	UACFBaseFactory* MakeFactory(UACFAssetAction* AssetAction);
	UACFAssetAction* MakeActorAction(const FAssetActionSettings& assetSetting);
	UACFActorFactory* MakeActorFactoryFromClass(TSubclassOf<AActor> AssetClass);
	UACFEditorSettings* GetEditorSettings() const;

private:
	// Keep track of actor factories we have created to remove them when we refresh the actions.
	UPROPERTY(Transient)
	TArray<UActorFactory*> ActorFactories;

	// Keep all Factories of UACFBaseFactory loaded.
	UPROPERTY(Transient)
	TArray<UClass*> Factories;

	// Keep all asset actions loaded and cached. So we don't need to get them all the time.
	UPROPERTY(Transient)
	TArray<UClass*> AssetActions;

	UPROPERTY(Transient)
	TArray<UACFAssetAction*> AssetActionsInst;

	UPROPERTY(Transient)
	TArray<UACFBaseFactory*> BaseFactories;

	// Keep track of all AssetTypeActions so we can unregister them on refresh.
	TArray<TSharedRef<IAssetTypeActions>> AssetTypeActions;

	// Keep track of all Placeable Items so we can unregister them on refresh.
	TArray<TOptional<FPlacementModeID>> RegisteredPlaceableItems;

	// Keep track of all Placeable Items categories so we can unregister them on refresh.
	TArray<FPlacementCategoryInfo> RegisteredPlaceableItemCategories;

	FDelegateHandle AssetRenamedHandle;

private:
	FDelegateHandle OnMapOpenedDelegate;
};
