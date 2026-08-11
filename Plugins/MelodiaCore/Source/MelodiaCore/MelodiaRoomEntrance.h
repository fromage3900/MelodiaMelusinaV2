#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "MelodiaRoomEntrance.generated.h"

class USceneComponent;

/**
 * ROGUELIKE-TRAVERSAL ONLY: marks the safe player arrival transform in a generated room.
 * It never opens a level, advances a run, or owns story progression.
 */
UCLASS(Blueprintable, meta=(DisplayName="Melodia Roguelike Room Entrance"))
class MELODIACORE_API AMelodiaRoomEntrance : public AActor
{
	GENERATED_BODY()

public:
	AMelodiaRoomEntrance();

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Melodia|Roguelike")
	TObjectPtr<USceneComponent> ArrivalTransform;

	/** Exactly one loaded entrance should be primary for the generated stage. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Roguelike")
	bool bPrimaryRunEntrance = true;
};
