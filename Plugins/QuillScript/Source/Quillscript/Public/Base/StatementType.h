// Copyright Bruno Caxito. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "StatementType.generated.h"

/**
 * Quillscript language statement type enumerator.
 */
UENUM(BlueprintType)
enum class EStatementType : uint8
{
	/// Non Statement Lines

	FreeText	UMETA(DisplayName = "Free Text"),
	Comment		UMETA(DisplayName = "//  Comment"),


	/// Statements.

	Dialogue	UMETA(DisplayName = "-  Dialogue"),
	Option		UMETA(DisplayName = "*  Option"),
	Label		UMETA(DisplayName = "@  Label"),
	Router		UMETA(DisplayName = "-> Router"),
	Command		UMETA(DisplayName = "$  Command"),
	Condition	UMETA(DisplayName = "?  Condition"),
	Directive	UMETA(DisplayName = "~  Directive")
};