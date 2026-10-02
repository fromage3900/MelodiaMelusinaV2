// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "Components/ACFShootingComponent.h"
#include "ACFItemSystemFunctionLibrary.h"
#include "ACMCollisionManagerComponent.h"
#include "ACMCollisionsFunctionLibrary.h"
#include "ACMTypes.h"
#include "Components/ACFEquipmentComponent.h"
#include "Components/ACFInventoryComponent.h"
#include "GameFramework/Character.h"
#include "ItemActors/ACFProjectileActor.h"
#include "Items/ACFItem.h"
#include "Items/ACFProjectile.h"
#include "Logging.h"
#include "Net/UnrealNetwork.h"
#include <Engine/World.h>
#include <GameFramework/ProjectileMovementComponent.h>
#include <Kismet/GameplayStatics.h>
#include <Sound/SoundCue.h>
#include <TimerManager.h>

// Sets default values for this component's properties
UACFShootingComponent::UACFShootingComponent()
{
    // Set this component to be initialized when the game starts, and to be ticked every frame.  You can turn these features
    // off to improve performance if you don't need them.
    PrimaryComponentTick.bCanEverTick = false;
    // ProjectileShotSpeed = 3500.0f;
    SetIsReplicatedByDefault(true);
}

void UACFShootingComponent::SetupShootingComponent(class APawn* inOwner, class UMeshComponent* inMesh)
{
    shootingMesh = inMesh;
    characterOwner = inOwner;
    Internal_SetupComponent(inOwner, inMesh);
}

void UACFShootingComponent::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(UACFShootingComponent, characterOwner);
    DOREPLIFETIME(UACFShootingComponent, AmmoState);
}

// Called when the game starts
void UACFShootingComponent::BeginPlay()
{
    Super::BeginPlay();
}

void UACFShootingComponent::ShootAtDirection(const FRotator& direction, float charge /*= 1.f*/, TSubclassOf<class UACFProjectile> projectileOverride, const FName socketOverride)
{
    if (!CanShoot()) {
        return;
    }

    const FVector ShotDirection = direction.Vector();

    FTransform spawnTransform;
    const FVector startingPos = socketOverride == NAME_None ? GetShootingSocketPosition() : shootingMesh->GetSocketLocation(socketOverride);
    spawnTransform.SetLocation(startingPos);
    spawnTransform.SetRotation(direction.Quaternion());
    spawnTransform.SetScale3D(FVector(1.f, 1.f, 1.f));

    Internal_Shoot(spawnTransform, ShotDirection, charge, projectileOverride);
}

void UACFShootingComponent::Shoot(APawn* SourcePawn, EShootingType type, EShootTargetType targetType, float charge /*= 1.f*/, TSubclassOf<class UACFProjectile> projectileOverride /*= nullptr*/)
{

    if (!CanShoot()) {
        return;
    }

    FVector startLoc;
    const FTransform targetTransform = UACFItemSystemFunctionLibrary::GetShootTransform(SourcePawn, targetType, startLoc);
    const FVector direction = targetTransform.GetUnitAxis(EAxis::X);
    const FTransform spawnTransform = FTransform(targetTransform.GetRotation(), startLoc);

    switch (type) {
    case EShootingType::EProjectile:
        //  const FVector BulletDir = VRandConeNormalDistribution(InputData.AimDir, HalfSpreadAngleInRadians, WeaponData->GetSpreadExponent());
        Internal_Shoot(spawnTransform, direction, charge, projectileOverride);
        break;
    case EShootingType::ESwipeTrace:
        FHitResult outResult;
        SwipeTraceShootAtDirection(startLoc, direction, outResult);
        break;
    }
}

