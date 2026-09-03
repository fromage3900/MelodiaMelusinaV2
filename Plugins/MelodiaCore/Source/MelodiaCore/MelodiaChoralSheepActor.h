#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "MelodiaCompanionData.h"
#include "MelodiaChoralSheepActor.generated.h"

class AActor;
class USceneComponent;
class USkeletalMeshComponent;
class USphereComponent;
class UMelodiaCompanionComponent;
class UMelodiaCompanionDefinitionAsset;

/**
 * Native, map-agnostic home for the Choral Sheep.
 *
 * The actor deliberately owns no rig, Groom, map reference, save authority,
 * or interaction-detector dependency. Its data asset supplies presentation;
 * a Blueprint subclass only needs to assign that asset after import.
 */
UCLASS(Blueprintable)
class MELODIACORE_API AMelodiaChoralSheepActor : public AActor
{
	GENERATED_BODY()

public:
	AMelodiaChoralSheepActor();

	virtual void PostInitializeComponents() override;
	virtual void BeginPlay() override;

	/** The one authored data asset that owns mesh, optional animation, and behavior identity. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|ChoralSheep")
	TSoftObjectPtr<UMelodiaCompanionDefinitionAsset> CompanionDefinition;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Melodia|ChoralSheep")
	TObjectPtr<USkeletalMeshComponent> SkeletalMeshComponent;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Melodia|ChoralSheep")
	TObjectPtr<UMelodiaCompanionComponent> CompanionComponent;

	/** Query-only radius. Existing interaction systems may call the explicit Try* methods below. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Melodia|ChoralSheep|Interaction")
	TObjectPtr<USphereComponent> InteractionRange;

	/** Keeps the actor usable in a simple standalone smoke without controller/map edits. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|ChoralSheep|Movement")
	bool bAutoFollowFirstPlayer = true;

	UFUNCTION(BlueprintCallable, Category="Melodia|ChoralSheep")
	bool ApplyChoralSheepDefinition();

	UFUNCTION(BlueprintCallable, Category="Melodia|ChoralSheep")
	bool SetChoralSheepDefinition(UMelodiaCompanionDefinitionAsset* InDefinition);

	UFUNCTION(BlueprintPure, Category="Melodia|ChoralSheep|Interaction")
	bool IsInteractorInRange(const AActor* Interactor) const;

	UFUNCTION(BlueprintCallable, Category="Melodia|ChoralSheep|Interaction")
	bool TryBeginGraze(AActor* Interactor);

	UFUNCTION(BlueprintCallable, Category="Melodia|ChoralSheep|Interaction")
	bool TryBeginHarmonize(AActor* Interactor);

	UFUNCTION(BlueprintCallable, Category="Melodia|ChoralSheep|Interaction")
	bool TryBeginGuide(AActor* Interactor, AActor* GuideTarget);

	UFUNCTION(BlueprintCallable, Category="Melodia|ChoralSheep|Interaction")
	void EndCompanionInteraction();

private:
	EMelodiaCompanionInteractionKind ActiveInteraction = EMelodiaCompanionInteractionKind::Harmonize;
};
