// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "GameplayTagContainer.h"
#include "UObject/NoExportTypes.h"
#include "UObject/SoftObjectPtr.h"

#include "ACFEditorTypes.generated.h"

/**
 * Single entry in the Asset Creator default-class table.
 * Stored as a TArray so the editor UI can show DisplayName as a title
 * and the struct can be looked up by tag via FindByKey(Tag).
 */
USTRUCT(BlueprintType)
struct FAssetCreatorDefaultClassEntry
{
	GENERATED_BODY()

	/** GameplayTag used as the lookup key (e.g. AssetCreator.DataAsset). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, config, Category = "Asset Creator", meta = (Categories = "DataAssetCreator"))
	FGameplayTag Tag;

	/** Soft reference to the default class for this tag. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, config, Category = "Asset Creator")
	TSoftClassPtr<UObject> Class;

	/** Human-readable label shown in the Asset Creator UI and as the row title in Project Settings. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, config, Category = "Asset Creator")
	FText DisplayName;

	/** Optional icon displayed in the Asset Creator UI for this entry. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, config, Category = "Asset Creator")
	TSoftObjectPtr<UTexture2D> Icon;

	/** Human-readable description shown in the Asset Creator UI and as the row title in Project Settings. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, config, Category = "Asset Creator")
	FText Description;

	/** Equality between two entries (compares by Tag). */
	bool operator==(const FAssetCreatorDefaultClassEntry& Other) const { return Tag == Other.Tag; }
     
	/** Key-based equality so TArray::FindByKey(FGameplayTag) works directly. */
	bool operator==(const FGameplayTag& InTag) const { return Tag == InTag; }
};

USTRUCT(BlueprintType)
struct FAssetIconData
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, config, Category = "Custom Asset Icons")
    TSoftObjectPtr<UTexture2D> Icon;

    UPROPERTY(EditAnywhere, config, Category = "Custom Asset Icons")
    FLinearColor IconTint = FLinearColor(0.85f, 0.85f, 0.85f, .85f);


    UPROPERTY(EditAnywhere, config, Category = "Custom Asset Icons")
    FVector2D IconScale = FVector2D(.7f, .7f);
};

USTRUCT(BlueprintType)
struct FAssetActionConfig {
    GENERATED_BODY()

    // The class you want this Asset Action to be responsible for.
    UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = "Class Settings")
    TSoftClassPtr<UObject> AssetClass;

    /*Replaces the default class name if not empty*/
    UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = "Class Settings")
    FText ClassNameOverride;

    // The color of the asset in the editor menus only. Once the asset is created it will default back to its original color.
    // By default it's the default Blueprint color.
    UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = "Cosmetic")
    FColor AssetColor = FColor(63, 126, 255);
};

USTRUCT(BlueprintType)
struct FAssetActionSettings {
    GENERATED_BODY()

    FAssetActionSettings()
    {
        CategoryName = "ACF Gameplay";
        ClassNameOverride = FText::FromString("");
    }

    FAssetActionSettings(const FAssetActionConfig& actionConfig, const FName& inCategoryName, 
        const bool bInSubMenu, const FText& inSubCategoryName)
    {
        AssetClass = actionConfig.AssetClass.Get();
        ClassNameOverride = actionConfig.ClassNameOverride;
        bEnabled = true;
        CategoryName = inCategoryName;
        UseSubMenu = bInSubMenu;
        SubCategoryName = inSubCategoryName;
        AssetColor = actionConfig.AssetColor;
    }

    // If this Asset Action is enabled and show up in the set category.
    UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = "Asset Action")
    bool bEnabled = true;

    // The class you want this Asset Action to be responsible for.
    UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = "Class Settings")
    TSubclassOf<UObject> AssetClass;

    /*Replaces the default class name if not empty*/
    UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = "Class Settings")
    FText ClassNameOverride;

    // The name of the category this Asset Action should be in.
    // Example: Weapons
    UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = "Asset Category")
    FName CategoryName;

    // Bool to check if sub menu should be considered at all in the drop down menu.
    UPROPERTY()
    bool UseSubMenu = false;

    // The name of the Sub Category this Asset Action will exists in within the category. If left empty, it will count as no SubCategory.
    // NOTE: A sub category can only be created if there are more than one item in the main category.
    UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = "Asset Category", meta = (EditCondition = UseSubMenu))
    FText SubCategoryName;

    // The color of the asset in the editor menus only. Once the asset is created it will default back to its original color.
    // By default it's the default Blueprint color.
    UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = "Cosmetic")
    FColor AssetColor = FColor(63, 126, 255);

    bool IsValid()
    {
        return bEnabled && !CategoryName.IsNone() && AssetClass;
    }
};

USTRUCT(BlueprintType)
struct FCategoryConfig {
    GENERATED_BODY()

    // The name of the category this Asset Action should be in.
    UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = "Asset Category")
    FName CategoryName = "ACF";

    UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = "Asset Category", meta = (TitleProperty = "ClassNameOverride"))
    TArray<FAssetActionConfig> Entries;
};

USTRUCT(BlueprintType)
struct FPlaceCategoryConfig : public FCategoryConfig {
    GENERATED_BODY()

    UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = "Asset Category")
    FName IconName = "ACFEditor.SmallIcon";

    /** Controls the position of this tab in the Place Actors sidebar.
     *  Lower values appear higher. Built-in tabs: Favorites=0, Recent=1, Basic=10, Lights=15, Shapes/Cine=20.
     *  Default is 1, placing the ACF tab right after Favorites. */
    UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = "Asset Category")
    int32 SortOrder = 1;
};

USTRUCT(BlueprintType)
struct FMainCategoryConfig {
    GENERATED_BODY()

    // The name of the category this Asset Action should be in.
    UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = "Asset Category")
    FName MainCategoryName = "Ascent Combat Framework";

    UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = "Asset Category", meta = (TitleProperty = "ClassNameOverride"))
    TArray<FAssetActionConfig> Entries;

    UPROPERTY(BlueprintReadWrite, meta = (TitleProperty = "CategoryName"), EditAnywhere, Category = "Asset Category")
    TArray<FCategoryConfig> SubCategories;
};

UCLASS()
class ASCENTEDITOREXTENSIONS_API UACFEditorTypes : public UObject {
    GENERATED_BODY()
};
