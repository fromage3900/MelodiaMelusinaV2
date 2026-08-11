// Copyright Bruno Caxito. All Rights Reserved.

#pragma once

#include "Misc/EnumRange.h"

#include "CoreMinimal.h"
#include "Permission.generated.h"

/**
 * .
 */
UENUM(BlueprintType)
enum class EPermission : uint8
{
	/// Call

	CallBuiltInFunctions		UMETA(DisplayName = "Call Built-In Functions"),
	CallFunctionsByReference	UMETA(DisplayName = "Call Functions By Reference"),
	CallFunctionsByClass		UMETA(DisplayName = "Call Functions By Class"),
	CallFunctionsByTag			UMETA(DisplayName = "Call Functions By Tag"),


	/// Variables

	CreateGlobalVariables		UMETA(DisplayName = "Create Global Variables"),
	ModifyGlobalVariables		UMETA(DisplayName = "Modify Global Variables"),
	DeleteGlobalVariables		UMETA(DisplayName = "Delete Global Variables"),

	CreateTemporaryVariables	UMETA(DisplayName = "Create Temporary Variables"),
	ModifyTemporaryVariables	UMETA(DisplayName = "Modify Temporary Variables"),
	DeleteTemporaryVariables	UMETA(DisplayName = "Delete Temporary Variables"),


	/// Script

	PlayDialogues				UMETA(DisplayName = "Play Dialogues"),
	PlaySelections				UMETA(DisplayName = "Play Selections"),
	PlayRouters					UMETA(DisplayName = "Play Routers"),
	PlayDirectives				UMETA(DisplayName = "Play Directives"),


	Count UMETA(Hidden)
};
ENUM_RANGE_BY_COUNT(EPermission, EPermission::Count);


/**
 * .
 */
UENUM(BlueprintType)
enum class EPermissionMode : uint8
{
	/**
	 * All permissions, no exception.
	 * ! If the source script text comes from an external untrusted source, this can be used to exploit the game.
	 */
	All		UMETA(DisplayName = "All"),

	/**
	 * Play statements but can't handle variables or call functions.
	 */
	Safe	UMETA(DisplayName = "Safe"),

	/**
	 * Play this script isolated in its own universe.
	 * Play statements, can call built-in functions, and handle temporary variables.
	 */
	Sandbox	UMETA(DisplayName = "Sandbox")
};