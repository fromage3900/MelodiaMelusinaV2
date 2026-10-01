// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ACFBaseBuildable.h"

#include "ACFBuildRecipe.h"
#include "ACFBuildableEntityComponent.h"
#include "ACFBuildingManagerComponent.h"
#include "ACFBuildingSnapComponent.h"
#include "Components/ACFEquipmentComponent.h"
#include <Components/StaticMeshComponent.h>

AACFBaseBuildable::AACFBaseBuildable()
{
    BuildableComp = CreateDefaultSubobject<UACFBuildableEntityComponent>(TEXT("Buildable Entity Component"));
    SnapComponent = CreateDefaultSubobject<UACFBuildingSnapComponent>(TEXT("Snap Component"));
    Root = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
    MeshComponent = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Mesh Component"));
    MeshComponent->SetupAttachment(Root);
    bReplicates = true;
    bAlwaysRelevant = true;
}

void AACFBaseBuildable::BeginPlay()
{
    Super::BeginPlay();
}

void AACFBaseBuildable::OnPlaced_Implementation()
{
}

void AACFBaseBuildable::OnDismantled_Implementation()
{
}

bool AACFBaseBuildable::IsPlacementValid_Implementation(const FVector& Location, const FRotator& Rotation)
{
    return true;
}

void AACFBaseBuildable::OnInteractedByPawn_Implementation(APawn* Pawn, const FString& interactionType)
{
}

void AACFBaseBuildable::Dismantle(APawn* Pawn)
{
    UACFBuildingManagerComponent* BuildableManager = GetBuildableManager(Pawn);
    if (IsValid(BuildableManager)) {
        if (BuildableManager->GetBuildingMode() == EBuildingMode::EDismantling) {
            BuildableManager->Dismantle(this);
        }
    }
}

UACFBuildingManagerComponent* AACFBaseBuildable::GetBuildableManager(APawn* Pawn) const
{
    if (Pawn && Pawn->GetController()) {
        return Pawn->GetController()->GetComponentByClass<UACFBuildingManagerComponent>();
    }
    return nullptr;
}

void AACFBaseBuildable::OnLocalInteractedByPawn_Implementation(APawn* Pawn, const FString& interactionType)
{
    Dismantle(Pawn);
}

void AACFBaseBuildable::OnInteractableRegisteredByPawn_Implementation(APawn* Pawn)
{
}

void AACFBaseBuildable::OnInteractableUnregisteredByPawn_Implementation(APawn* Pawn)
{
}

bool AACFBaseBuildable::CanBeInteracted_Implementation(APawn* Pawn)
{
    const UACFBuildingManagerComponent* BuildableManager = GetBuildableManager(Pawn);

    return IsValid(BuildableManager) && BuildableManager->GetBuildingMode() == EBuildingMode::EDismantling && 
        BuildableComp && BuildableComp->CanBeDismantled(Pawn);
}

FText AACFBaseBuildable::GetInteractableName_Implementation()
{
    if (BuildableComp)
    {
        const UACFBuildRecipe* recipe = BuildableComp->GetBuildingRecipe();
        if (recipe) {
            return FText::Format(
                NSLOCTEXT("ACF", "DismantleFormat", "Dismantle {0}"),
                recipe->BuildingName);
        }
    }
    return FText::FromString("Dismantle");
}
