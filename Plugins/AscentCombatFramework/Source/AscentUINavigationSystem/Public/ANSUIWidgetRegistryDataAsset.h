// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CommonActivatableWidget.h"
#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "GameplayTagContainer.h"

#include "ANSUIWidgetRegistryDataAsset.generated.h"

/**
 * Per-layer configuration. Define which other layers should be hidden
 * when this layer has an active widget.
 */
USTRUCT(BlueprintType)
struct FANSUILayerConfig {
	GENERATED_BODY()

	/** Other layers to hide when this layer has an active widget. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Layer", meta = (Categories = "UI.Layer"))
	TArray<FGameplayTag> HidesLayers;
};

/**
 * Per-widget spawn configuration stored in the Widget Registry.
 * All settings for a widget are defined here once so SpawnWidgetByTag
 * uses the correct layer, pause, and input-lock behaviour automatically.
 */
USTRUCT(BlueprintType)
struct FANSWidgetConfig {
	GENERATED_BODY()

	FANSWidgetConfig()
		: bPauseGame(true)
		, bLockGameInput(true)
	{}

	/** The widget class to spawn. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Widget")
	TSubclassOf<UCommonActivatableWidget> WidgetClass;

	/** Layer to push this widget onto. Leave empty to use the default layer. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Widget", meta = (Categories = "UI.Layer"))
	FGameplayTag LayerTag;

	/** If true, the game is paused while this widget is active. Disable for HUD or overlay widgets. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Widget")
	bool bPauseGame;

	/** If true, input is locked to UI-Only mode while this widget is active. Disable for HUD or overlay widgets. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Widget")
	bool bLockGameInput;
};

/**
 * Data Asset that maps GameplayTags to widget spawn configurations
 * and configures UI layer relationships.
 * Configure one in the Content Browser and assign it in
 * Project Settings > Plugins > Ascent Navigation Settings.
 */
UCLASS(BlueprintType)
class ASCENTUINAVIGATIONSYSTEM_API UANSUIWidgetRegistryDataAsset : public UPrimaryDataAsset {
	GENERATED_BODY()

public:
	/** Returns the widget class mapped to the given tag, or nullptr if not found. */
	UFUNCTION(BlueprintPure, Category = ANS)
	TSubclassOf<UCommonActivatableWidget> FindWidgetClassForTag(FGameplayTag Tag) const;

	/** Returns the full spawn config for a widget tag, or nullptr if not found. */
	const FANSWidgetConfig* FindConfigForTag(FGameplayTag Tag) const;

	/** Returns the spawn config for the given widget class, or nullptr if not found. */
	const FANSWidgetConfig* FindConfigForClass(TSubclassOf<UCommonActivatableWidget> WidgetClass) const;

	/** Returns the layer configuration map. */
	const TMap<FGameplayTag, FANSUILayerConfig>& GetLayerConfigs() const { return LayerConfigs; }

	/** Returns the config for a specific layer tag, or nullptr if not found. */
	const FANSUILayerConfig* FindLayerConfig(FGameplayTag LayerTag) const { return LayerConfigs.Find(LayerTag); }

protected:
	/**
	 * Maps widget GameplayTags to their full spawn configuration.
	 * Set WidgetClass, LayerTag, bPauseGame, and bLockGameInput per widget.
	 * HUD widgets should have bPauseGame=false and bLockGameInput=false.
	 */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Widgets", meta = (Categories = "UI.Widget"))
	TMap<FGameplayTag, FANSWidgetConfig> WidgetsByTag;

	/**
	 * Per-layer visibility rules. For each registered layer tag, define which
	 * other layers should be hidden when that layer has an active widget.
	 *
	 * Example: UI.Layer.Default -> HidesLayers: [UI.Layer.HUD]
	 * means the HUD is hidden whenever any page is active in the Default layer.
	 */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Layers", meta = (Categories = "UI.Layer"))
	TMap<FGameplayTag, FANSUILayerConfig> LayerConfigs;
};
