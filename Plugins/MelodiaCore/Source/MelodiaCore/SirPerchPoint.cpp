#include "SirPerchPoint.h"

#include "Components/SceneComponent.h"
#include "Components/StaticMeshComponent.h"

ASirPerchPoint::ASirPerchPoint()
{
	PrimaryActorTick.bCanEverTick = false;

	USceneComponent* SceneRoot = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
	SetRootComponent(SceneRoot);

	Glint = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Glint"));
	Glint->SetupAttachment(SceneRoot);
	// No mesh is assigned: the cue is authored in the BP child, and an empty
	// component must not render or collide in the meantime.
	Glint->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Glint->SetVisibility(false);
	Glint->SetHiddenInGame(true);
}

FVector ASirPerchPoint::GetLandingLocation() const
{
	return GetActorLocation() + GetActorTransform().TransformVectorNoScale(LandingOffset);
}

FRotator ASirPerchPoint::GetLandingRotation() const
{
	return bFaceAlongPerch ? GetActorRotation() + PerchFacing : FRotator::ZeroRotator;
}
