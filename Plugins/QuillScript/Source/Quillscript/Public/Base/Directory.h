// Copyright Bruno Caxito. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Directory.generated.h"

/**
 * Directory type enumerator.
 */
UENUM(BlueprintType)
enum class EDirectory : uint8
{
	Custom 			UMETA(DisplayName = "Custom"),

	Project 		UMETA(DisplayName = "Project"),
	ProjectContent 	UMETA(DisplayName = "Project Content"),
	ProjectSaved 	UMETA(DisplayName = "Project Saved"),
	ProjectConfig 	UMETA(DisplayName = "Project Config"),

	ScreenShot		UMETA(DisplayName = "Screenshot"),
	Launch			UMETA(DisplayName = "Launch")
};


/**
 * File selection type enumerator.
 */
UENUM(BlueprintType)
enum class EFileSelection : uint8
{
	Single		UMETA(DisplayName = "Single File"),
	Multiple	UMETA(DisplayName = "Multiple Files")
};