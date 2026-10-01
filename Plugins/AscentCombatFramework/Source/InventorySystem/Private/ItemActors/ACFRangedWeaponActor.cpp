// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ItemActors/ACFRangedWeaponActor.h"
#include "ACFItemSystemFunctionLibrary.h"
#include "GameFramework/Character.h"
#include "Items/ACFItem.h"
#include "Items/ACFProjectile.h"
#include "Items/ACFRangedWeapon.h"
#include <GameFramework/ProjectileMovementComponent.h>
#include <Kismet/GameplayStatics.h>
#include <Kismet/KismetMathLibrary.h>
#include <Sound/SoundCue.h>

AACFRangedWeaponActor::AACFRangedWeaponActor()
{

    ShootingComp = CreateDefaultSubobject<UACFShootingComponent>(TEXT("ShotingComponent"));
}

void AACFRangedWeaponActor::BeginPlay()
{
    Super::BeginPlay();
}

void AACFRangedWeaponActor::OnRep_ItemOwner()
{
    InitShooting();
}

void AACFRangedWeaponActor::InitShooting()
{
    if (ShootingComp) {
        ACharacter* charOwner = Cast<ACharacter>(ItemOwner);
        if (charOwner) {
            ShootingComp->SetupShootingComponent(charOwner, Mesh);
        }
    }
}

void AACFRangedWeaponActor::InitItemActor(APawn* inOwner, UACFItem* inItemDefinition)
{
    Super::InitItemActor(inOwner, inItemDefinition);

    if (ShootingComp) {
        ShootingComp->SetupShootingComponent(inOwner, Mesh);
        ShootingComp->Reload(true);
    }
}

bool AACFRangedWeaponActor::SwipeTraceShootAtActor(const AActor* target, FHitResult& outResult, float randomDeviation /*= 5.f*/)
{
    if (target && ItemOwner && ShootingComp) {
        return ShootingComp->SwipeTraceShootAtActor(target, outResult, randomDeviation, GetRangedWeaponDefinition()->ShootRadius);
    }
    return false;
}

void AACFRangedWeaponActor::Shoot(const FRotator& deltaRot, float charge /*= 1.f*/, TSubclassOf<class UACFProjectile> projectileOverride /*= nullptr);*/)
{
    if (ItemOwner && ShootingComp) {
        const FRotator EyesRotation = ItemOwner->GetControlRotation();
        ShootingComp->ShootAtDirection(EyesRotation + deltaRot, charge, projectileOverride);
    }
}

void AACFRangedWeaponActor::ShootAtDirection(const FRotator& direction, float charge /*= 1.f*/, TSubclassOf<class UACFProjectile> projectileOverride /* = nullptr);*/)
{
    if (ShootingComp) {
        ShootingComp->ShootAtDirection(direction, charge, projectileOverride);
    }
}

bool AACFRangedWeaponActor::SwipeTraceShoot(EShootTargetType targetType, FHitResult& outResult)
{
    if (ShootingComp && ItemOwner) {
        return ShootingComp->SwipeTraceShoot(ItemOwner, targetType, outResult, GetRangedWeaponDefinition()->ShootRadius);
    }
    return false;
}

void AACFRangedWeaponActor::ShootProjectile(EShootTargetType targetType /*= EShootTargetType::WeaponTowardsFocus*/, float charge /*= 1.f*/, TSubclassOf<class UACFProjectile> projectileOverride /*= nullptr*/)
{
    if (ShootingComp && ItemOwner) {
        ShootingComp->Shoot(ItemOwner, EShootingType::EProjectile, targetType, charge, projectileOverride);
    }
}

void AACFRangedWeaponActor::Reload(bool bTryToEquipAmmo)
{
    ShootingComp->Reload(bTryToEquipAmmo);
    OnReload();
}

void AACFRangedWeaponActor::OnReload_Implementation()
{
}

EShootingType AACFRangedWeaponActor::GetShootingType() const
{
    return GetRangedWeaponDefinition()->GetShootingType();
}

bool AACFRangedWeaponActor::CanShoot() const
{
    return ShootingComp->CanShoot();
}

bool AACFRangedWeaponActor::NeedsReload() const
{
    return ShootingComp->NeedsReload();
}

UACFRangedWeapon* AACFRangedWeaponActor::GetRangedWeaponDefinition() const
{
    return Cast<UACFRangedWeapon>(GetItemDefinition());
}

void AACFRangedWeaponActor::ShootAtActor(const AActor* target, float randomDeviation /*= 50.f*/, float charge /*= 1.f*/, TSubclassOf<class UACFProjectile> projectileOverride /*= nullptr);*/)
{
    if (ItemOwner && ShootingComp) {
        ShootingComp->ShootAtActor(target, randomDeviation, charge, projectileOverride);
    }
}
