// // Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ACMDamageActor.h"
#include <Components/InterpToMovementComponent.h>
#include <Components/MeshComponent.h>

// Sets default values
AACMDamageActor::AACMDamageActor()
{
    // Set this actor to call Tick() every frame.  You can turn this off to improve performance if you don't need it.
    PrimaryActorTick.bCanEverTick = false;
    bReplicates = true;
    SetReplicateMovement(true);
    CollisionComp = CreateDefaultSubobject<UACMCollisionManagerComponent>(TEXT("Collisions Manager"));
    MovementComp = CreateDefaultSubobject<UInterpToMovementComponent>(TEXT("Movement Comp"));
    MeshComp = CreateDefaultSubobject<UMeshComponent>(TEXT("Mesh Comp"));
}

void AACMDamageActor::SetupCollisions(AActor* inOwner)
{
    if (CollisionComp) {
        CollisionComp->SetActorOwner(inOwner);
        CollisionComp->SetupCollisionManager(MeshComp, {});
        CollisionComp->AddActorToIgnore(inOwner);
        OnSetup(inOwner);
    }
}

void AACMDamageActor::StartDamageTraces()
{
    if (CollisionComp) {
        CollisionComp->StartAllTraces();
    }
}

void AACMDamageActor::StopDamageTraces()
{
    if (CollisionComp) {
        CollisionComp->StopAllTraces();
    }
}

void AACMDamageActor::StartAreaDamage(float radius /*= 100.f*/, float damageInterval)
{
    if (CollisionComp) {
        CollisionComp->StartAreaDamage(GetActorLocation(), radius, damageInterval);
    }
}

void AACMDamageActor::StopAreaDamage()
{
    if (CollisionComp) {
        CollisionComp->StopCurrentAreaDamage();
    }
}

void AACMDamageActor::OnSetup_Implementation(AActor* new0wner)
{
}

// Called when the game starts or when spawned
void AACMDamageActor::BeginPlay()
{
    Super::BeginPlay();

    if (CollisionComp) {
        CollisionComp->OnActorDamaged.AddDynamic(this, &AACMDamageActor::HandleDamagedActor);
        SetupCollisions(ActorOwner);
    }
}

void AACMDamageActor::EndPlay(EEndPlayReason::Type end)
{
    Super::EndPlay(end);
    if (CollisionComp) {
        CollisionComp->OnActorDamaged.RemoveDynamic(this, &AACMDamageActor::HandleDamagedActor);
    }
}

void AACMDamageActor::HandleDamagedActor(AActor* damagedActor)
{
    OnActorDamaged.Broadcast(damagedActor);
}
