// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ItemActors/ACFGliderActor.h"
#include "Items/ACFGliderItem.h"

#include "Components/ACFEquipmentComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "GameFramework/Character.h"
#include "Net/UnrealNetwork.h"

AACFGliderActor::AACFGliderActor()
{
    bReplicates = true;
    SetReplicateMovement(true);

    Mesh = CreateDefaultSubobject<USkeletalMeshComponent>(TEXT("GliderMesh"));
    Mesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    SetRootComponent(Mesh);

    LeftHandIKPos = CreateDefaultSubobject<USceneComponent>(TEXT("Left Hand IK"));
    LeftHandIKPos->SetupAttachment(Mesh);
}

void AACFGliderActor::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(AACFGliderActor, ReplicatedMesh);
}

void AACFGliderActor::InitItemActor(APawn* inOwner, UACFItem* inItemDefinition)
{
    Super::InitItemActor(inOwner, inItemDefinition);

    UACFGliderItem* GliderItem = Cast<UACFGliderItem>(inItemDefinition);
    if (!GliderItem)
    {
        return;
    }

    // Store the mesh in a replicated property — OnRep_GliderMesh will apply it on clients.
    ReplicatedMesh = GliderItem->GliderMesh;
    ApplyMesh();

    // Attach to the equipment component's main mesh at the configured socket.
    UACFEquipmentComponent* EquipComp = inOwner->FindComponentByClass<UACFEquipmentComponent>();
    if (!EquipComp)
    {
        return;
    }

    USkeletalMeshComponent* OwnerSkelMesh = EquipComp->GetMainMesh();
    if (!OwnerSkelMesh)
    {
        return;
    }

    const FAttachmentTransformRules Rules(
        EAttachmentRule::SnapToTarget,
        EAttachmentRule::SnapToTarget,
        EAttachmentRule::KeepRelative,
        true);

    const FName Socket = GliderItem->AttachSocketName;
    if (Socket != NAME_None && OwnerSkelMesh->DoesSocketExist(Socket))
    {
        AttachToComponent(OwnerSkelMesh, Rules, Socket);
    }
    else
    {
        AttachToComponent(OwnerSkelMesh, Rules);
    }

    ApplyIKOverride();
}

void AACFGliderActor::OnRep_ItemOwner()
{
    Super::OnRep_ItemOwner();
    ApplyIKOverride();
}

void AACFGliderActor::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
    ClearIKOverride();
    Super::EndPlay(EndPlayReason);
}

void AACFGliderActor::ApplyIKOverride()
{
    if (!GetItemOwner())
    {
        return;
    }
    if (UACFEquipmentComponent* EquipComp = GetItemOwner()->FindComponentByClass<UACFEquipmentComponent>())
    {
        EquipComp->SetLeftHandIKOverride(LeftHandIKPos);
    }
}

void AACFGliderActor::ClearIKOverride()
{
    if (!GetItemOwner())
    {
        return;
    }
    if (UACFEquipmentComponent* EquipComp = GetItemOwner()->FindComponentByClass<UACFEquipmentComponent>())
    {
        EquipComp->ClearLeftHandIKOverride();
    }
}

void AACFGliderActor::BeginPlay()
{
    Super::BeginPlay();

    // On clients, ReplicatedMesh may already be set if the rep arrived before BeginPlay.
    if (ReplicatedMesh)
    {
        ApplyMesh();
    }
}

void AACFGliderActor::OnRep_GliderMesh()
{
    ApplyMesh();
}

void AACFGliderActor::ApplyMesh()
{
    if (Mesh && ReplicatedMesh)
    {
        Mesh->SetSkeletalMesh(ReplicatedMesh.Get());
    }
}

void AACFGliderActor::InitItemFromDefinition_Implementation(UACFItem* inItemDefinition)
{
    // Handled in InitItemActor.
}
