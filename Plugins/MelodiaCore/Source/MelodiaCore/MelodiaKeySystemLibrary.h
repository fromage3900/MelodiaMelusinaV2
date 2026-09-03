// Element weakness wheel and harmonic key damage rules.
// Ported from MelodiaMelusina_PROD to MelodiaCore plugin (UE 5.8).

#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "MelodiaSpellTypes.h"
#include "MelodiaKeySystemLibrary.generated.h"

UCLASS()
class MELODIACORE_API UMelodiaKeySystemLibrary : public UBlueprintFunctionLibrary
{
	GENERATED_BODY()

public:
	static constexpr float WeaknessMultiplier = 1.5f;
	static constexpr float ResistanceMultiplier = 0.75f;
	static constexpr float MatchingKeyWeaknessBonus = 1.25f;

	UFUNCTION(BlueprintPure, Category = "Melodia|Element Keys")
	static TArray<FMelodiaElementKeyDefinition> BuildDemoElementKeys();

	UFUNCTION(BlueprintPure, Category = "Melodia|Element Keys")
	static bool FindElementKey(FName KeyId, FMelodiaElementKeyDefinition& OutKey);

	UFUNCTION(BlueprintPure, Category = "Melodia|Element Keys")
	static FName GetKeyIdForMechanicLevel(int32 MechanicLevel);

	/** True when AttackElement is super-effective against DefenseElement on the weakness wheel. */
	UFUNCTION(BlueprintPure, Category = "Melodia|Element Keys")
	static bool IsWeaknessHit(EMelodiaSpellElement AttackElement, EMelodiaSpellElement DefenseElement);

	UFUNCTION(BlueprintPure, Category = "Melodia|Element Keys")
	static bool IsResistanceHit(EMelodiaSpellElement AttackElement, EMelodiaSpellElement DefenseElement);

	UFUNCTION(BlueprintPure, Category = "Melodia|Element Keys")
	static float GetElementDamageMultiplier(EMelodiaSpellElement AttackElement, EMelodiaSpellElement DefenseElement, bool bHasMatchingKey);

	/** Seed enemy element deterministically from encounter level (1-30 demo band). */
	UFUNCTION(BlueprintPure, Category = "Melodia|Element Keys")
	static EMelodiaSpellElement GetEnemyElementForEncounterLevel(int32 EncounterLevel);
};
