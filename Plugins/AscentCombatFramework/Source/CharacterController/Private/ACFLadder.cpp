// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ACFLadder.h"

AACFLadder::AACFLadder()
{
    PrimaryActorTick.bCanEverTick = false;
}

// ── IACFInteractableInterface ─────────────────────────────────────────────────

void AACFLadder::OnInteractedByPawn_Implementation(APawn* Pawn, const FString& interactionType)
{
}

void AACFLadder::OnLocalInteractedByPawn_Implementation(APawn* Pawn, const FString& interactionType)
{
}

void AACFLadder::OnInteractableRegisteredByPawn_Implementation(APawn* Pawn)
{
}

void AACFLadder::OnInteractableUnregisteredByPawn_Implementation(APawn* Pawn)
{
}

FText AACFLadder::GetInteractableName_Implementation()
{
    return FText::GetEmpty();
}
