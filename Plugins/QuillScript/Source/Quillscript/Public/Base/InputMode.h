// Copyright Bruno Caxito. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "InputMode.generated.h"

/**
 * Input mode enumerator.
 */
UENUM(BlueprintType)
enum class EInputMode : uint8
{
	/**
	 * Project Settings:	This setting-related functionality will keep as it is.
	 * Script Settings:		Use the value defined for this setting in project settings.
	 */
	Default		UMETA(DisplayName = "Default"),

	GameOnly	UMETA(DisplayName = "Game Only"),
	GameAndUI	UMETA(DisplayName = "Game and UI"),
	UIOnly		UMETA(DisplayName = "UI Only")
};