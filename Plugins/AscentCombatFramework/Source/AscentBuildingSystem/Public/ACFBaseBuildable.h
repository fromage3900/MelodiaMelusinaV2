// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "ACFBuildableInterface.h"
#include "ALSSavableInterface.h"
#include "CoreMinimal.h"
#include "Interfaces/ACFInteractableInterface.h"

#include "ACFBaseBuildable.generated.h"

class UACFBuildableEntityComponent;
class UACFBuildingSnapComponent;
class UACFBuildRecipe;
class UACFBuildingManagerComponent;
class APawn;

/**
 * @class AACFBaseBuildable
 * Base class for buildable objects
 */
UCLASS(Blueprintable)
class ASCENTBUILDINGSYSTEM_API AACFBaseBuildable : public AActor,
	public IACFBuildableInterface,
	public IACFInteractableInterface,
	public IALSSavableInterface {
	GENERATED_BODY()

public:
	AACFBaseBuildable();

	void BeginPlay() override;

	UFUNCTION(BlueprintCallable, Category = "ACF|Building")
	void Dismantle(APawn* Pawn);

	// IACFBuildableInterface implementation
	void OnPlaced_Implementation() override;
	void OnDismantled_Implementation() override;
	bool IsPlacementValid_Implementation(const FVector& Location, const FRotator& Rotation) override;
	UACFBuildableEntityComponent* GetBuildingSystemComponent() const override { return BuildableComp; }
	// End Interface

	/**
	 * Called when a pawn interacts with this object.
	 * @param Pawn The pawn that interacted.
	 * @param interactionType The type of interaction.
	 */

	virtual void OnInteractedByPawn_Implementation(class APawn* Pawn, const FString& interactionType = "") override;



	/**
	 * Called when a local interaction happens (client-side).
	 * @param Pawn The interacting pawn.
	 * @param interactionType The type of interaction.
	 */
	void OnLocalInteractedByPawn_Implementation(class APawn* Pawn, const FString& interactionType = "");

	/**
	 * Called when a pawn registers this item as interactable.
	 * @param Pawn The pawn that registered the interaction.
	 */
	virtual void OnInteractableRegisteredByPawn_Implementation(class APawn* Pawn) override;

	/**
	 * Called when a pawn unregisters this item as interactable.
	 * @param Pawn The pawn that unregistered the interaction.
	 */
	virtual void OnInteractableUnregisteredByPawn_Implementation(class APawn* Pawn) override;

	/**
	 * Determines if this item can be interacted with.
	 * @param Pawn The pawn attempting interaction.
	 * @return True if the item can be interacted with, false otherwise.
	 */
	virtual bool CanBeInteracted_Implementation(class APawn* Pawn) override;

	/**
	 * Retrieves the name of the interactable object.
	 * @return The interactable name as an FText.
	 */
	virtual FText GetInteractableName_Implementation() override;

	UACFBuildingManagerComponent* GetBuildableManager(APawn* Pawn) const;

protected:
	UPROPERTY(Category = ACF, EditAnywhere)
	TObjectPtr<UStaticMeshComponent> MeshComponent;

	UPROPERTY(Category = ACF, EditAnywhere)
	TObjectPtr<USceneComponent> Root;

	UPROPERTY(Category = ACF, EditAnywhere)
	TObjectPtr<UACFBuildableEntityComponent> BuildableComp;

	UPROPERTY(Category = ACF, EditAnywhere)
	TObjectPtr<UACFBuildingSnapComponent> SnapComponent;

	FVector LastLocation;
};
