// Optional player-pawn presentation hooks for authoritative Melodia combat.

#pragma once

#include "CoreMinimal.h"
#include "UObject/Interface.h"
#include "MelodiaBattleTypes.h"
#include "MelodiaCombatPresentationInterface.generated.h"

UINTERFACE(BlueprintType)
class MELODIACORE_API UMelodiaCombatPresentationInterface : public UInterface
{
	GENERATED_BODY()
};

class MELODIACORE_API IMelodiaCombatPresentationInterface
{
	GENERATED_BODY()

public:
	/** Presentation-only notification after a successful rhythm command resolves. */
	UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category="Melodia|Presentation")
	void OnMelodiaCommandResolved(FName CommandId, EMelodiaRhythmGrade RhythmGrade);

	/** Presentation-only notification when the encounter enters Victory for the first time. */
	UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category="Melodia|Presentation")
	void OnMelodiaVictory();

	/** Presentation-only notification when the encounter enters Defeat for the first time. */
	UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category="Melodia|Presentation")
	void OnMelodiaDefeat();
};