void UACFShootingComponent::ShootAtActor(const AActor* target, float randomDeviation /*= 50.f*/, float charge /*= 1.f*/, TSubclassOf<class UACFProjectile> projectileOverride, const FName socketOverride)
{
    if (!CanShoot()) {
        return;
    }

    UWorld* world = GetWorld();

    if (target) {
        const FVector SpawnProjectileLocation = socketOverride == NAME_None ? GetShootingSocketPosition() : shootingMesh->GetSocketLocation(socketOverride);

        const FRotator ProjectileOrientation = shootingMesh->GetSocketRotation(ProjectileStartSocket);

        const FVector targetLocation = target->GetActorLocation();

        FVector FlyDir;
        float FlyDistance;
        (targetLocation - SpawnProjectileLocation).ToDirectionAndLength(FlyDir, FlyDistance);
        const float FlyTime = FlyDistance / 3500.0f;
        FVector PredictedPosition = targetLocation + (target->GetVelocity() * FlyTime);

        const float RandomOffset_z = FMath::RandRange(-randomDeviation, randomDeviation);
        const float RandomOffset_x = FMath::RandRange(-randomDeviation, randomDeviation);
        const float RandomOffset_y = FMath::RandRange(-randomDeviation, randomDeviation);

        // Override Predicted Location with offset value
        PredictedPosition += FVector(RandomOffset_x, RandomOffset_y, RandomOffset_z);

        // Finalize Projectile fly direction
        FlyDir = (PredictedPosition - SpawnProjectileLocation).GetSafeNormal();

        FTransform spawnTransform;
        spawnTransform.SetLocation(SpawnProjectileLocation);
        spawnTransform.SetRotation(ProjectileOrientation.Quaternion());

        Internal_Shoot(spawnTransform, FlyDir, charge, projectileOverride);
    }
}
bool UACFShootingComponent::SwipeTraceShootAtActor(const AActor* target, FHitResult& outResult, float randomDeviation /*= 5.f*/, float swipeRadius)
{
    if (!CanShoot()) {
        return false;
    }
    const FVector SpawnProjectileLocation = GetShootingSocketPosition();
    const FVector targetLocation = target->GetActorLocation();

    FVector FlyDir;
    float FlyDistance;
    (targetLocation - SpawnProjectileLocation).ToDirectionAndLength(FlyDir, FlyDistance);
    // to check the real shoot speed for the prediction
    const float FlyTime = FlyDistance / 3500.0f;
    FVector PredictedPosition = targetLocation + (target->GetVelocity() * FlyTime);

    const float RandomOffset_z = FMath::RandRange(-randomDeviation, randomDeviation);
    const float RandomOffset_x = FMath::RandRange(-randomDeviation, randomDeviation);
    const float RandomOffset_y = FMath::RandRange(-randomDeviation, randomDeviation);

    // Override Predicted Location with offset value
    PredictedPosition += FVector(RandomOffset_x, RandomOffset_y, RandomOffset_z);

    // Finalize Projectile fly direction
    FlyDir = (PredictedPosition - SpawnProjectileLocation).GetSafeNormal();

    return SwipeTraceShootAtDirection(SpawnProjectileLocation, FlyDir, outResult, swipeRadius);
}

bool UACFShootingComponent::SwipeTraceShoot(APawn* SourcePawn, EShootTargetType targetType, FHitResult& outResult, float swipeRadius)
{
    if (!CanShoot()) {
        return false;
    }

    FVector startLoc;
    const FTransform targetTransform = UACFItemSystemFunctionLibrary::GetShootTransform(SourcePawn, targetType, startLoc);
    const FVector direction = targetTransform.GetUnitAxis(EAxis::X);
    const FTransform spawnTransform = FTransform(targetTransform.GetRotation(), startLoc);
    return SwipeTraceShootAtDirection(startLoc, direction, outResult, swipeRadius);
}

void UACFShootingComponent::ReduceAmmoMagazine_Implementation(int32 amount /*= 1*/)
{
    currentMagazine -= amount;
    if (currentMagazine < 0) {
        currentMagazine = 0;
    }
    UpdateAmmoState();
}

void UACFShootingComponent::Reload_Implementation(bool bTryToEquipAmmo = true)
{
    FEquippedItem equip;
    bool bFoundAmmo = false;
    FInventoryItem invItem;
    // let's see if we have equipped the ammo
    if (bTryToEquipAmmo) {
        UACFEquipmentComponent* equipComp = TryGetEquipment();
        if (TryGetAmmoSlot(equip) && equipComp) {

            if (!equipComp->GetItemByGuid(equip.ItemGuid, invItem)) {
                return;
            }

            const UACFProjectile* projectileClass = Cast<UACFProjectile>(invItem.ItemClass->GetDefaultObject());
            if (projectileClass && CanUseProjectile(projectileClass->GetClass())) {
                bFoundAmmo = true;
            } else {
                bFoundAmmo = TryEquipAmmoFromInventory();
            }

        } else {
            bFoundAmmo = TryEquipAmmoFromInventory();
        }
    } else {
        bFoundAmmo = TryGetAmmoSlot(equip);
    }

    // if we have valid ammos, we refill the magazine
    if (bFoundAmmo) {
        currentMagazine = invItem.Count > AmmoMagazine ? AmmoMagazine : invItem.Count;
        UpdateAmmoState();
    }
}

bool UACFShootingComponent::TryEquipAmmoFromInventory()
{
    FInventoryItem invItem;
    FEquippedItem equip;

    // otherwise we try to equip it from the inventory
    if (TryGetAllowedAmmoFromInventory(invItem)) {
        UACFEquipmentComponent* equipComp = TryGetEquipment();
        equipComp->EquipItemFromInventory(invItem);
        return TryGetAmmoSlot(equip);
    }
    return false;
}

