// Copyright Bruno Caxito. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "SettingsFile.generated.h"

/**
 * Setting file enumerator.
 */
UENUM(BlueprintType)
enum class ESettingsFile : uint8
{
	// Editor per-project ini files.

	Game				UMETA(DisplayName = "Game"),
	Editor				UMETA(DisplayName = "Editor"),
	Input				UMETA(DisplayName = "Input"),
	Hardware			UMETA(DisplayName = "Hardware"),
	GameUserSettings	UMETA(DisplayName = "Game User Settings"),
	EditorPerProject	UMETA(DisplayName = "Editor per Project"),
	RuntimeOptions		UMETA(DisplayName = "Runtime Options"),
	DeviceProfiles		UMETA(DisplayName = "Device Profiles"),
	GameplayTags		UMETA(DisplayName = "Gameplay Tags"),
	Compat				UMETA(DisplayName = "Compat"),
	Lightmass			UMETA(DisplayName = "Lightmass"),
	Scalability			UMETA(DisplayName = "Scalability"),
	InstallBundle		UMETA(DisplayName = "Install Bundle"),


	// Editor ini files.

	EditorLayout		UMETA(DisplayName = "Editor Layout"),
	EditorKeyBindings	UMETA(DisplayName = "Editor Ke yBindings"),
	EditorSettings		UMETA(DisplayName = "Editor Settings"),


	Custom				UMETA(DisplayName = "Custom")
};