// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "AUTThemeDataAsset.h"
#include "AUTTypes.h"
#include "Components/InputComponent.h"
#include "CoreMinimal.h"
#include "Engine/DataTable.h"
#include "Engine/DeveloperSettings.h"
#include "GameplayTagContainer.h"
#include "UObject/SoftObjectPath.h"
#include "UObject/SoftObjectPtr.h"

#include "AUTDeveloperSettings.generated.h"

class FAUTAnalogCursor;

UCLASS(config = Plugins, Defaultconfig, meta = (DisplayName = "Ascent UI Settings"))
class ASCENTUITOOLS_API UAUTDeveloperSettings : public UDeveloperSettings {
    GENERATED_BODY()

public:
    UAUTDeveloperSettings() {};

    UAUTThemeDataAsset* GetTheme() const;

    TArray<FSoftObjectPath> GetDefaultSoundClasses() const { return DefaultSoundClasses; }
    TSoftObjectPtr<UWorld> GetDefaultMenuMapRef() const;
    TSoftObjectPtr<UWorld> GetDefaultNewGameMapRef() const;

    /** Returns the soft path to the Widget Registry Data Asset. */
    const FSoftObjectPath& GetWidgetRegistryPath() const { return WidgetRegistryAsset; }

    /** Returns the GameplayTag of the default UI layer used when no LayerTag is specified. Defaults to UI.Layer.Default. */
    const FGameplayTag& GetDefaultLayerTag() const
    {
        if (DefaultLayerTag.IsValid()) { return DefaultLayerTag; }
        static const FGameplayTag Fallback = FGameplayTag::RequestGameplayTag(FName("UI.Layer.Default"));
        return Fallback;
    }

    /** Returns the icons-by-tag DataTable, loading it synchronously if needed. */
    UDataTable* GetIconsByTag() const { return IconsByTag.LoadSynchronous(); }

    /** Returns the DataTable mapping keys to icons for the given platform name. */
    UDataTable* GetKeysConfigForPlatform(const FString& Platform) const;

protected:
    UPROPERTY(config, EditAnywhere, Category = Style, meta = (AllowedClasses = "/Script/AscentUITools.AUTThemeDataAsset"))
    FSoftObjectPath ThemesAsset;

    /** If set, this map will be loaded when the Editor starts up. */
	UPROPERTY(config, EditAnywhere, Category=DefaultMaps, meta=(AllowedClasses="/Script/Engine.World"))
	FSoftObjectPath DefaultMenuMap;

    UPROPERTY(config, EditAnywhere, Category=DefaultMaps, meta=(AllowedClasses="/Script/Engine.World"))
	FSoftObjectPath DefaultNewGameMap;

   UPROPERTY(config, EditAnywhere, Category = DefaultMaps, meta=(AllowedClasses="/Script/Engine.SoundClass"))
    TArray<FSoftObjectPath> DefaultSoundClasses;

    /** Widget Registry Data Asset mapping GameplayTags to widget classes. */
    UPROPERTY(config, EditAnywhere, Category = "Navigation",
        meta = (AllowedClasses = "/Script/AscentUINavigationSystem.ANSUIWidgetRegistryDataAsset"))
    FSoftObjectPath WidgetRegistryAsset;

    /**
     * Default UI layer used by SpawnInGameWidget when no LayerTag is specified.
     * Must match one of the layers registered via RegisterLayer() in your HUD.
     * If empty, the first layer registered becomes the default.
     */
    UPROPERTY(config, EditAnywhere, Category = "Navigation", meta = (Categories = "UI.Layer"))
    FGameplayTag DefaultLayerTag;

    /** DataTable mapping FGameplayTag -> UTexture2D used to draw UI icons by tag. */
    UPROPERTY(config, EditAnywhere, Category = "UI Keys",
        meta = (RequiredAssetDataTags = "RowStructure=/Script/AscentUINavigationSystem.ANSIcons"))
    TSoftObjectPtr<UDataTable> IconsByTag;

    /** Per-platform DataTables mapping FKey -> UTexture2D for key prompt icons. */
    UPROPERTY(config, EditAnywhere, Category = "UI Keys",
        meta = (RequiredAssetDataTags = "RowStructure=/Script/AscentUINavigationSystem.ANSKeysIconConfig"))
    TMap<FString, TSoftObjectPtr<UDataTable>> KeysConfigByPlatform;
};
