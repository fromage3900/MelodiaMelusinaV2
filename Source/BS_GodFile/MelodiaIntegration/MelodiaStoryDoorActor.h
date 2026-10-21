#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "MelodiaStoryDoorComponent.h"
#include "MelodiaStoryDoorActor.generated.h"

class UBoxComponent;
class UStaticMeshComponent;

/**
 * A story-gated doorway for the Houdini room suites (and any authored room): blocks the opening until its narrative flag is earned.
 *
 *   Sealed      leaf fills the opening and blocks pawns
 *   Assembling  the leaf rises like a drawn curtain over AssemblySeconds (one bar of the room's song); still blocking until done
 *   Open        leaf hidden, collision off
 *
 * State is re-derived from UMelodiaNarrativeSubsystem::GetNarrativeFlag on BeginPlay (via the story-door component), so save/load and
 * replays land in the right stage with no animation. Presentation only: it never writes gameplay state.
 * Doorway size defaults match the room_shell door (1.0 m x 2.15 m); set OpeningSizeCm per instance from the suite JSON.
 */
UCLASS(Blueprintable)
class BS_GODFILE_API AMelodiaStoryDoorActor : public AActor
{
	GENERATED_BODY()

public:
	AMelodiaStoryDoorActor();

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Melodia|Story Door")
	TObjectPtr<USceneComponent> Root;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Melodia|Story Door")
	TObjectPtr<UStaticMeshComponent> Leaf;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Melodia|Story Door")
	TObjectPtr<UBoxComponent> Blocker;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Melodia|Story Door")
	TObjectPtr<UMelodiaStoryDoorComponent> StoryDoor;

	/** Doorway width (X, along the wall), thickness (Y) and height (Z) in cm. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Story Door")
	FVector OpeningSizeCm = FVector(100.0, 8.0, 215.0);

	virtual void OnConstruction(const FTransform& Transform) override;
	virtual void BeginPlay() override;
	virtual void Tick(float DeltaSeconds) override;

private:
	UFUNCTION()
	void HandleStage(EMelodiaStoryDoorStage Stage, bool bFromLoad);

	void ApplyLeaf(float Fraction);   // 1 = closed, 0 = gone

	float AssemblyElapsed = 0.0f;
	bool bAssembling = false;
};
