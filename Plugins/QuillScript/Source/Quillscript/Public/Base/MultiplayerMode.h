// Copyright Bruno Caxito. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "MultiplayerMode.generated.h"

/**
 * Quillscript multiplayer mode enumerator.
 */
UENUM(BlueprintType)
enum class EMultiplayerMode : uint8
{
	/** This game has no need for Quillscript multiplayer features. */
	None		UMETA(DisplayName = "None"),

	/** Only the server/host player can start a script. */
	HostOnly	UMETA(DisplayName = "Host Only"),

	/** Any player can start a script. */
	Individual	UMETA(DisplayName = "Individual")
};