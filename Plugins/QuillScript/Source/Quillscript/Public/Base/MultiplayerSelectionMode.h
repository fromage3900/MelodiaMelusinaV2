// Copyright Bruno Caxito. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "MultiplayerSelectionMode.generated.h"

/**
 * Quillscript multiplayer option selection mode enumerator.
 */
UENUM(BlueprintType)
enum class EMultiplayerSelectionMode : uint8
{
	/** Only the server/host player can select options. */
	Host	UMETA(DisplayName = "Host"),

	/** Only the player that started the script (Owner) can select options. */
	Owner	UMETA(DisplayName = "Owner"),

	/**
	 * The option is selected by a poll result with all players currently joined to that script play.
	 * In case of a tie, the player that started the script wins.
	 */
	Poll	UMETA(DisplayName = "Poll")
};