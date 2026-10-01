// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "Actors/ACFBaseInteractableActor.h"
#include "Components/ACFInteractableComponent.h"
#include "Components/SceneComponent.h"

AACFBaseInteractableActor::AACFBaseInteractableActor()
{
    PrimaryActorTick.bCanEverTick = false;

    SceneRoot = CreateDefaultSubobject<USceneComponent>(TEXT("SceneRoot"));
    SetRootComponent(SceneRoot);

    InteractableComponent = CreateDefaultSubobject<UACFInteractableComponent>(TEXT("InteractableComponent"));
    InteractableComponent->SetupAttachment(SceneRoot);
}

FText AACFBaseInteractableActor::GetInteractableName_Implementation()
{
    return InteractableComponent ? InteractableComponent->GetInteractableName() : FText::GetEmpty();
}
