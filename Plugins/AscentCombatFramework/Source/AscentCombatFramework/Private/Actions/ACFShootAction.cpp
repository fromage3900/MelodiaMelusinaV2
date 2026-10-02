// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "Actions/ACFShootAction.h"
#include "Components/ACFEquipmentComponent.h"
#include "Components/ACFShootingComponent.h"
#include "ItemActors/ACFRangedWeaponActor.h"
#include "ItemActors/ACFWeaponActor.h"

UACFShootAction::UACFShootAction()
{
    ActionConfig.PerformableInMovementModes.Add(EMovementMode::MOVE_Falling);
}

void UACFShootAction::OnActionStarted_Implementation()
{
    Super::OnActionStarted_Implementation();
    if (GetCharacterOwner()) {
        const TObjectPtr<UACFEquipmentComponent> equipComp = GetCharacterOwner()->FindComponentByClass<UACFEquipmentComponent>();
        if (!equipComp) {
            return;
        }
        rangedWeapon = Cast<AACFRangedWeaponActor>(equipComp->GetCurrentMainWeapon());
    }
}

bool UACFShootAction::GetSwipeResult(FHitResult& outResult) const
{
    outResult = ShootResult;
    return bSwipeSuccess;
}

bool UACFShootAction::CanActivateAbility(const FGameplayAbilitySpecHandle Handle, const FGameplayAbilityActorInfo* ActorInfo, const FGameplayTagContainer* SourceTags /*= nullptr*/, const FGameplayTagContainer* TargetTags /*= nullptr*/, OUT FGameplayTagContainer* OptionalRelevantTags /*= nullptr*/) const
{
    const TObjectPtr<UACFEquipmentComponent> equipComp = ActorInfo->AvatarActor->FindComponentByClass<UACFEquipmentComponent>();

    // checking if we can actually shoot
    if (equipComp) {
        const TObjectPtr<AACFWeaponActor> mainWeapon = equipComp->GetCurrentMainWeapon();
        if (mainWeapon) {
            const TObjectPtr<UACFShootingComponent> shootingComp = mainWeapon->FindComponentByClass<UACFShootingComponent>();
            if (shootingComp) {
                const bool bCanShoot = shootingComp->CanShoot();
                return bCanShoot && Super::CanActivateAbility(Handle, ActorInfo, SourceTags, TargetTags, OptionalRelevantTags);
            };
        }
    }
    return false;
}

void UACFShootAction::OnNotablePointReached_Implementation()
{
    Super::OnNotablePointReached_Implementation();

    if (rangedWeapon) {
        switch (rangedWeapon->GetShootingType()) {
        case EShootingType::ESwipeTrace:
            bSwipeSuccess = rangedWeapon->SwipeTraceShoot(SwipeTargetType, ShootResult);
            break;
        case EShootingType::EProjectile:
            rangedWeapon->Shoot(DeltaDirection, 1.f, ProjectileOverride);
            break;
        }
    }
}
