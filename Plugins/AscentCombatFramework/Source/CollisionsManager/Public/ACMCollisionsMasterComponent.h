// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 

#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "ACMCollisionsMasterComponent.generated.h"


/**
 * Component responsible for coordinating all ACMCollisionManagerComponent instances
 * Acts as a master controller to centralize damage collision
 */
UCLASS(ClassGroup = (ACF), meta = (BlueprintSpawnableComponent))
class COLLISIONSMANAGER_API UACMCollisionsMasterComponent : public UActorComponent
{
	GENERATED_BODY()

public:	
	/** Default constructor */
	UACMCollisionsMasterComponent();

protected:
	/** Called when the game starts */
	virtual void BeginPlay() override;

public:	
	/** Called every frame */
	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

	/**
	 * Registers a collision manager component under this master.
	 * @param compToAdd	The collision manager component to add.
	 */
	void AddComponent(class UACMCollisionManagerComponent* compToAdd);

	/**
	 * Unregisters a collision manager component from this master.
	 * @param compToAdd	The collision manager component to remove.
	 */
	void RemoveComponent(class UACMCollisionManagerComponent* compToAdd);

private:

	UPROPERTY()
	TArray<TObjectPtr<UACMCollisionManagerComponent>> currentlyActiveComponents;

	UPROPERTY()
	TArray<TObjectPtr< UACMCollisionManagerComponent>> pendingDelete;
};
