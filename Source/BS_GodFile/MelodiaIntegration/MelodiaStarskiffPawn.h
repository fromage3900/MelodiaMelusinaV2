#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Pawn.h"
#include "MelodiaStarskiffPawn.generated.h"

class UFloatingPawnMovement;

/**
 * Canonical player-controlled Starskiff authority. The existing BP shell owns
 * authored hull/buoyancy presentation; this class owns boarding, movement and
 * capability-gated travel so a chapter cannot invent a second boat path.
 */
UCLASS(Blueprintable)
class BS_GODFILE_API AMelodiaStarskiffPawn : public APawn
{
	GENERATED_BODY()

public:
	AMelodiaStarskiffPawn();

	virtual void BeginPlay() override;
	virtual void SetupPlayerInputComponent(UInputComponent* PlayerInputComponent) override;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Starskiff|Traversal")
	FName RequiredCapabilityId = TEXT("capability.melodia.sail");

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Starskiff|Traversal")
	FName TraversalCapabilityContextId = TEXT("active_traversal_context");

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Starskiff|Traversal")
	float BoardingRadius = 400.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Starskiff|Traversal")
	FName DefaultDestinationMap = TEXT("/Game/ZenForestTest");

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Starskiff|Traversal")
	FName DefaultDestinationSpawnTag = NAME_None;

	/**
	 * When this narrative flag turns true, the nearest player boards. The dock QSC sets it as
	 * its last line, after its reward has equipped the Sail form. None disables.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Starskiff|Traversal")
	FName BoardOnFlagId = TEXT("flag.sea_above.starskiff_ready");

	UFUNCTION(BlueprintPure, Category="Melodia|Starskiff|Traversal")
	bool IsBoarded() const { return bBoarded; }

	UFUNCTION(BlueprintPure, Category="Melodia|Starskiff|Traversal")
	bool CanBoard(AActor* InteractingActor, FName& OutBlockReason) const;

	UFUNCTION(BlueprintCallable, Category="Melodia|Starskiff|Traversal")
	bool TryBoard(AActor* InteractingActor);

	/** Interaction seam used by the player controller when this skiff is nearest. */
	UFUNCTION(BlueprintCallable, Category="Melodia|Starskiff|Traversal")
	bool TryBoardNearestPlayer();

	UFUNCTION(BlueprintCallable, Category="Melodia|Starskiff|Traversal")
	void Disembark();

	UFUNCTION(BlueprintCallable, Category="Melodia|Starskiff|Traversal")
	bool RequestBoatTraversal(FName DestinationMap = NAME_None, FName DestinationSpawnTag = NAME_None);

private:
	UFUNCTION()
	void HandleFlagChanged(FName FlagId, bool bValue);

	void MoveForward(float Value);
	void MoveRight(float Value);

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Melodia|Starskiff|Movement", meta=(AllowPrivateAccess="true"))
	TObjectPtr<UFloatingPawnMovement> Movement;

	TWeakObjectPtr<APawn> BoardedPawn;
	bool bBoarded = false;
};
