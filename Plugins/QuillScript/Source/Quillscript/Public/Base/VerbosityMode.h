// Copyright Bruno Caxito. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "VerbosityMode.generated.h"

/**
 * Verbosity mode enumerator.
 */
UENUM()
enum class EVerbosityMode : uint8
{
	Full	UMETA(DisplayName = "Screen and Console"),
	Console	UMETA(DisplayName = "Console Only"),
	None	UMETA(DisplayName = "Neither")
};