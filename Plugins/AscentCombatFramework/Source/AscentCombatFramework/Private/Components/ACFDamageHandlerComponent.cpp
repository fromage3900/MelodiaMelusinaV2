// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "Components/ACFDamageHandlerComponent.h"
#include "ACFActionsFunctionLibrary.h"
#include "ACFLegacyStatisticsComponent.h"
#include "ARSLevelingComponent.h"
#include "ARSStatisticsComponent.h"
#include "ARSTypes.h"
#include "AbilitySystemComponent.h"
#include "Actors/ACFCharacter.h"
#include "Components/ACFTeamManagerComponent.h"
#include "Engine/DamageEvents.h"
#include "Engine/World.h"
#include "Game/ACFDamageType.h"
#include "Game/ACFGASDamageCalculator.h"
#include "Game/ACFFunctionLibrary.h"
#include "Net/UnrealNetwork.h"
#include <Components/MeshComponent.h>
#include <Engine/EngineTypes.h>
#include <GameFramework/Actor.h>
#include <GameFramework/Controller.h>
#include <GameFramework/DamageType.h>
#include <GameplayEffectTypes.h>
#include <Kismet/KismetSystemLibrary.h>
#include <Logging.h>
#include <PhysicsEngine/BodyInstance.h>

// Sets default values for this component's properties
UACFDamageHandlerComponent::UACFDamageHandlerComponent()
{
	// Set this component to be initialized when the game starts, and to be ticked every frame.  You can turn these features
	// off to improve performance if you don't need them.
	PrimaryComponentTick.bCanEverTick = false;
	SetIsReplicatedByDefault(true);
	bIsAlive = true;
	DamageCalculatorClass = UACFGASDamageCalculator::StaticClass();
	bIsImmortal = false;
}



void UACFDamageHandlerComponent::BeginPlay()
{
	Super::BeginPlay();

	UARSStatisticsComponent* StatisticsComp = GetOwner()->FindComponentByClass<UARSStatisticsComponent>();
	if (StatisticsComp && !StatisticsComp->OnHealthReachesZero.IsAlreadyBound(this, &UACFDamageHandlerComponent::HandleStatReachedZero)) {

		StatisticsComp->OnHealthReachesZero.AddDynamic(this, &UACFDamageHandlerComponent::HandleStatReachedZero);
	}
}

float UACFDamageHandlerComponent::TakePointDamage(float Damage, const class UDamageType* DamageType, FVector HitLocation,
	FVector HitNormal, class UPrimitiveComponent* HitComponent, FName BoneName, FVector ShotFromDirection,
	class AController* InstigatedBy, AActor* DamageCauser, const FHitResult& HitInfo)
{
	FPointDamageEvent newEvent = FPointDamageEvent(Damage, HitInfo, ShotFromDirection, DamageType->GetClass());
	return TakeDamage(GetOwner(), Damage, newEvent, InstigatedBy, DamageCauser);
}

float UACFDamageHandlerComponent::TakeDamage(class AActor* damageReceiver, float Damage, FDamageEvent const& DamageEvent, AController* EventInstigator, AActor* DamageCauser)
{
	if (!GetIsAlive()) {
		return 0.f;
	}

	if (GetIsImmortal()) {
		// Damage types with bAffectedByImmortality == false (e.g. poison DoT) bypass immortality
		// and are always applied. Non-ACF damage types and types with bAffectedByImmortality == true
		// are blocked while the target is immortal (e.g. during a dodge-roll i-frame window).
		const UACFDamageType* acfDamageType = nullptr;
		if (DamageEvent.DamageTypeClass) {
			acfDamageType = Cast<UACFDamageType>(DamageEvent.DamageTypeClass->GetDefaultObject());
		}
		if (!acfDamageType || acfDamageType->bAffectedByImmortality) {
			return 0.f;
		}
	}

	if (!damageReceiver) {
		return Damage;
	}


	FHitResult outDamage;
	FVector ShotDirection;
	DamageEvent.GetBestHitInfo(damageReceiver, DamageCauser, outDamage, ShotDirection);
	FACFDamageEvent outDamageEvent;
	ConstructDamageReceived(damageReceiver, Damage, EventInstigator, outDamage.Location, outDamage.Component.Get(), outDamage.BoneName, ShotDirection, DamageEvent.DamageTypeClass,
		DamageCauser);


	if (GetIsImmortal()) {
		const UACFAbilitySystemComponent* abilitySystem = GetOwner()->GetComponentByClass<UACFAbilitySystemComponent>();

		FGameplayTag currentActionTag;
		if (abilitySystem) {
			currentActionTag = abilitySystem->GetCurrentActionTag();
		}
		OnDamageAvoided.Broadcast(currentActionTag);
		return 0.f;
	}
	else {
		UARSStatisticsComponent* StatisticsComp = damageReceiver->FindComponentByClass<UARSStatisticsComponent>();
		TArray<FStatisticValue> damages;
		for (const auto& damageData : LastDamageReceived.AttributesData) {
			FStatisticValue statMod(damageData.AttributeData, damageData.Value);
			damages.Add(statMod);
		}
		if (StatisticsComp) {
			FStatisticValue statMod(UACFFunctionLibrary::GetHealthTag(), LastDamageReceived.FinalDamage);
			damages.Add(statMod);
		}
		StatisticsComp->ConsumeStatistics(damages);
	}

	OnRep_LastDamageReceived();
	return LastDamageReceived.FinalDamage;
}

