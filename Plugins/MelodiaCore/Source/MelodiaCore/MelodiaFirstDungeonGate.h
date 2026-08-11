#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "MelodiaFirstDungeonGate.generated.h"

class AMelodiaDungeonRunCoordinator;
class UBoxComponent;
class UTextRenderComponent;
class UPrimitiveComponent;
struct FHitResult;

/** Authored ZenForest doorway that becomes usable after the Sakura tutorial victory. */
UCLASS(Blueprintable)
class MELODIACORE_API AMelodiaFirstDungeonGate : public AActor
{
	GENERATED_BODY()

public:
	AMelodiaFirstDungeonGate();

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Melodia|Opening")
	TObjectPtr<UBoxComponent> TriggerVolume;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Melodia|Opening")
	TObjectPtr<UTextRenderComponent> PromptText;

	UPROPERTY(EditInstanceOnly, BlueprintReadWrite, Category="Melodia|Opening")
	TObjectPtr<AMelodiaDungeonRunCoordinator> RunCoordinator;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Opening")
	int32 FirstRunSeed = 0;

	UFUNCTION(BlueprintPure, Category="Melodia|Opening")
	bool IsUnlocked() const { return bUnlocked; }

protected:
	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

private:
	UFUNCTION()
	void HandleFirstDungeonUnlocked();

	UFUNCTION()
	void HandleOverlap(UPrimitiveComponent* OverlappedComponent, AActor* OtherActor,
		UPrimitiveComponent* OtherComp, int32 OtherBodyIndex, bool bFromSweep,
		const FHitResult& SweepResult);

	void SetUnlocked(bool bNewUnlocked);
	bool bUnlocked = false;
	bool bEntered = false;
};
