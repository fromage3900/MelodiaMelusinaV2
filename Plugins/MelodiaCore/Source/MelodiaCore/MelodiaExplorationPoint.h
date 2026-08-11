#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "MelodiaExplorationPoint.generated.h"

class USphereComponent;
class UPrimitiveComponent;
struct FHitResult;

/**
 * A single authored thing-to-look-at in the Morning bedroom exploration phase.
 * Placeable, one-shot: the player overlapping it once reports PointId to
 * UMelodiaOpeningFlowSubsystem and does nothing further on subsequent overlaps.
 *
 * Deliberately dumb -- no visual/audio cue is authored here. That stays in
 * content (a Blueprint child, or a hook on the trigger) so this class is not
 * re-touched every time the presentation changes.
 */
UCLASS(Blueprintable)
class MELODIACORE_API AMelodiaExplorationPoint : public AActor
{
	GENERATED_BODY()

public:
	AMelodiaExplorationPoint();

protected:
	virtual void BeginPlay() override;

	UFUNCTION()
	void HandleOverlap(UPrimitiveComponent* OverlappedComponent, AActor* OtherActor,
		UPrimitiveComponent* OtherComp, int32 OtherBodyIndex, bool bFromSweep, const FHitResult& SweepResult);

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Melodia|Opening|Exploration")
	TObjectPtr<USphereComponent> Trigger;

	/** Unique per placed instance -- "Bookshelf", "Window", "OldPhoto", etc.
	 * Two points sharing an Id count as one for the required-visits gate. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Opening|Exploration")
	FName PointId;

private:
	bool bVisited = false;
};
