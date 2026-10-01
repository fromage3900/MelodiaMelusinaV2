// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 


#include "ACMCollisionsMasterComponent.h"
#include "ACMCollisionManagerComponent.h"

// Sets default values for this component's properties
UACMCollisionsMasterComponent::UACMCollisionsMasterComponent()
{
	// Set this component to be initialized when the game starts, and to be ticked every frame.  You can turn these features
	// off to improve performance if you don't need them.
	PrimaryComponentTick.bCanEverTick = true;

	// ...
}


// Called when the game starts
void UACMCollisionsMasterComponent::BeginPlay()
{
	Super::BeginPlay();

	// ...
	
}


// Called every frame
void UACMCollisionsMasterComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);
	for (UACMCollisionManagerComponent* del : pendingDelete) {
		currentlyActiveComponents.Remove(del);
	}

	pendingDelete.Empty();

	for (UACMCollisionManagerComponent* comp : currentlyActiveComponents) {
		if (IsValid(comp) &&  IsValid(comp->GetOwner())  ) {
			comp->UpdateCollisions();
		}
		else {
			pendingDelete.Add(comp);
		}
	}
}

void UACMCollisionsMasterComponent::AddComponent(class UACMCollisionManagerComponent* compToAdd)
{
	currentlyActiveComponents.AddUnique(compToAdd);
	if (pendingDelete.Contains(compToAdd)) {
		pendingDelete.Remove(compToAdd);
	}
}

void UACMCollisionsMasterComponent::RemoveComponent(class UACMCollisionManagerComponent* compToAdd)
{
	if (currentlyActiveComponents.Contains(compToAdd)) {
		pendingDelete.Add(compToAdd);
	}
}

