// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ItemActors/ACFProjectileActor.h"
#include "ACFTeamManagerSubsystem.h"
#include "ACMCollisionManagerComponent.h"
#include "ACMCollisionsFunctionLibrary.h"
#include "Components/ACFEquipmentComponent.h"
#include "Components/ACFTeamManagerComponent.h"
#include "Components/SphereComponent.h"
#include "GameFramework/Character.h"
#include "GameFramework/GameStateBase.h"
#include "Interfaces/ACFEntityInterface.h"
#include "Interfaces/ACFInteractableInterface.h"
#include "Items/ACFRangedWeapon.h"
#include <Components/SceneComponent.h>
#include <Components/StaticMeshComponent.h>
#include <Engine/EngineTypes.h>
#include <Engine/World.h>
#include <GameFramework/Actor.h>
#include <GameFramework/ProjectileMovementComponent.h>
#include <Kismet/GameplayStatics.h>
#include <Net/UnrealNetwork.h>
#include <Particles/ParticleSystemComponent.h>
#include "ACFItemSystemFunctionLibrary.h"

AACFProjectileActor::AACFProjectileActor()
{
    // Set this actor to call Tick() every frame.  You can turn this off to improve performance if you don't need it.
    PrimaryActorTick.bCanEverTick = false;
    // Create A Default Root Component as a container
    SphereComp = CreateDefaultSubobject<USphereComponent>(TEXT("RootComp"));
    SetRootComponent(SphereComp);

    CollisionComp = CreateDefaultSubobject<UACMCollisionManagerComponent>(TEXT("Collision Manager Comp"));
    // Attach Mesh component to root component
    MeshComp = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("ProjectileMeshComp"));
    MeshComp->SetupAttachment(SphereComp);
    MeshComp->SetCollisionProfileName(TEXT("NoCollision"));
    MeshComp->SetCollisionEnabled(ECollisionEnabled::NoCollision);

    bReplicates = true;

    SetReplicateMovement(true);
    // Use a ProjectileMovementComponent to govern this projectile's movement
    ProjectileMovementComp = CreateDefaultSubobject<UProjectileMovementComponent>(TEXT("ProjectileMovementComp"));

    ProjectileMovementComp->UpdatedComponent = SphereComp;
    ProjectileMovementComp->InitialSpeed = 4000.f;
    ProjectileMovementComp->MaxSpeed = 5000.0f;
    ProjectileMovementComp->bRotationFollowsVelocity = true;
    ProjectileMovementComp->bShouldBounce = false;
    ProjectileMovementComp->bAutoActivate = false;

    bIsFlying = false;
    bPickable = false;
    SphereComp->SetSphereRadius(4.0f);
    HitPolicy = EProjectileHitPolicy::DestroyOnHit;
}

// Called when the game starts or when spawned
void AACFProjectileActor::BeginPlay()
{
    Super::BeginPlay();
    if (CollisionComp) {
        CollisionComp->SetActorOwner(ItemOwner);
        CollisionComp->SetupCollisionManager(MeshComp, UACFItemSystemFunctionLibrary::GetDefaultHitTraceChannels());
    }
    if (SphereComp && !SphereComp->OnComponentHit.IsAlreadyBound(this, &AACFProjectileActor::HandleProjectileHit)) {
        SphereComp->OnComponentHit.AddDynamic(this, &AACFProjectileActor::HandleProjectileHit);
    }
    if (bIsFlying) {
        ProjectileMovementComp->SetActive(true);
    }
}

void AACFProjectileActor::ActivateDamage()
{
    if (CollisionComp) {
        CollisionComp->SetActorOwner(ItemOwner);
        CollisionComp->SetupCollisionManager(MeshComp, UACFItemSystemFunctionLibrary::GetDefaultHitTraceChannels());

        const bool bImplements = ItemOwner->GetClass()->ImplementsInterface(UACFEntityInterface::StaticClass());
        if (bImplements) {
            const FGameplayTag combatTeam = IACFEntityInterface::Execute_GetEntityCombatTeam(ItemOwner);
            if (UACFTeamManagerSubsystem* TeamSubsystem = GetWorld()->GetSubsystem<UACFTeamManagerSubsystem>()) {
                CollisionComp->AddCollisionChannels(TeamSubsystem->GetHostileCollisionChannels(combatTeam));
            } else {
                UE_LOG(LogTemp, Error, TEXT("NO  TEAM MANAGER MANAGER ON GAMESTATE! - AACFProjectile"));
            }
        }
        bImpacted = false;
        CollisionComp->StartAllTraces();
        CollisionComp->OnCollisionDetected.AddDynamic(this, &AACFProjectileActor::HandleAttackHit);
    }
}

