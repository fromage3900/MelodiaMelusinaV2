// Copyright Benoit Pelletier 2019 - 2026 All Rights Reserved.
//
// This software is available under different licenses depending on the source from which it was obtained:
// - The Fab EULA (https://fab.com/eula) applies when obtained from the Fab marketplace.
// - The CeCILL-C license (https://cecill.info/licences/Licence_CeCILL-C_V1-en.html) applies when obtained from any other source.
// Please refer to the accompanying LICENSE file for further details.

#include "Door.h"
#include "DoorType.h"
#include "ProceduralDungeonLog.h"
#include "Components/DoorComponent.h"

ADoor::ADoor()
{
	PrimaryActorTick.bCanEverTick = true;
	bReplicates = true;
	bAlwaysRelevant = true; // prevent the doors from despawning on clients when server's player is too far
	NetDormancy = ENetDormancy::DORM_DormantAll;

	DefaultSceneComponent = CreateDefaultSubobject<USceneComponent>(TEXT("SceneComponent"));
	RootComponent = DefaultSceneComponent;

	DoorComponent = CreateDefaultSubobject<UDoorComponent>(TEXT("DoorComponent"));
}

void ADoor::PostInitializeComponents()
{
	Super::PostInitializeComponents();

	if (!IsValid(DoorComponent))
		return;

	// Forward the component events to the actor events for retro-compatibility
	DoorComponent->OnDoorLocked.AddDynamic(this, &ADoor::DispatchDoorLock);
	DoorComponent->OnDoorOpened.AddDynamic(this, &ADoor::DispatchDoorOpen);
}

bool ADoor::IsLocked() const
{
	if (!IsValid(DoorComponent))
		return false;

	return DoorComponent->IsLocked();
}

bool ADoor::IsOpen() const
{
	if (!IsValid(DoorComponent))
		return false;

	return DoorComponent->IsOpen();
}

void ADoor::Open(bool bOpen)
{
	if (!IsValid(DoorComponent))
		return;

	DoorComponent->Open(bOpen);
}

void ADoor::Lock(bool bLock)
{
	if (!IsValid(DoorComponent))
		return;

	DoorComponent->Lock(bLock);
}

bool ADoor::ShouldBeOpened() const
{
	if (!IsValid(DoorComponent))
		return false;

	return DoorComponent->ShouldBeOpen();
}

bool ADoor::ShouldBeLocked() const
{
	if (!IsValid(DoorComponent))
		return false;

	return DoorComponent->ShouldBeLocked();
}

const UDoorType* ADoor::GetDoorType() const
{
	if (!IsValid(DoorComponent))
		return nullptr;

	return DoorComponent->GetDoorType();
}

URoom* ADoor::GetRoomA() const
{
	if (!IsValid(DoorComponent))
		return nullptr;

	return DoorComponent->GetRoomA();
}

URoom* ADoor::GetRoomB() const
{
	if (!IsValid(DoorComponent))
		return nullptr;

	return DoorComponent->GetRoomB();
}

void ADoor::DispatchDoorLock(UDoorComponent* Component, bool IsLocked)
{
	if (IsLocked)
	{
		OnDoorLock();
		OnDoorLock_BP();
	}
	else
	{
		OnDoorUnlock();
		OnDoorUnlock_BP();
	}
}

void ADoor::DispatchDoorOpen(UDoorComponent* Component, bool IsOpened)
{
	if (IsOpened)
	{
		OnDoorOpen();
		OnDoorOpen_BP();
	}
	else
	{
		OnDoorClose();
		OnDoorClose_BP();
	}
}

bool ADoor::GetAlwaysVisible() const
{
	if (!IsValid(DoorComponent))
		return false;

	return DoorComponent->IsAlwaysVisible();
}

bool ADoor::GetAlwaysUnlocked() const
{
	if (!IsValid(DoorComponent))
		return false;

	return DoorComponent->IsAlwaysUnlocked();
}

void ADoor::SetAlwaysVisible(bool bInAlwaysVisible)
{
	if (!IsValid(DoorComponent))
		return;

	DoorComponent->SetAlwaysVisible(bInAlwaysVisible);
}

void ADoor::SetAlwaysUnlocked(bool bInAlwaysUnlocked)
{
	if (!IsValid(DoorComponent))
		return;

	DoorComponent->SetAlwaysUnlocked(bInAlwaysUnlocked);
}