bool UACFShootingComponent::CanShoot() const
{
    if (!(shootingMesh && characterOwner)) {
        UE_LOG(LogTemp, Error, TEXT("Shooting component not initialized! - UACFShootingComponent"));
        return false;
    }

    if (!bConsumeAmmo) {
        return true;
    } else {
        FEquippedItem equip;
        if (TryGetAmmoSlot(equip)) {
            const UACFProjectile* projectileClass = Cast<UACFProjectile>(equip.Item);
            if (projectileClass == nullptr) {
                UE_LOG(LogTemp, Warning, TEXT("No Projectile Class in Ammo Slot! - UACFShootingComponent::CanShoot()"));
                return false;
            }
            if (bUseMagazine) {
                return CanUseProjectile(projectileClass->GetClass()) && currentMagazine > 0;
            } else {
                return CanUseProjectile(projectileClass->GetClass());
            }
        } else {
            UE_LOG(LogTemp, Warning, TEXT("No Ammo Slot in Equipment! - UACFShootingComponent::"));
        }
    }
    return false;
}

bool UACFShootingComponent::CanUseProjectile(const TSubclassOf<UACFProjectile>& projectileClass) const
{
    return AllowedProjectiles.Contains(projectileClass);
}

bool UACFShootingComponent::NeedsReload() const
{
    FEquippedItem equip;
    if (bUseMagazine && currentMagazine <= 0) {
        return TryGetAmmoSlot(equip);
    }
    return false;
}

bool UACFShootingComponent::TryGetAllowedAmmoFromInventory(FInventoryItem& outAmmoSlot) const
{
    UACFEquipmentComponent* equipComp = TryGetEquipment();
    outAmmoSlot.Count = 0;
    bool bFound = false;

    if (equipComp) {
        FEquippedItem currentSlot;
        const bool bHasCurrentSlot = TryGetAmmoSlot(currentSlot);

        // first we try with current item class
        if (bHasCurrentSlot && AllowedProjectiles.Contains(currentSlot.GetItemClass())) {
            TArray<FInventoryItem> invItems;
            equipComp->GetAllItemsOfClassInInventory(currentSlot.GetItemClass(), invItems);
            for (const auto& item : invItems) {
                if (outAmmoSlot.Count < item.Count) {
                    outAmmoSlot = item;
                    bFound = true;
                }
            }
        }
        // if none, we try with all the possible classes
        else {
            for (const auto& projClass : AllowedProjectiles) {
                TArray<FInventoryItem> invItems;
                equipComp->GetAllItemsOfClassInInventory(projClass, invItems);
                for (const auto& item : invItems) {
                    if (outAmmoSlot.Count < item.Count) {
                        outAmmoSlot = item;
                        bFound = true;
                    }
                }
            }
        }
    }
    return bFound;
}

void UACFShootingComponent::OnRep_AmmoState()
{
    // Single atomic snapshot: magazine and total arrive together, so no race.
    currentMagazine = AmmoState.MagazineAmmo;
    OnCurrentAmmoChanged.Broadcast(AmmoState.MagazineAmmo, AmmoState.TotalAmmo);
}

void UACFShootingComponent::UpdateAmmoState()
{
    if (GetOwnerRole() != ROLE_Authority) {
        return;
    }

    // On the authority the total is computed from the live inventory; cache it
    // together with the magazine so clients receive a coherent pair.
    const int32 NewTotal = GetTotalAmmoCount();
    if (AmmoState.MagazineAmmo == currentMagazine && AmmoState.TotalAmmo == NewTotal) {
        return;
    }
    AmmoState.MagazineAmmo = currentMagazine;
    AmmoState.TotalAmmo = NewTotal;

    // Listen server: OnRep doesn't fire on the authority, so broadcast here.
    OnCurrentAmmoChanged.Broadcast(AmmoState.MagazineAmmo, AmmoState.TotalAmmo);
}

bool UACFShootingComponent::SwipeTraceShootAtDirection(const FVector& start, const FVector& direction, FHitResult& outResult, float swipeRadius)
{
    if (!CanShoot()) {
        return false;
    }

    UACMCollisionManagerComponent* collisionMan = GetOwner()->FindComponentByClass<UACMCollisionManagerComponent>();
    if (collisionMan) {

        //  PlayMuzzleEffect();
        RemoveAmmo();
        if (collisionMan) {
            const FVector endTrace = start + (direction * ShootRange);
            OnProjectileShoot.Broadcast();
            return collisionMan->PerformSwipeTraceShot_Local(start, endTrace, swipeRadius, outResult);
        }
    }
    return false;
}

