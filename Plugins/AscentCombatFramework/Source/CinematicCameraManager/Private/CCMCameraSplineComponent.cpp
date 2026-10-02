// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 


#include "CCMCameraSplineComponent.h"
#include "CCMLookAtPointComponent.h"
#include <GameFramework/Actor.h>


AActor* UCCMCameraSplineComponent::GetSequenceLookAtPointLocation() const
{
	return GetLookAtPointLocationByName(SequenceSettings.LookAtPoint);
}

AActor* UCCMCameraSplineComponent::GetLookAtPointLocationByName(const FName& lookAtPointName) const
{
	TArray< UCCMLookAtPointComponent*> lookAtPoints;
	GetOwner()->GetComponents<UCCMLookAtPointComponent>(lookAtPoints, true);

	for (auto point : lookAtPoints) {
		if (point->GetPointName() == lookAtPointName) {
			return (AActor*)(point->GetTargetPoint());
		}
	}

	return GetOwner();
}
