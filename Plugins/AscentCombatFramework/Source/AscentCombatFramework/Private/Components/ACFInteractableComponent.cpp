// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "Components/ACFInteractableComponent.h"
#include "GameFramework/Pawn.h"
#include "Net/UnrealNetwork.h"

UACFInteractableComponent::UACFInteractableComponent()
{
    PrimaryComponentTick.bCanEverTick = false;
    SetIsReplicatedByDefault(true);

    DefaultInteractableName = FText::FromString(TEXT("Interact"));
}

void UACFInteractableComponent::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(UACFInteractableComponent, InteractionState);
}

// ── Handle* helpers ───────────────────────────────────────────────────────────

void UACFInteractableComponent::HandleInteractedByPawn(APawn* Pawn, const FString& InteractionType)
{
    if (!Pawn || !CanBeInteracted(Pawn))
    {
        return;
    }

    LastInteractorPawn = Pawn;

    if (!bAllowInteractionWhileBusy)
    {
        Internal_SetState(EACFInteractionState::EBusy);
    }

    OnInteractionOccurred.Broadcast(Pawn);

}

void UACFInteractableComponent::HandleLocalInteractedByPawn(APawn* Pawn, const FString& InteractionType)
{
    if (Pawn)
    {
        OnLocalInteractionOccurred.Broadcast(Pawn);
    }
}

void UACFInteractableComponent::HandleInteractableRegisteredByPawn(APawn* Pawn)
{
    CurrentRegisteredInteractor = Pawn;
    if (Pawn)
    {
        OnInteractorRegistered.Broadcast(Pawn);
    }
}

void UACFInteractableComponent::HandleInteractableUnregisteredByPawn(APawn* Pawn)
{
    if (CurrentRegisteredInteractor == Pawn)
    {
        CurrentRegisteredInteractor = nullptr;
    }

    if (Pawn)
    {
        OnInteractorUnregistered.Broadcast(Pawn);
    }

    if (bResetStateOnUnregister)
    {
        Internal_SetState(EACFInteractionState::EFree);
    }
}

// ── State management ──────────────────────────────────────────────────────────

void UACFInteractableComponent::EndInteraction()
{
    Internal_SetState(EACFInteractionState::EFree);
}

void UACFInteractableComponent::SetInteractionState(EACFInteractionState NewState)
{
    Internal_SetState(NewState);
}

// ── Public getters ────────────────────────────────────────────────────────────

bool UACFInteractableComponent::CanBeInteracted(APawn* Pawn) const
{
    if (!bInteractionEnabled)
    {
        return false;
    }

    if (!bAllowInteractionWhileBusy && InteractionState == EACFInteractionState::EBusy)
    {
        return false;
    }

    return true;
}

// ── Setters ───────────────────────────────────────────────────────────────────

void UACFInteractableComponent::SetInteractionEnabled(bool bEnabled)
{
    bInteractionEnabled = bEnabled;
}

// ── Internal ──────────────────────────────────────────────────────────────────

void UACFInteractableComponent::Internal_SetState(EACFInteractionState NewState)
{
    if (InteractionState == NewState)
    {
        return;
    }

    InteractionState = NewState;
    OnInteractionStateChanged.Broadcast(NewState);
}

void UACFInteractableComponent::OnRep_InteractionState()
{
    // Broadcast on clients so UI and Blueprints react to state changes
    OnInteractionStateChanged.Broadcast(InteractionState);
}
