// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "Components/ACFDefenseStanceComponent.h"
#include "ACFCCTypes.h"
#include "ARSStatisticsComponent.h"
#include "Components/ACFAbilitySystemComponent.h"
#include "Actors/ACFCharacter.h"
#include "Components/ACFBlockComponent.h"
#include "Components/ACFCharacterMovementComponent.h"
#include "Components/ACFEquipmentComponent.h"
#include "Game/ACFFunctionLibrary.h"
#include "Items/ACFWeapon.h"
#include "Logging.h"
#include "Net/UnrealNetwork.h"
#include "ItemActors/ACFWeaponActor.h"
#include "ARSFunctionLibrary.h"
#include <AbilitySystemComponent.h>

// Sets default values for this component's properties
UACFDefenseStanceComponent::UACFDefenseStanceComponent()
{
	// Set this component to be initialized when the game starts, and to be ticked every frame.  You can turn these features
	// off to improve performance if you don't need them.
	PrimaryComponentTick.bCanEverTick = false;
	SetIsReplicatedByDefault(true);

	// ...
}

void UACFDefenseStanceComponent::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
	Super::GetLifetimeReplicatedProps(OutLifetimeProps);
	DOREPLIFETIME(UACFDefenseStanceComponent, bIsInDefensePosition);
	DOREPLIFETIME(UACFDefenseStanceComponent, bCounterGate);
	DOREPLIFETIME(UACFDefenseStanceComponent, bParryGate);
}

// Called when the game starts
void UACFDefenseStanceComponent::BeginPlay()
{
	Super::BeginPlay();

	statComp = GetOwner()->FindComponentByClass<UARSStatisticsComponent>();
	ensure(statComp);
	locComp = GetOwner()->FindComponentByClass<UACFCharacterMovementComponent>();

	UACFEquipmentComponent* equipComp = GetOwner()->FindComponentByClass<UACFEquipmentComponent>();
	if (equipComp && !equipComp->OnEquipmentChanged.IsAlreadyBound(this, &UACFDefenseStanceComponent::HandleEquipmentChanged)) {
		equipComp->OnEquipmentChanged.AddDynamic(this, &UACFDefenseStanceComponent::HandleEquipmentChanged);
	}
}

void UACFDefenseStanceComponent::HandleEquipmentChanged(const FEquipment& Equipment)
{
	if (bIsInDefensePosition) {
		StopDefending();
	}
}

bool UACFDefenseStanceComponent::CanStartDefensePosition() const
{
	UAbilitySystemComponent* abilityComp = GetAbilityComponent();
	if (!abilityComp) {
		return false;
	}
	bool bFound = false;
	if (abilityComp->GetGameplayAttributeValue(DamagedAttribute, bFound) < MinimumDamageStatisticToStartBlocking && bFound && !bParryGate) {
		return false;
	}

	return IsValid(TryGetBestBlockComp());
}

void UACFDefenseStanceComponent::StartDefending_Implementation()
{
	if (CanStartDefensePosition()) {
		currentBlockComp = TryGetBestBlockComp();
		if (locComp) {
			locComp->ActivateLocomotionStance(UGameplayTagsManager::Get().RequestGameplayTag(ACF::BlockTag));
			locComp->SetLocomotionState(LocomotionStateWhileBlocking);
		}
		bIsInDefensePosition = true;

		defendingModifierHandle = statComp->AddAttributeSetModifier(currentBlockComp->GetDefendingModifier());

		OnDefenseStanceChanged.Broadcast(bIsInDefensePosition);
	}
}

void UACFDefenseStanceComponent::StopDefending_Implementation()
{
	if (!statComp) {
		return;
	}
	if (!bIsInDefensePosition) {
		return;
	}

	if (locComp) {
		locComp->DeactivateLocomotionStance(UGameplayTagsManager::Get().RequestGameplayTag(ACF::BlockTag));
		locComp->ResetToDefaultLocomotionState();
	}
	bIsInDefensePosition = false;

	statComp->RemoveAttributeSetModifier(defendingModifierHandle);

	OnDefenseStanceChanged.Broadcast(bIsInDefensePosition);
}

bool UACFDefenseStanceComponent::TryBlockIncomingDamage(const FACFDamageEvent& damageEvent, float damageToBlock, FGameplayTag& outAction)
{
	if (!CanBlockDamage(damageEvent)) {
		return false;
	}

	if (!damageEvent.DamageReceiver) {
		return false;
	}

	const float tempDamage = damageToBlock * currentBlockComp->GetDamagedStatisticMultiplier();
	UACFAbilitySystemComponent* actionsManager = damageEvent.DamageReceiver->FindComponentByClass<UACFAbilitySystemComponent>();

	if (bParryGate) {
		outAction = ActionToBeTriggeredOnParry;
		OnDamageBlocked.Broadcast(damageEvent);
		return true;
	}
	if (bCounterGate) {
		outAction = CounterAttackAction;
		OnDamageBlocked.Broadcast(damageEvent);
		return true;
	}
	UAbilitySystemComponent* abilityComp = damageEvent.DamageReceiver->FindComponentByClass<UAbilitySystemComponent>();
	if (!abilityComp) {
		return false;
	}
	if (DamagedAttribute.IsValid() && abilityComp->GetNumericAttribute(DamagedAttribute) > tempDamage) {
		outAction = ActionToBeTriggeredOnBlock;
		OnDamageBlocked.Broadcast(damageEvent);
		return true;
	}
	else {
		if (actionsManager && ActionToBeTriggeredOnDefenceBreak != FGameplayTag()) {
			outAction = ActionToBeTriggeredOnDefenceBreak;
		}
		StopDefending();
		return true;
	}
}

