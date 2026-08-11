// Copyright Epic Games, Inc. All Rights Reserved.

#include "MelodiaMapTransitionComponent.h"
#include "Engine/World.h"
#include "TimerManager.h"
#include "Kismet/GameplayStatics.h"
#include "Components/BoxComponent.h"
#include "GameFramework/Character.h"
#include "MelodiaInputContextSubsystem.h"
#include "MelodiaTravelSubsystem.h"

UMelodiaMapTransitionComponent::UMelodiaMapTransitionComponent()
{
	PrimaryComponentTick.bCanEverTick = false;
	bAutoTransition = false;
}

void UMelodiaMapTransitionComponent::BeginPlay()
{
	Super::BeginPlay();

	// If auto-transition is enabled, set up overlap detection
	if (bAutoTransition)
	{
		if (UBoxComponent* BoxComp = GetOwner()->FindComponentByClass<UBoxComponent>())
		{
			BoxComp->OnComponentBeginOverlap.AddDynamic(this, &UMelodiaMapTransitionComponent::OnOverlapBegin);
		}
	}
}

void UMelodiaMapTransitionComponent::TransitionToMap(const FString& MapName)
{
	if (MapName.IsEmpty())
	{
		return;
	}

	// Routes through the single travel authority (Decision 023) rather than
	// travelling directly. That buys allowlist validation and arrival placement for
	// every overlap volume in the game without each one reimplementing them.
	//
	// This previously called LoadStreamLevel, which streams a sublevel into the
	// current world and cannot work for a standalone map -- it silently did nothing.
	if (UMelodiaTravelSubsystem* Travel = UMelodiaTravelSubsystem::Get(this))
	{
		Travel->TravelTo(FName(*MapName), TargetSpawnTag);
		return;
	}

	UE_LOG(LogTemp, Warning,
		TEXT("MelodiaMapTransitionComponent: travel subsystem unavailable; '%s' not entered."),
		*MapName);
}

void UMelodiaMapTransitionComponent::SetTargetMap(const FString& MapName)
{
	TargetMapName = MapName;
}

void UMelodiaMapTransitionComponent::OnOverlapBegin(UPrimitiveComponent* OverlappedComp, AActor* OtherActor,
	UPrimitiveComponent* OtherComp, int32 OtherBodyIndex, bool bFromSweep, const FHitResult& SweepResult)
{
	if (!Cast<ACharacter>(OtherActor) || TargetMapName.IsEmpty() || PendingTransitionActor.IsValid())
	{
		return;
	}

	PendingTransitionActor = OtherActor;
	if (UWorld* World = GetWorld())
	{
		// Defer one frame. A Quill trigger entered by this same overlap gets the
		// opportunity to push Dialogue before automatic travel is considered.
		World->GetTimerManager().SetTimerForNextTick(this, &ThisClass::AttemptPendingAutoTransition);
	}
}

void UMelodiaMapTransitionComponent::AttemptPendingAutoTransition()
{
	AActor* TransitionActor = PendingTransitionActor.Get();
	UBoxComponent* BoxComp = GetOwner() ? GetOwner()->FindComponentByClass<UBoxComponent>() : nullptr;
	if (!TransitionActor || !BoxComp || !BoxComp->IsOverlappingActor(TransitionActor))
	{
		PendingTransitionActor.Reset();
		return;
	}

	const UMelodiaInputContextSubsystem* Input = UMelodiaInputContextSubsystem::Get(this);
	if (Input && !Input->IsMovementAllowed())
	{
		if (UWorld* World = GetWorld())
		{
			World->GetTimerManager().SetTimer(
				PendingTransitionTimer,
				this,
				&ThisClass::AttemptPendingAutoTransition,
				BlockedTransitionRetryDelay,
				false);
		}
		return;
	}

	PendingTransitionActor.Reset();
	TransitionToMap(TargetMapName);
}