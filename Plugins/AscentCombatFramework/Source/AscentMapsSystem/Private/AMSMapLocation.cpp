// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "AMSMapLocation.h"
#include "AMSMapMarkerComponent.h"
#include "Components/SphereComponent.h"
#include "Kismet/GameplayStatics.h"
#include <GameFramework/Pawn.h>
#include "AMSMapSubsystem.h"
#include <Engine/GameInstance.h>

// Sets default values
AAMSMapLocation::AAMSMapLocation()
{
	// Set this actor to call Tick() every frame.  You can turn this off to improve performance if you don't need it.
	PrimaryActorTick.bCanEverTick = false;
	SphereComp = CreateDefaultSubobject<USphereComponent>(TEXT("Discover Area"));
	MarkerComp = CreateDefaultSubobject<UAMSMapMarkerComponent>(TEXT("Marker Componenr"));
	SphereComp->SetSphereRadius(2000.f);
}

FString AAMSMapLocation::GetLocationID() const
{
	return GetMarkerComponent()->GetMarkerID();
}

FText AAMSMapLocation::GetLocationUIName() const
{
	return GetMarkerComponent()->GetMarkerName();
}


void AAMSMapLocation::SetLocationUIName(const FText& newName)
{
	GetMarkerComponent()->SetMarkerName(newName);
}

void AAMSMapLocation::SetLocationID(const FString& newName)
{
	GetMarkerComponent()->SetMarkerID(newName);
}

void AAMSMapLocation::SetDiscoveredState(bool newState)
{
	bDiscovered = newState;
	if (bDiscovered) {
		MarkerComp->AddMarker();
	}
	else {
		MarkerComp->RemoveMarker();
	}
}

// Called when the game starts or when spawned
void AAMSMapLocation::BeginPlay()
{
	Super::BeginPlay();

	SphereComp->OnComponentBeginOverlap.AddDynamic(this, &AAMSMapLocation::HandleLocalPlayerOverlap);
	SphereComp->OnComponentEndOverlap.AddDynamic(this, &AAMSMapLocation::HandleOverlapEnds);
	if (IsDiscovered()) {
		MarkerComp->AddMarker();
	}
}

void AAMSMapLocation::OnDiscovered_Implementation(const APawn* pawn)
{
}

void AAMSMapLocation::HandleLocalPlayerOverlap(UPrimitiveComponent* OverlappedComponent, AActor* OtherActor, UPrimitiveComponent* OtherComp, int32 OtherBodyIndex, bool bFromSweep, const FHitResult& SweepResult)
{
	if (UGameplayStatics::GetPlayerPawn(this, 0) == OtherActor) {
		if (!IsDiscovered()) {
			DiscoverLocation(Cast<APawn>(OtherActor));
		}
		MarkerComp->RemoveMarker();
	}

}

void AAMSMapLocation::HandleOverlapEnds(UPrimitiveComponent* OnComponentEndOverlap, AActor* OtherActor, UPrimitiveComponent* OtherComp, int32 OtherBodyIndex)
{
	if (IsDiscovered()) {
		MarkerComp->AddMarker();
	}
}

void AAMSMapLocation::DiscoverLocation(const APawn* pawn)
{
	if (IsDiscovered()) {
		return;
	}
	SetDiscoveredState(true);
	OnDiscovered(pawn);

	UGameInstance* GameInstance = UGameplayStatics::GetGameInstance(this);
	UAMSMapSubsystem* mapSubsystem = GameInstance->GetSubsystem<UAMSMapSubsystem>();
	if (mapSubsystem) {
		mapSubsystem->OnLocationDiscovered.Broadcast(this);
	}
	OnDiscoveredEvent.Broadcast();
}

void AAMSMapLocation::OnTeleported_Implementation()
{
	APawn* currentPawn = UGameplayStatics::GetPlayerPawn(this, 0);
	if (currentPawn) {
		FHitResult outRes;
		currentPawn->SetActorLocation(GetFastTravelPoint(), false, &outRes, ETeleportType::TeleportPhysics);
	}
}

bool AAMSMapLocation::CanFastTravel_Implementation() const
{
	return bCanFastTravel;
}

void AAMSMapLocation::FastTraverlToLocation()
{
	if (CanFastTravel()) {
		OnTeleported();
		OnFastTravelEvent.Broadcast();
	}
}

FVector AAMSMapLocation::GetFastTravelPoint() const
{
	return GetActorLocation() + FastTravelLocation;
}