bool UACFDefenseStanceComponent::CanBlockDamage(const FACFDamageEvent& damageEvent) const
{
	if (!statComp) {
		UE_LOG(ACFLog, Error, TEXT("Missing Stat Component! - UACFDefenseStanceComponent::CanBlockDamage"));
		return false;
	}

	if (!bIsInDefensePosition) {
		return false;
	}

	if (!TryGetBestBlockComp()) {
		return false;
	}

	if (!IsAttackBlocked(damageEvent.DamageReceiver, damageEvent.DamageDealer, currentBlockComp->GetMaxBlockAngleDegrees())) {
		return false;
	}

	const UACFAbilitySystemComponent* ownerActions = GetOwner()->FindComponentByClass<UACFAbilitySystemComponent>();
	// you can't block while doing other actions

	if (!ownerActions || !ownerActions->CanExecuteAbility(ActionToBeTriggeredOnBlock)) {

		UE_LOG(ACFLog, Warning, TEXT("Impossible to execute block action! - UACFDefenseStanceComponent::CanBlockDamage"));
		return false;
	}

	if (!IsParrying() && ActionsThatPreventBlocking.Num() > 0) {
		const FGameplayTag CurrentAction = ownerActions->GetCurrentActionTag();
		if (CurrentAction.IsValid() && ActionsThatPreventBlocking.Contains(CurrentAction)) {
			return false;
		}
	}

	return currentBlockComp->GetBlockableDamages().Contains(damageEvent.DamageClass);
}

void UACFDefenseStanceComponent::StartParry()
{
	bParryGate = true;
	StartDefending();
}

void UACFDefenseStanceComponent::StopParry()
{
	bParryGate = false;
	StopDefending();
}

bool UACFDefenseStanceComponent::CanParry() const
{
	if (bParryGate) {
		return false;
	}
	const UACFBlockComponent* blockComp = TryGetBestBlockComp();
	if (blockComp) {
		return blockComp->GetCanParry() && CanStartDefensePosition();
	}

	return false;
}

bool UACFDefenseStanceComponent::IsAttackBlocked(AActor* Receiver, AActor* Attacker, float inMaxBlockAngleDegrees) const
{
	if (!Receiver || !Attacker) {
		return false;
	}

	// Get direction from attacker to receiver (reverse of hit direction)
	FVector DirectionToAttacker = Attacker->GetActorLocation() - Receiver->GetActorLocation();
	DirectionToAttacker.Z = 0.f;
	DirectionToAttacker.Normalize();

	FVector ReceiverForward = Receiver->GetActorForwardVector();
	ReceiverForward.Z = 0.f;
	ReceiverForward.Normalize();

	const float DotProduct = FVector::DotProduct(ReceiverForward, DirectionToAttacker);
	const float AngleDegrees = FMath::RadiansToDegrees(FMath::Acos(FMath::Clamp(DotProduct, -1.f, 1.f)));

	return AngleDegrees <= inMaxBlockAngleDegrees;
}

float UACFDefenseStanceComponent::GetDamagedStatisticMultiplier() const
{
	return GetCurrentBlockComp()->GetDamagedStatisticMultiplier();
}

bool UACFDefenseStanceComponent::CanCounterAttack(const FACFDamageEvent& incomingDamage)
{
	if (!bCounterGate) {
		return false;
	}

	if (!currentBlockComp) {
		return false;
	}

	const UACFAbilitySystemComponent* actionsManager = GetOwner()->FindComponentByClass<UACFAbilitySystemComponent>();
	if (!actionsManager) {
		return false;
	}

	if (!actionsManager->CanExecuteAbility(CounterAttackAction)) {
		return false;
	}
	if (!currentBlockComp->GetCounterableDamages().Contains(incomingDamage.DamageClass)) {
		return false;
	}

	if (!incomingDamage.DamageDealer) {
		return false;
	}

	const IACFEntityInterface* acfEntity = Cast<IACFEntityInterface>(incomingDamage.DamageDealer);
	if (acfEntity && !IACFEntityInterface::Execute_IsEntityAlive(incomingDamage.DamageDealer)) {
		return false;
	}

	return true;
}

bool UACFDefenseStanceComponent::TryCounterAttack(const FACFDamageEvent& incomingDamage, FGameplayTag& outCounterAction)
{
	if (!CanCounterAttack(incomingDamage)) {
		return false;
	}
	outCounterAction = CounterAttackAction;
	OnCounterAttackTriggered.Broadcast();

	return true;
}

UACFBlockComponent* UACFDefenseStanceComponent::TryGetBestBlockComp() const
{
	const UACFEquipmentComponent* equipComp = GetOwner()->FindComponentByClass<UACFEquipmentComponent>();

	if (!equipComp) {
		return GetOwner()->FindComponentByClass<UACFBlockComponent>();
	}

	const AACFWeaponActor* offhand = equipComp->GetCurrentOffhandWeapon();
	if (offhand) {
		auto blockComp = offhand->FindComponentByClass<UACFBlockComponent>();
		if (blockComp) {
			return blockComp;
		}
	}

	const AACFWeaponActor* currWeap = equipComp->GetCurrentMainWeapon();

	if (currWeap) {
		auto blockComp = currWeap->FindComponentByClass<UACFBlockComponent>();
		if (blockComp) {
			return blockComp;
		}
	}
	return GetOwner()->FindComponentByClass<UACFBlockComponent>();
}

void UACFDefenseStanceComponent::OnRep_DefPos()
{
	OnDefenseStanceChanged.Broadcast(bIsInDefensePosition);
}


UAbilitySystemComponent* UACFDefenseStanceComponent::GetAbilityComponent() const
{
	if (GetOwner()) {
		return GetOwner()->FindComponentByClass<UAbilitySystemComponent>();
	}
	return nullptr;
}