void UACFDamageHandlerComponent::Revive_Implementation()
{
	bIsAlive = true;
	UARSStatisticsComponent* StatisticsComp = GetOwner()->FindComponentByClass<UARSStatisticsComponent>();
	if (StatisticsComp) {
		StatisticsComp->OnRevive();
	}
}

FGameplayTag UACFDamageHandlerComponent::GetCombatTeam() const
{
	const bool bImplements = GetOwner()->GetClass()->ImplementsInterface(UACFEntityInterface::StaticClass());
	if (bImplements) {
		return IACFEntityInterface::Execute_GetEntityCombatTeam(GetOwner());
	}
	return FGameplayTag();
}

void UACFDamageHandlerComponent::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
	Super::GetLifetimeReplicatedProps(OutLifetimeProps);

	DOREPLIFETIME(UACFDamageHandlerComponent, bIsAlive);
}

void UACFDamageHandlerComponent::ConstructDamageReceived(AActor* DamagedActor, float Damage, class AController* InstigatedBy, FVector HitLocation,
	class UPrimitiveComponent* FHitComponent, FName BoneName, FVector ShotFromDirection, TSubclassOf<UDamageType> DamageType,
	AActor* DamageCauser)
{

	FACFDamageEvent tempDamageEvent;
	tempDamageEvent.contextString = NAME_None;
	tempDamageEvent.FinalDamage = Damage;
	tempDamageEvent.hitDirection = ShotFromDirection;
	tempDamageEvent.hitResult.BoneName = BoneName;
	tempDamageEvent.hitResult.ImpactPoint = HitLocation;
	tempDamageEvent.hitResult.Location = HitLocation;
	tempDamageEvent.hitResult.HitObjectHandle = FActorInstanceHandle(DamagedActor);
	tempDamageEvent.DamageReceiver = DamagedActor;
	tempDamageEvent.DamageClass = DamageType;

	// Extract damage tags from damage type class for easier access in abilities
	if (DamageType)
	{
		const UACFDamageType* ACFDamageType = Cast<UACFDamageType>(DamageType.GetDefaultObject());
		if (ACFDamageType)
		{
			tempDamageEvent.DamageTags = ACFDamageType->DamageTags;
		}
	}

	if (DamageCauser) {
		tempDamageEvent.DamageDealer = DamageCauser;
		tempDamageEvent.DamageDirection = UACFFunctionLibrary::GetHitDirectionByHitResult(tempDamageEvent.DamageDealer, tempDamageEvent.hitResult);
	}

	tempDamageEvent.HitResponseAction = FGameplayTag();

	AACFCharacter* acfReceiver = Cast<AACFCharacter>(DamagedActor);

	if (acfReceiver) {
		tempDamageEvent.DamageZone = acfReceiver->GetDamageZoneByBoneName(BoneName);
		FBodyInstance* bodyInstance = acfReceiver->GetMesh()->GetBodyInstance(BoneName);
		if (bodyInstance) {
			tempDamageEvent.PhysMaterial = bodyInstance->GetSimplePhysicalMaterial();
		}
	}

	if (DamageCalculatorClass) {
		if (!DamageCalculator) {
			DamageCalculator = NewObject<UACFDamageCalculation>(this, DamageCalculatorClass);
		}
		if (DamageCalculator) {

			tempDamageEvent.bIsCritical = DamageCalculator->IsCriticalDamage(tempDamageEvent);
			tempDamageEvent.HitResponseAction = DamageCalculator->EvaluateHitResponseAction(tempDamageEvent, HitResponseActions);
			tempDamageEvent.FinalDamage = DamageCalculator->CalculateFinalDamage(tempDamageEvent, tempDamageEvent.AttributesData);
		}

	}
	else {
		ensure(false);
		UE_LOG(ACFLog, Error, TEXT("MISSING DAMAGE CALCULATOR CLASS -  UACFDamageHandlerComponent"));
	}

	LastDamageReceived = tempDamageEvent;
}

void UACFDamageHandlerComponent::HandleStatReachedZero()
{
	// we can't die twice
	if (!bIsAlive) {
		return;
	}
	if (GetOwner()->HasAuthority()) {
		bIsAlive = false;
		if (LastDamageReceived.DamageDealer) {
			UARSLevelingComponent* dealerStatComp = LastDamageReceived.DamageDealer->FindComponentByClass<UARSLevelingComponent>();
			const UARSLevelingComponent* ownerStatComp = GetOwner()->FindComponentByClass<UARSLevelingComponent>();
			if (dealerStatComp && ownerStatComp) {
				dealerStatComp->AddExp(ownerStatComp->GetExpOnDeath());
			}
		}
	}

	OnOwnerDeath.Broadcast();
}

void UACFDamageHandlerComponent::OnRep_IsAlive()
{
	OnOwnerDeath.Broadcast();
}

void UACFDamageHandlerComponent::OnRep_LastDamageReceived()
{
	OnDamageReceived.Broadcast(LastDamageReceived);

	if (LastDamageReceived.DamageDealer) {
		TObjectPtr<UACFDamageHandlerComponent> dealerComp = LastDamageReceived.DamageDealer->FindComponentByClass<UACFDamageHandlerComponent>();
		if (dealerComp) {
			dealerComp->OnDamageInflicted.Broadcast(LastDamageReceived);
		}
	}
}
