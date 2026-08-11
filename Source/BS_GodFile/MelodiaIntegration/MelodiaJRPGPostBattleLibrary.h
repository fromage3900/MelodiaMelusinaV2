#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "MelodiaJRPGPostBattleLibrary.generated.h"

/**
 * Post-battle party recovery seam.
 *
 * The stock template persists unit state (currentHP / currentMP) across
 * encounters and nothing heals it, so a dead unit stays dead and the party
 * trends toward an unwinnable state -- a soft-lock vector in a slice with no
 * shop or inn loop. This restores the live battle unit instances to full HP/MP
 * at battle end, BEFORE the stock UpdatePlayerUnits sync writes their state
 * back into the controller's persistent map.
 *
 * Authority stays stock: party, turns, damage and persistence are untouched.
 * This only mutates the stock currentHP/currentMP fields on the stock unit
 * instances, through the stock BattleBase's playerUnits array.
 */
UCLASS()
class BS_GODFILE_API UMelodiaJRPGPostBattleLibrary : public UBlueprintFunctionLibrary
{
	GENERATED_BODY()

public:
	/**
	 * Restores every player unit in the active battle to full HP/MP.
	 *
	 * @param BattleController The stock battle controller whose `battle` variable
	 *                         names the active BP_BattleBase; the base's
	 *                         `playerUnits` array holds the live unit instances.
	 *                         No-op when the battle base or its units cannot be
	 *                         read -- recovery must never interrupt stock flow.
	 */
	UFUNCTION(BlueprintCallable, Category = "Melodia|Party")
	static void RestorePartyAfterBattle(UObject* BattleController);
};
