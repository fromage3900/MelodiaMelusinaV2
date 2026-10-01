// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "Data/ACFComponentsFragment.h"
#include "GameFramework/Pawn.h"
#include "Components/ActorComponent.h"

void UACFComponentsFragment::ApplyFragment_Implementation(APawn* pawnOwner)
{
	if (!pawnOwner) {
		return;
	}

	for (const TSubclassOf<UActorComponent>& CompClass : ComponentsToAdd)
	{
		if (!CompClass) {
			continue;
		}

		// Skip if a component of the same class is already attached.
		// Safe to call on both server and client — each machine adds its own instance.
		if (pawnOwner->FindComponentByClass(CompClass)) {
			continue;
		}

		UActorComponent* NewComp = NewObject<UActorComponent>(pawnOwner, CompClass);
		if (!NewComp) {
			continue;
		}

		// AddInstanceComponent registers the component in the actor's instance component
		// list so the editor, serialisation and component iterators all see it correctly.
		// RegisterComponent finalises attachment and calls BeginPlay if the world has started.
		pawnOwner->AddInstanceComponent(NewComp);
		NewComp->RegisterComponent();

		// If the component class opts into replication (bReplicates == true in its CDO),
		// register it with the actor's replicated subobject list so its UPROPERTY(Replicated)
		// fields reach all clients.  The component's presence on each machine is already
		// guaranteed because ApplyFragmentsData() runs on both server and client; this step
		// only covers property-level replication inside the component itself.
		if (NewComp->GetIsReplicated())
		{
			NewComp->SetIsReplicated(true);
			pawnOwner->AddReplicatedSubObject(NewComp);
		}
	}
}
