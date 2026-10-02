// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 


#include "Components/ACFRagdollMasterComponent.h"
#include "Components/ACFRagdollComponent.h"

// Sets default values for this component's properties
UACFRagdollMasterComponent::UACFRagdollMasterComponent()
{
	// Set this component to be initialized when the game starts, and to be ticked every frame.  You can turn these features
	// off to improve performance if you don't need them.
	PrimaryComponentTick.bCanEverTick = true;

	// ...
}


// Called when the game starts
void UACFRagdollMasterComponent::BeginPlay()
{
	Super::BeginPlay();

	// ...
	
}


// Called every frame
void UACFRagdollMasterComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

	for (auto del : pendingDelete) {
		currentlyActiveComponents.Remove(del);
	}

	pendingDelete.Empty();

	for (auto comp : currentlyActiveComponents) {
		if (IsValid(comp)) {
			comp->UpdateOwnerLocation();
		}
		else {
			pendingDelete.Add(comp);
		}
	}
}

void UACFRagdollMasterComponent::AddComponent(class UACFRagdollComponent* compToAdd)
{
	currentlyActiveComponents.AddUnique(compToAdd);
	if (pendingDelete.Contains(compToAdd)) {
		pendingDelete.Remove(compToAdd);
	}
}

void UACFRagdollMasterComponent::RemoveComponent(class UACFRagdollComponent* compToAdd)
{
	if (currentlyActiveComponents.Contains(compToAdd)) {
		pendingDelete.Add(compToAdd);
	}
}

