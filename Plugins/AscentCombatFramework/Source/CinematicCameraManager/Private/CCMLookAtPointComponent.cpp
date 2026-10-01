// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 


#include "CCMLookAtPointComponent.h"
#include <Engine/TargetPoint.h>
#include <Engine/World.h>

// Sets default values for this component's properties
UCCMLookAtPointComponent::UCCMLookAtPointComponent()
{
	// Set this component to be initialized when the game starts, and to be ticked every frame.  You can turn these features
	// off to improve performance if you don't need them.
	PrimaryComponentTick.bCanEverTick = false;

}



ATargetPoint* UCCMLookAtPointComponent::GetTargetPoint()
{
	if (!targetPoint) {
		FActorSpawnParameters spawnParam;
		spawnParam.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
		targetPoint = GetWorld()->SpawnActor<ATargetPoint>(GetComponentLocation(), GetComponentRotation(), spawnParam);
		targetPoint->AttachToComponent(this, FAttachmentTransformRules::SnapToTargetNotIncludingScale);
	}

	return targetPoint;
}




