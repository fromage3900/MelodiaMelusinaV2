#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "MelodiaRoomExit.generated.h"

class UBoxComponent;
class UTextRenderComponent;
class AMelodiaDungeonRunCoordinator;

/**
 * ROGUELIKE-TRAVERSAL ONLY: advances the active run and regenerates streamed rooms.
 * Never opens an authored map and never owns story/opening progression.
 */
UCLASS(Blueprintable, meta=(DisplayName="Melodia Roguelike Room Exit"))
class MELODIACORE_API AMelodiaRoomExit : public AActor
{
	GENERATED_BODY()

public:
	AMelodiaRoomExit();

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Melodia|Roguelike")
	TObjectPtr<UBoxComponent> TriggerVolume;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Melodia|Roguelike")
	TObjectPtr<UTextRenderComponent> StatusLabel;

	UPROPERTY(EditInstanceOnly, BlueprintReadWrite, Category="Melodia|Roguelike")
	TObjectPtr<AMelodiaDungeonRunCoordinator> Coordinator;

	/** Temporary compatibility path for existing maps. New authored exits must assign Coordinator explicitly. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Roguelike|Migration")
	bool bAllowCoordinatorAutoResolve = true;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Roguelike")
	bool bLocked = true;

	UFUNCTION(BlueprintCallable, Category="Melodia|Roguelike")
	void SetLocked(bool bNewLocked);

protected:
	virtual void BeginPlay() override;

private:
	UFUNCTION()
	void HandleOverlap(UPrimitiveComponent* OverlappedComponent, AActor* OtherActor,
		UPrimitiveComponent* OtherComp, int32 OtherBodyIndex, bool bFromSweep,
		const FHitResult& SweepResult);

	bool bTransitionRequested = false;
};
