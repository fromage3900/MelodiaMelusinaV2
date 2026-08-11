// Copyright Bruno Caxito. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Picker.generated.h"

/**
 * Setting value enumerator.
 */
UENUM(BlueprintType)
enum class EPicker : uint8
{
	/**
	 * Project Settings:	This setting-related functionality will keep as it is.
	 * Script Settings:		Use the value defined for this setting in project settings.
	 */
	Default		UMETA(DisplayName = "Default"),

	Yes			UMETA(DisplayName = "Yes"),
	No			UMETA(DisplayName = "No")
};