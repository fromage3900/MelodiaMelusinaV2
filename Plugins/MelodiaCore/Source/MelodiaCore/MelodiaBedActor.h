#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "MelodiaBedActor.generated.h"

class UBoxComponent;
class UStaticMeshComponent;
class UMelodiaSaveGameSubsystem;

/** Placeholder bed proxy for Melusina's bedroom - no authored bed asset exists yet
 * (see Docs/MELODIA_OPENING_BUILD_PREP_2026-07-13.md). Sleeping saves the narrow
 * profile save (opening-flow phase + persistent party stats) via
 * UMelodiaSaveGameSubsystem. Repeatable interaction, not one-shot - sleeping to
 * save is naturally repeatable, unlike the Sir Melodious reunion beat this is
 * loosely modeled after. */
UCLASS(Blueprintable)
class MELODIACORE_API AMelodiaBedActor : public AActor
{
	GENERATED_BODY()

public:
	AMelodiaBedActor();

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Bed")
	bool bSaveOnInteract = true;

protected:
	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

	UFUNCTION()
	void HandleInteractionOverlap(UPrimitiveComponent* OverlappedComponent, AActor* OtherActor,
		UPrimitiveComponent* OtherComp, int32 OtherBodyIndex, bool bFromSweep, const FHitResult& SweepResult);

	UFUNCTION()
	void HandleSaveCompleted(bool bSuccess);

	/** Presentation hook - fade/prompt. Fires before SaveGame() executes. */
	UFUNCTION(BlueprintImplementableEvent, Category="Melodia|Bed")
	void PresentSleepBeat();

	/** Presentation hook - fires once SaveGame() has completed. */
	UFUNCTION(BlueprintImplementableEvent, Category="Melodia|Bed")
	void PresentSaveCompleted(bool bSuccess);

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Melodia|Bed")
	TObjectPtr<UStaticMeshComponent> BedMesh;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Melodia|Bed")
	TObjectPtr<UBoxComponent> InteractionTrigger;

private:
	UPROPERTY()
	TObjectPtr<UMelodiaSaveGameSubsystem> SaveSubsystem;
};
