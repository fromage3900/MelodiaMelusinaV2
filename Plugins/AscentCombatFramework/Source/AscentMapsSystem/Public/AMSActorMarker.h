// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "AMSActorMarker.generated.h"

/**
 * Simple actor marker used to pin a point on the map.
 * Can be placed in the world and will show up on the in-game map via its MarkerComp.
 */
UCLASS()
class ASCENTMAPSSYSTEM_API AAMSActorMarker : public AActor
{
	GENERATED_BODY()
	
public:	
	// Sets default values for this actor's properties
	AAMSActorMarker();

protected:
	// Called when the game starts or when spawned
	virtual void BeginPlay() override;

	// Component that handles display and logic for this marker on the map
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = ACF)
	TObjectPtr<class UAMSMapMarkerComponent> MarkerComp;

};
