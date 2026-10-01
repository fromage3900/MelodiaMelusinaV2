// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ACFSplinePath.h"
#include "Components/SplineComponent.h"

AACFSplinePath::AACFSplinePath()
{
	PrimaryActorTick.bCanEverTick = false;
	SplineComp = CreateDefaultSubobject<USplineComponent>(TEXT("Spline Component"));
}

void AACFSplinePath::BeginPlay()
{
	Super::BeginPlay();
}

void AACFSplinePath::NotifyPointReached(int32 PointIndex, APawn* TraversingPawn)
{
	OnPointReached.Broadcast(PointIndex, TraversingPawn);
	HandlePointReached(PointIndex, TraversingPawn);
}

void AACFSplinePath::HandlePointReached_Implementation(int32 PointIndex, APawn* TraversingPawn)
{
	(void)PointIndex;
	(void)TraversingPawn;
}

void AACFSplinePath::AddSplinePoint(const FVector& worldPos)
{
	SplineComp->AddSplinePoint(worldPos, ESplineCoordinateSpace::World);
}

void AACFSplinePath::SetSplinePoints(const TArray<FVector>& worldPos)
{
	SplineComp->SetSplinePoints(worldPos, ESplineCoordinateSpace::World);
}
