// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "ACFEditorTypes.h"
#include "CoreMinimal.h"
#include "Engine/DataAsset.h"

#include "ACFAssetCreatorDataAsset.generated.h"

/**
 * Data asset that configures the Asset Creator default-class table.
 *
 * Create one of these assets in your project, populate DefaultClasses, then
 * assign it to the "Asset Creator Config Asset" field in Project Settings >
 * Ascent Editor Settings.  Once assigned, the deprecated inline
 * "Default Classes (Deprecated)" array in the settings page is ignored.
 */
UCLASS(BlueprintType)
class ASCENTEDITOREXTENSIONS_API UACFAssetCreatorDataAsset : public UDataAsset
{
	GENERATED_BODY()

public:
	/**
	 * Tag -> class bindings used by the Asset Creator UI.
	 * Each entry carries a Tag (lookup key), a Class (soft reference),
	 * a DisplayName and a Description shown in the picker.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Asset Creator",
		meta = (TitleProperty = "DisplayName"))
	TArray<FAssetCreatorDefaultClassEntry> DefaultClasses;
};
