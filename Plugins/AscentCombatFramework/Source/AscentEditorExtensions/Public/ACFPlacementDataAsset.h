// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "ACFEditorTypes.h"
#include "CoreMinimal.h"
#include "Engine/DataAsset.h"

#include "ACFPlacementDataAsset.generated.h"

/**
 * Data asset that holds one or more placement tab configurations for the
 * Quick Placement (Place Actors) panel.
 *
 * Each entry in Categories becomes its own tab in the Place Actors sidebar,
 * with an independent CategoryName, IconName, SortOrder and actor list.
 *
 * When this asset is assigned to "Placement Entries Asset" in Ascent Editor
 * Settings, the Categories array here fully replaces the inline
 * QuickPlacementActor configuration in Project Settings, allowing you to
 * expose as many or as few tabs as you want from a single data asset.
 *
 * If no asset is assigned, the system falls back to the single
 * QuickPlacementActor entry defined in Project Settings.
 */
UCLASS(BlueprintType)
class ASCENTEDITOREXTENSIONS_API UACFPlacementDataAsset : public UDataAsset
{
	GENERATED_BODY()

public:
	/**
	 * One entry per tab to register in the Quick Placement (Place Actors) panel.
	 * Each category can have its own name, icon, sort order and actor list.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Placement", meta = (TitleProperty = "CategoryName"))
	TArray<FPlaceCategoryConfig> Categories;

};
