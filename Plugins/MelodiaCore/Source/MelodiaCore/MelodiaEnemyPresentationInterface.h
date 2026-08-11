// Optional presentation hooks for battle enemy actors.

#pragma once

#include "CoreMinimal.h"
#include "UObject/Interface.h"
#include "MelodiaBattleTypes.h"
#include "MelodiaCoreRulesLibrary.h"
#include "MelodiaEnemyPresentationInterface.generated.h"

UINTERFACE(BlueprintType)
class MELODIACORE_API UMelodiaEnemyPresentationInterface : public UInterface
{
	GENERATED_BODY()
};

class MELODIACORE_API IMelodiaEnemyPresentationInterface
{
	GENERATED_BODY()

public:
	UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category="Melodia|Enemy Presentation")
	void OnMelodiaEnemyIntentStarted(FName EnemyId, FName IntentId);

	UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category="Melodia|Enemy Presentation")
	void OnMelodiaEnemyHit(FName EnemyId, float Damage, EMelodiaRhythmGrade RhythmGrade);

	UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category="Melodia|Enemy Presentation")
	void OnMelodiaEnemyBroken(FName EnemyId);

	UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category="Melodia|Enemy Presentation")
	void OnMelodiaEnemyDefeated(FName EnemyId);
};
