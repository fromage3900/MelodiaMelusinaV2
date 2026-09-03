// Copyright Bruno Caxito. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "ScriptIdMethod.generated.h"

/**
 * Call method enumerator.
 */
UENUM()
enum class EScriptIdMethod : uint8
{
	Name	UMETA(DisplayName = "Name"),
	Path	UMETA(DisplayName = "Path"),
	Random	UMETA(DisplayName = "Random"),

	Custom	UMETA(DisplayName = "Custom")
};