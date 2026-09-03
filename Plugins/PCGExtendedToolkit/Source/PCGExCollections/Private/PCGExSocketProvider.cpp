// Copyright 2026 Timothé Lapetite and contributors
// Released under the MIT license https://opensource.org/license/MIT/

#include "PCGExSocketProvider.h"

#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"

APCGExSocketActor::APCGExSocketActor()
{
	// Socket actors are editor-only design markers; never visible, active, or ticking at runtime.
	PrimaryActorTick.bCanEverTick = false;
	PrimaryActorTick.bStartWithTickEnabled = false;
	PrimaryActorTick.bAllowTickOnDedicatedServer = false;

	SetActorTickEnabled(false);
	SetActorHiddenInGame(true);
	SetActorEnableCollision(false);
	SetCanBeDamaged(false);

	bRelevantForLevelBounds = false;
	bRelevantForNetworkReplays = false;
	bReplicates = false;
	bNetLoadOnClient = false;

	MeshComponent = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Mesh"));
	RootComponent = MeshComponent;

	MeshComponent->PrimaryComponentTick.bCanEverTick = false;
	MeshComponent->PrimaryComponentTick.bStartWithTickEnabled = false;
	MeshComponent->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	MeshComponent->SetCastShadow(false);
	MeshComponent->SetGenerateOverlapEvents(false);
	MeshComponent->bReceivesDecals = false;
	MeshComponent->SetHiddenInGame(true);

	MeshComponent->SetStaticMesh(LoadObject<UStaticMesh>(
		nullptr, TEXT("/PCG/DebugObjects/PCG_AxisTripod.PCG_AxisTripod")));
}

void APCGExSocketActor::OnConstruction(const FTransform& Transform)
{
	Super::OnConstruction(Transform);
	CachedTransform = Transform;
}
