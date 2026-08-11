#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "MelodiaTravelInteractionPortal.generated.h"

class UBoxComponent;
class UTextRenderComponent;

/** Explicit, player-confirmed story exit routed through the single travel authority. */
UCLASS(Blueprintable, meta=(DisplayName="Melodia Travel Interaction Portal"))
class BS_GODFILE_API AMelodiaTravelInteractionPortal final : public AActor
{
	GENERATED_BODY()

public:
	AMelodiaTravelInteractionPortal();

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Melodia|Travel Interaction")
	TObjectPtr<UBoxComponent> InteractionVolume;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Melodia|Travel Interaction")
	TObjectPtr<UTextRenderComponent> PromptText;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Travel Interaction", meta=(AllowedClasses="/Script/Engine.World"))
	FName DestinationMap = TEXT("/Game/ZenForestTest");

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Travel Interaction")
	FName DestinationSpawnTag = NAME_None;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Travel Interaction")
	FText InteractionPrompt = NSLOCTEXT("Melodia", "ContinueExplorationPrompt", "Continue exploring  [F]");

	/** Called by Melusina's nearest-overlap interaction route. */
	UFUNCTION(BlueprintCallable, Category="Melodia|Travel Interaction")
	bool TryInteract(AActor* InteractingActor);

protected:
	virtual void BeginPlay() override;

private:
	bool bTravelRequested = false;
};
