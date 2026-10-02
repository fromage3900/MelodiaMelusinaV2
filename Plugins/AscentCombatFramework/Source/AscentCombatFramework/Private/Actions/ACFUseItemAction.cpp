// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "Actions/ACFUseItemAction.h"
#include "ACFItemTypes.h"
#include "Actors/ACFCharacter.h"
#include "Animation/ACFAnimInstance.h"
#include "Components/ACFEquipmentComponent.h"
#include "Items/ACFRangedWeapon.h"
#include "Items/ACFWeapon.h"
#include <GameplayTagsManager.h>
#include "ItemActors/ACFRangedWeaponActor.h"
#include <Abilities/GameplayAbilityTypes.h>



FGameplayTag UACFUseItemAction::GetItemSlot_Implementation() const
{
	if (StoredPayload.bIsValid && StoredPayload.PayloadTag != FGameplayTag()) {
		return StoredPayload.PayloadTag;
	}
	return ItemSlot;
}

FGameplayTag UACFUseItemAction::GetOffHandSlot_Implementation() const
{
	return OffHandSlot;
}

void UACFUseItemAction::OnNotablePointReached_Implementation()
{
	Super::OnNotablePointReached_Implementation();
	UseItem();
	bSuccess = true;
}

void UACFUseItemAction::OnActionEnded_Implementation()
{
	if (!bSuccess && bShouldUseIfInterrupted) {
		UseItem();
	}
}

UACFUseItemAction::UACFUseItemAction()
{
	ActionConfig.PerformableInMovementModes.Add(EMovementMode::MOVE_Falling);
}

void UACFUseItemAction::ActivateAbility(const FGameplayAbilitySpecHandle Handle, const FGameplayAbilityActorInfo* ActorInfo, const FGameplayAbilityActivationInfo ActivationInfo, const FGameplayEventData* TriggerEventData)
{
	Super::ActivateAbility(Handle, ActorInfo, ActivationInfo, TriggerEventData);

	bSuccess = false;
	if (bCheckHandsIK) {
		const AACFCharacter* acfCharacter = Cast<AACFCharacter>(GetCharacterOwner());
		if (acfCharacter) {
			const UACFEquipmentComponent* equipComp = acfCharacter->GetEquipmentComponent();
			UACFAnimInstance* animInst = acfCharacter->GetACFAnimInstance();
			if (equipComp && animInst) {
				animInst->SetEnableHandIK(false);
			}
		}
	}

}

void UACFUseItemAction::EndAbility(const FGameplayAbilitySpecHandle Handle, const FGameplayAbilityActorInfo* ActorInfo, const FGameplayAbilityActivationInfo ActivationInfo, bool bReplicateEndAbility, bool bWasCancelled)
{
	if (bCheckHandsIK) {
		const AACFCharacter* acfCharacter = Cast<AACFCharacter>(GetCharacterOwner());

		if (acfCharacter) {
			const UACFEquipmentComponent* equipComp = acfCharacter->GetEquipmentComponent();
			UACFAnimInstance* animInst = acfCharacter->GetACFAnimInstance();
			if (equipComp && animInst) {
				animInst->SetEnableHandIK(equipComp->ShouldUseLeftHandIK());
			}
		}
	}
	Super::EndAbility(Handle, ActorInfo, ActivationInfo, bReplicateEndAbility, bWasCancelled);
}

bool UACFUseItemAction::CanActivateAbility(const FGameplayAbilitySpecHandle Handle, const FGameplayAbilityActorInfo* ActorInfo, const FGameplayTagContainer* SourceTags /* = nullptr */,
	const FGameplayTagContainer* TargetTags /* = nullptr */, OUT FGameplayTagContainer* OptionalRelevantTags /* = nullptr */) const
{
	const UACFEquipmentComponent* equipComp = ActorInfo->AvatarActor->FindComponentByClass<UACFEquipmentComponent>();

	if (equipComp) {
		return equipComp->HasAnyItemInEquipmentSlot(ItemSlot);//&& Super::CanActivateAbility(Handle, ActorInfo, SourceTags, TargetTags, OptionalRelevantTags);
	}
	else {
		UE_LOG(LogTemp, Warning, TEXT("ACFUseItemAction::CanActivateAbility: Invalid UACFEquipmentComponent on Owner"));
		return false;
	}
}

void UACFUseItemAction::UseItem()
{
	if (GetCharacterOwner()) {
		UACFEquipmentComponent* equipComp = GetCharacterOwner()->FindComponentByClass<UACFEquipmentComponent>();
		if (equipComp) {
			equipComp->UseEquippedItemBySlot(GetItemSlot());
			if (bTryToEquipOffhand) {
				const AACFWeaponActor* mainWeap = equipComp->GetCurrentMainWeapon();
				if (mainWeap && mainWeap->GetHandleType() == EHandleType::OneHanded) {
					equipComp->UseEquippedItemBySlot(GetOffHandSlot());
				}
			}
			if (bTryToEquipAmmo) {
				AACFRangedWeaponActor* rangedWeap = Cast<AACFRangedWeaponActor>(equipComp->GetCurrentMainWeapon());
				if (rangedWeap) {
					rangedWeap->Reload(bTryToEquipAmmo);
				}
			}
		}
	}
}