void AACFProjectileActor::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
    if (CollisionComp) {
        CollisionComp->StopAllTraces();
    }
    Super::EndPlay(EndPlayReason);
}

void AACFProjectileActor::InitItemActor(APawn* inOwner, UACFItem* inItemDefinition)
{
    Super::InitItemActor(inOwner, inItemDefinition);
    bPickable = false;

    SetupProjectile(inOwner);
}

void AACFProjectileActor::OnInteractedByPawn_Implementation(class APawn* Pawn, const FString& interactionType /*= ""*/)
{
    if (Pawn) {
        TObjectPtr<UACFEquipmentComponent> equipComp = Pawn->GetComponentByClass<UACFEquipmentComponent>();
        if (equipComp) {
            equipComp->AddItemToInventoryByClass(GetProjectileDefinition()->GetClass(), 1);
            Destroy();
        }
    }
}

bool AACFProjectileActor::CanBeInteracted_Implementation(class APawn* Pawn)
{
    return bPickable;
}

FText AACFProjectileActor::GetInteractableName_Implementation()
{
    return GetItemDefinition() ? GetItemDefinition()->GetItemName() : FText::GetEmpty();
}

void AACFProjectileActor::OnRep_ItemOwner()
{
    if (ItemOwner) {
        ActivateDamage();
    }
}

void AACFProjectileActor::SetupProjectile(class APawn* inOwner)
{
    if (GetItemDefinition()) {
        projDefinitionClass = GetItemDefinition()->GetClass();
    }
    if (inOwner) {
        bIsFlying = true;
        ItemOwner = inOwner;
        SetLifeSpan(ProjectileLifespan);
       // ActivateDamage();

    } else {
        bIsFlying = false;
    }
}

void AACFProjectileActor::MakeStatic()
{
    ProjectileMovementComp->SetActive(false);
    ProjectileMovementComp->Velocity = FVector::ZeroVector;
    SetActorScale3D(FVector(1.0f, 1.0f, 1.0f));
    if (CollisionComp) {
        CollisionComp->StopAllTraces();
    }
}

void AACFProjectileActor::PlayImpact(const FHitResult& HitResult)
{
    if (!bImpacted && CollisionComp) {
        const FImpactFX impact = FImpactFX(ImpactEffect, HitResult.ImpactPoint);
        FComponentFX outComps;
        UACMCollisionsFunctionLibrary::PlayEffectLocally(impact, ItemOwner,outComps);
        bImpacted = true;
    }
}

void AACFProjectileActor::OnRep_ProjDefinitionClass()
{
    ItemDefinition = NewObject<UACFItem>(this, projDefinitionClass);

}

void AACFProjectileActor::HandleAttackHit(const FHitResult& HitResult)
{
    if (HasAuthority()) {
        switch (HitPolicy) {
        case EProjectileHitPolicy::DestroyOnHit:
            SetLifeSpan(.1f);
            break;
        case EProjectileHitPolicy::AttachOnHit:
            AttachToHit(HitResult, false);
            break;
        default:
            break;
        }
    }

    PlayImpact(HitResult);
}

void AACFProjectileActor::HandleProjectileHit(UPrimitiveComponent* HitComponent, AActor* OtherActor, UPrimitiveComponent* OtherComp, FVector NormalImpulse, const FHitResult& Hit)
{
    switch (HitPolicy) {
    case EProjectileHitPolicy::DestroyOnHit:
        SetLifeSpan(.1f);
        break;
    case EProjectileHitPolicy::AttachOnHit:
        AttachToHit(Hit, true);
        break;
    default:
        break;
    }
    PlayImpact(Hit);
}

void AACFProjectileActor::AttachToHit(const FHitResult& HitResult, bool inPickable)
{
    ACharacter* damagedActor = Cast<ACharacter>(HitResult.GetActor());
    //   const FVector AttachLocation = GetActorLocation() + (GetActorForwardVector() * PenetrationLevel) + (GetActorUpVector() * PenetrationLevel);
    const FRotator AttachRotation = GetActorRotation();
    bPickable = inPickable;
    MakeStatic();
    if (damagedActor) {
        AttachToComponent(damagedActor->GetMesh(), FAttachmentTransformRules::SnapToTargetNotIncludingScale, HitResult.BoneName);
        SetActorRotation(AttachRotation);
    } else {
        AttachToComponent(HitResult.Component.Get(), FAttachmentTransformRules::KeepWorldTransform);
    }
    SetActorRotation(GetActorRotation());
    SetLifeSpan(AttachedLifespan);
    CollisionComp->StopAllTraces();
}

void AACFProjectileActor::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(AACFProjectileActor, bPickable);
    DOREPLIFETIME(AACFProjectileActor, projDefinitionClass);
}