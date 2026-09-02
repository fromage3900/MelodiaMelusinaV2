#pragma once

#include "CoreMinimal.h"
#include "Engine/EngineTypes.h"
#include "GameFramework/Actor.h"
#include "MelodiaTravelInteractionPortal.generated.h"

class UBoxComponent;
class UTextRenderComponent;

/**
 * Explicit, player-confirmed story exit routed through the single travel authority.
 *
 * This shell is intentionally Blueprint-extensible: content children may provide
 * presentation and authored prompts while TravelSubsystem remains the only route
 * owner. Do not add direct map loading to a child.
 */
UCLASS(Blueprintable, meta=(DisplayName="Melodia Travel Interaction Portal"))
class BS_GODFILE_API AMelodiaTravelInteractionPortal : public AActor
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

	/** Optional capability required before this portal accepts interaction. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Travel Interaction|Capability")
	FName RequiredTraversalCapability = TEXT("capability.melodia.glide");

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Travel Interaction|Capability")
	FName TraversalCapabilityContext = TEXT("active_traversal_context");

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Travel Interaction|Capability")
	FText LockedInteractionPrompt = NSLOCTEXT("Melodia", "TraversalLockedPrompt", "A Resonant Form is required");

	UFUNCTION(BlueprintPure, Category="Melodia|Travel Interaction|Capability")
	bool IsTraversalUnlocked(FName& OutBlockReason) const;

	/** Called by Melusina's nearest-overlap interaction route. */
	UFUNCTION(BlueprintCallable, Category="Melodia|Travel Interaction")
	bool TryInteract(AActor* InteractingActor);

protected:
	virtual void BeginPlay() override;

private:
	void RefreshCapabilityPrompt();

	bool bTravelRequested = false;
	FTimerHandle CapabilityRefreshTimerHandle;
};
