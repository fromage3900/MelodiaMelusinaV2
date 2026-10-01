// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "Actors/ACFDestructable.h"
#include "ACFTeamManagerSubsystem.h"
#include "Components/ACFDamageHandlerComponent.h"
#include "GameFramework/DamageType.h"
#include "GeometryCollection/GeometryCollectionComponent.h"
#include "Kismet/KismetSystemLibrary.h"
#include <Engine/World.h>
#include <GameFramework/Pawn.h>
#include <TimerManager.h>
#include "Engine/DamageEvents.h"

AACFDestructable::AACFDestructable()
{
	PrimaryActorTick.bCanEverTick = false;


	GeometryCollectionComp = CreateDefaultSubobject<UGeometryCollectionComponent>(TEXT("GeometryCollection"));
	GeometryCollectionComp->SetupAttachment(RootComp);
	GeometryCollectionComp->SetUsingAbsoluteLocation(false);
	GeometryCollectionComp->SetUsingAbsoluteRotation(false);
	GeometryCollectionComp->SetUsingAbsoluteScale(false);
}

void AACFDestructable::BeginPlay()
{
	Super::BeginPlay();
	RootComp->SetCollisionEnabled(ECollisionEnabled::NoCollision);

	if (DamageHandlerComp) {
		DamageHandlerComp->OnOwnerDeath.AddDynamic(this, &AACFDestructable::HandleDestructableDeath);
	}

	if (bDestroyOnFirstHostileHit && UKismetSystemLibrary::IsServer(this) && DamageHandlerComp) {
		DamageHandlerComp->OnDamageReceived.AddDynamic(this, &AACFDestructable::HandleDamageForFirstHitDestroy);
	}
}

void AACFDestructable::HandleDestructableDeath()
{
	if (!HasAuthority() || !DamageHandlerComp) {
		return;
	}

	const FACFDamageEvent Last = DamageHandlerComp->GetLastDamageInfo();
	FVector StrainLoc = Last.hitResult.ImpactPoint;
	if (StrainLoc.IsNearlyZero()) {
		StrainLoc = GetActorLocation();
	}

	FVector ImpulseDir = Last.hitDirection.GetSafeNormal();
	if (ImpulseDir.IsNearlyZero()) {
		ImpulseDir = FallbackBreakImpulse.GetSafeNormal();
		if (ImpulseDir.IsNearlyZero()) {
			ImpulseDir = FVector::UpVector;
		}
	}

	Multicast_PlayDestruction(StrainLoc, ImpulseDir);
}

void AACFDestructable::HandleDamageForFirstHitDestroy(const FACFDamageEvent& DamageEvent)
{
	if (!bDestroyOnFirstHostileHit || !HasAuthority() || bFirstHitKillFlushPending) {
		return;
	}
	if (!DamageHandlerComp || !DamageHandlerComp->GetIsAlive()) {
		return;
	}

	if (!DamageEvent.DamageDealer) {
		return;
	}

	if (UWorld* World = GetWorld()) {
		if (const UACFTeamManagerSubsystem* TeamSubsystem = World->GetSubsystem<UACFTeamManagerSubsystem>()) {
			if (!TeamSubsystem->CanActorDamageActor(DamageEvent.DamageDealer, this)) {
				return;
			}
		}
	}

	ServerTryFinishOnFirstHit(DamageEvent);
}

void AACFDestructable::ServerTryFinishOnFirstHit(const FACFDamageEvent& DamageEvent)
{
	bFirstHitKillFlushPending = true;
	PendingFirstHitKillEvent = DamageEvent;

	if (UWorld* World = GetWorld()) {
		World->GetTimerManager().SetTimerForNextTick(FTimerDelegate::CreateUObject(this, &AACFDestructable::DeferredApplyFirstHitKill));
	}
}

void AACFDestructable::DeferredApplyFirstHitKill()
{
	bFirstHitKillFlushPending = false;
	if (!DamageHandlerComp || !DamageHandlerComp->GetIsAlive()) {
		return;
	}

	FDamageEvent GenericEvent;
	if (PendingFirstHitKillEvent.DamageClass) {
		GenericEvent.DamageTypeClass = PendingFirstHitKillEvent.DamageClass;
	}
	else {
		GenericEvent.DamageTypeClass = TSubclassOf<UDamageType>(UDamageType::StaticClass());
	}

	AController* InstigatorController = nullptr;
	if (const APawn* DealerPawn = Cast<APawn>(PendingFirstHitKillEvent.DamageDealer)) {
		InstigatorController = DealerPawn->GetController();
	}

	DamageHandlerComp->TakeDamage(this, FirstHitFinisherDamage, GenericEvent, InstigatorController, PendingFirstHitKillEvent.DamageDealer);
}

void AACFDestructable::Multicast_PlayDestruction_Implementation(FVector StrainWorldLocation, FVector ImpulseDirection)
{
	ApplyChaosDestructionAt(StrainWorldLocation, ImpulseDirection);
}

void AACFDestructable::ApplyChaosDestructionAt(FVector StrainWorldLocation, FVector ImpulseDirection)
{
	if (!GeometryCollectionComp || !GeometryCollectionComp->GetRestCollection()) {
		return;
	}

	const int32 RootIdx = GeometryCollectionComp->GetRootIndex();
	if (RootIdx == INDEX_NONE) {
		return;
	}
	ImpulseDirection = ImpulseDirection.GetSafeNormal();
	if (ImpulseDirection.IsNearlyZero()) {
		ImpulseDirection = FVector::UpVector;
	}

	GeometryCollectionComp->ApplyExternalStrain(RootIdx, StrainWorldLocation, ExternalStrainRadius, ExternalStrainPropagationDepth,
		ExternalStrainPropagationFactor, ExternalStrainMagnitude);

	GeometryCollectionComp->ApplyBreakingLinearVelocity(RootIdx, ImpulseDirection * BreakScatterImpulse);
}