void UACFShootingComponent::Internal_Shoot(const FTransform& spawnTransform, const FVector& ShotDirection, float charge, TSubclassOf<class UACFProjectile> projectileOverride)
{
    if (!CanShoot()) {
        return;
    }

    TSubclassOf<class UACFItem> projToSpawn;
    if (projectileOverride) {
        projToSpawn = projectileOverride;
    } else {
        projToSpawn = GetBestProjectileToShoot();
    }

    if (!projToSpawn) {
        return;
    }

    UACFProjectile* projDefinition = NewObject<UACFProjectile>(characterOwner, projToSpawn);

    if (!projDefinition || !projDefinition->ProjectileClass) {
        UE_LOG(ACFInventoryLog, Warning, TEXT("No Projectile Definition or class found for %s"), *projToSpawn->GetName());
        return;
    }

    UWorld* world = GetWorld();

    AACFProjectileActor* projectile = world->SpawnActorDeferred<AACFProjectileActor>(projDefinition->ProjectileClass,
        spawnTransform, characterOwner, characterOwner, ESpawnActorCollisionHandlingMethod::AlwaysSpawn);

    projectile->InitItemActor(characterOwner, projDefinition);
    projectile->FinishSpawning(spawnTransform);
    projectile->ActivateDamage();

    if (projectile) {
        UProjectileMovementComponent* moveComp = projectile->GetProjectileMovementComp();
        const float speed = moveComp->Velocity.Size();
        moveComp->Velocity = ShotDirection.GetSafeNormal() * speed;
    }

    RemoveAmmo();
    OnProjectileShoot.Broadcast();
}

void UACFShootingComponent::Internal_SetupComponent_Implementation(class APawn* inOwner, class UMeshComponent* inMesh)
{
    shootingMesh = inMesh;
    characterOwner = inOwner;
}

UACFEquipmentComponent* UACFShootingComponent::TryGetEquipment() const
{
    if (characterOwner) {
        return characterOwner->FindComponentByClass<UACFEquipmentComponent>();
    }
    return nullptr;
}

bool UACFShootingComponent::TryGetAmmoSlot(FEquippedItem& outSlot) const
{
    UACFEquipmentComponent* equipCom = TryGetEquipment();
    if (equipCom) {
        return equipCom->GetEquippedItemSlot(AmmoSlot, outSlot);
    }
    return false;
}

bool UACFShootingComponent::TryGetAmmoInventorySlot(FInventoryItem& outSlot) const
{
    FEquippedItem equip;
    UACFEquipmentComponent* equipComp = TryGetEquipment();
    if (TryGetAmmoSlot(equip) && equipComp) {
        return equipComp->GetItemByGuid(equip.ItemGuid, outSlot);
    }
    return false;
}

void UACFShootingComponent::RemoveAmmo(int32 count)
{
    if (GetOwnerRole() != ENetRole::ROLE_Authority) {
        // this is called in RPC and auth only functions, we should never call this on clients
        ensure(false);
        return;
    }
    if (bConsumeAmmo) {
        UACFEquipmentComponent* equipCom = TryGetEquipment();
        if (equipCom) {
            FInventoryItem equip;
            if (TryGetAmmoInventorySlot(equip)) {
                equipCom->RemoveItem(equip, count);
                if (bUseMagazine) {
                    ReduceAmmoMagazine(count);
                }
                FEquippedItem equipSlot;
                if (!equipCom->GetEquippedItemSlot(AmmoSlot, equipSlot) || equip.Count == 0) {
                    TryEquipAmmoFromInventory();
                }

                UpdateAmmoState();
            }
        }
    }
}

TSubclassOf<UACFItem> UACFShootingComponent::GetBestProjectileToShoot() const
{
    if (bConsumeAmmo) {
        FInventoryItem item;
        if (TryGetAmmoInventorySlot(item)) {
            return (item.ItemClass);
        }
    } else {
        return ProjectileClassBP;
    }
    return nullptr;
}

int32 UACFShootingComponent::GetTotalEquippedAmmoCount() const
{
    FInventoryItem item;
    if (TryGetAmmoInventorySlot(item)) {
        return item.Count;
    }
    return 0;
}

int32 UACFShootingComponent::GetTotalAmmoCount() const
{
    // Clients read the replicated snapshot to avoid recomputing from the
    // equipment/inventory, which live on another component and may not be in
    // sync with the magazine at the moment this is queried.
    if (GetOwnerRole() != ROLE_Authority) {
        return AmmoState.TotalAmmo;
    }

    FEquippedItem currentSlot;
    const bool bHasCurrentSlot = TryGetAmmoSlot(currentSlot);
    if (bHasCurrentSlot) {
        FInventoryItem item;
        const UACFEquipmentComponent* equipCom = TryGetEquipment();
        if (equipCom && TryGetAmmoInventorySlot(item)) {
            return equipCom->GetTotalCountOfItemsByClass(item.ItemClass);
        }
    }
    return 0;
}
