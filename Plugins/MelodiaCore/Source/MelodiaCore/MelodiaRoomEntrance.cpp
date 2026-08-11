#include "MelodiaRoomEntrance.h"

#include "Components/SceneComponent.h"

AMelodiaRoomEntrance::AMelodiaRoomEntrance()
{
	PrimaryActorTick.bCanEverTick = false;
	ArrivalTransform = CreateDefaultSubobject<USceneComponent>(TEXT("ArrivalTransform"));
	SetRootComponent(ArrivalTransform);
}
