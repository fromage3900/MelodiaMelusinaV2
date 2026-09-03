// Copyright Bruno Caxito. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "PrintType.generated.h"

/**
 * Log message type enumerator.
 */
UENUM(BlueprintType)
enum class EPrintType : uint8
{
	Log		UMETA(DisplayName = "Log"),
	Success	UMETA(DisplayName = "Success"),
	Warning	UMETA(DisplayName = "Warning"),
	Error	UMETA(DisplayName = "Error")
};