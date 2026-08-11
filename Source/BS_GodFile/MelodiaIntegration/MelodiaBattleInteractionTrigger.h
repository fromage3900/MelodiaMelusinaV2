#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "MelodiaBattleInteractionTrigger.generated.h"

class UBoxComponent;
class UTextRenderComponent;

/**
 * Placeable interaction surface that delegates to the canonical narrative ->
 * stock-JRPG battle adapter. It owns no combat, reward, or result state.
 *
 * The authored stock encounter actor must carry EncounterId as an Actor Tag and
 * expose the adapter's confirmed StartBattle/offLevelBattleData/OnBattleOver contract.
 */
UCLASS(Blueprintable, meta=(DisplayName="Melodia JRPG Battle Interaction"))
class BS_GODFILE_API AMelodiaBattleInteractionTrigger final : public AActor
{
	GENERATED_BODY()

public:
	AMelodiaBattleInteractionTrigger();

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Melodia|Battle Interaction")
	TObjectPtr<UBoxComponent> InteractionVolume;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Melodia|Battle Interaction")
	TObjectPtr<UTextRenderComponent> PromptText;

	/** Must match exactly one stock JRPG battle actor's Actor Tag. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Battle Interaction")
	FName EncounterId = TEXT("KaleidoNaveMelodySlime");

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Battle Interaction")
	FText InteractionPrompt = NSLOCTEXT("Melodia", "BeginBattlePrompt", "Challenge  [F]");

	/** Called by Melusina's nearest-overlap interaction route. */
	UFUNCTION(BlueprintCallable, Category="Melodia|Battle Interaction")
	bool TryInteract(AActor* InteractingActor);

protected:
	virtual void BeginPlay() override;

};
