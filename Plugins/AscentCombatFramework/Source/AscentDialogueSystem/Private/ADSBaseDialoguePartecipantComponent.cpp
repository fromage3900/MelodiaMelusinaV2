// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ADSBaseDialoguePartecipantComponent.h"
#include "ADSDialogueFunctionLibrary.h"
#include "ADSDialogueMasterComponent.h"
#include "CineCameraActor.h"
#include <GameFramework/PlayerController.h>
#include <Kismet/GameplayStatics.h>
#include <Kismet/KismetMathLibrary.h>
#include "Net/UnrealNetwork.h"

UADSBaseDialoguePartecipantComponent::UADSBaseDialoguePartecipantComponent()
{
    PrimaryComponentTick.bCanEverTick = false;
}

bool UADSBaseDialoguePartecipantComponent::TryStartDialogue(const TArray<UADSBaseDialoguePartecipantComponent*>& participants, UADSDialogue* dialogueToStart)
{
    UE_LOG(LogTemp, Warning, TEXT("Base TryStartDialogue called - should be overridden in derived class!"));
    return false;
}

bool UADSBaseDialoguePartecipantComponent::TryStartDialogueFromActors(const TArray<AActor*>& participants, UADSDialogue* dialogueToStart)
{
    UE_LOG(LogTemp, Warning, TEXT("Base TryStartDialogueFromActors called - should be overridden in derived class!"));
    return false;
}

UADSDialogue* UADSBaseDialoguePartecipantComponent::GetDialogue(FGameplayTag dialogueTag, bool& bFound) const
{
    UE_LOG(LogTemp, Warning, TEXT("Base GetDialogue called - should be overridden in derived class!"));
    bFound = false;
    return nullptr;
}

void UADSBaseDialoguePartecipantComponent::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
	Super::GetLifetimeReplicatedProps(OutLifetimeProps);

	DOREPLIFETIME(UADSBaseDialoguePartecipantComponent, PartecipantTag);
	DOREPLIFETIME(UADSBaseDialoguePartecipantComponent, ParticipantNameText);
	DOREPLIFETIME(UADSBaseDialoguePartecipantComponent, DefaultCameraConfig);
	DOREPLIFETIME(UADSBaseDialoguePartecipantComponent, bIsInDialogue);
}

void UADSBaseDialoguePartecipantComponent::OnDialogueStartedEvent_Implementation()
{
	bIsInDialogue = true;
}

void UADSBaseDialoguePartecipantComponent::OnDialogueEndedEvent_Implementation()
{
	bIsInDialogue = false;
}

UADSCameraConfigDataAsset* UADSBaseDialoguePartecipantComponent::GetDefaultCameraAsset() const
{
    return GetDefaultCameraConfig();
}

UADSBaseDialoguePartecipantComponent* UADSBaseDialoguePartecipantComponent::GetDialogueComponentFromActor(AActor* InActor)
{
    if (!InActor) {
        UE_LOG(LogTemp, Error, TEXT("GetDialogueComponentFromActor called with null actor!"));
        return nullptr;
    }

    UADSBaseDialoguePartecipantComponent* Component = InActor->FindComponentByClass<UADSBaseDialoguePartecipantComponent>();
    if (Component) {
        UE_LOG(LogTemp, Log, TEXT("Found dialogue component on %s, type: %s, name: %s"),
            *InActor->GetName(),
            *Component->GetClass()->GetName(),
            *Component->GetInteractableName().ToString());
    } else {
        UE_LOG(LogTemp, Error, TEXT("No dialogue component found on %s!"), *InActor->GetName());
    }
    return Component;
}

void UADSBaseDialoguePartecipantComponent::SetCamera(const FDialogueCinematic& cameraSettings)
{
    const APlayerController* controller = UGameplayStatics::GetPlayerController(this, 0);
    UADSDialogueMasterComponent* dialogueMaster = UADSDialogueFunctionLibrary::GetLocalDialogueMaster(this);
    if (dialogueMaster) {
        dialogueMaster->ApplyDialogueCinematic(this, cameraSettings);
    }
}

void UADSBaseDialoguePartecipantComponent::SetDefaultCameraAndPosition()
{
    if (bShouldMovePlayer) {
        SetPosition(DefaultEnforcedPlayerPosition);
    }
    if (GetDefaultCameraConfig()) {
        APlayerController* controller = UGameplayStatics::GetPlayerController(this, 0);
        if (controller) {
            UADSDialogueMasterComponent* dialogueMaster = UADSDialogueFunctionLibrary::GetLocalDialogueMaster(GetOwner());
            if (dialogueMaster) {
                dialogueMaster->ApplyCameralShot(GetDefaultCameraConfig(), GetOwner(), controller);
            } else {
                UE_LOG(LogTemp, Warning, TEXT("No dialogue master found to set default camera!"));
            }
        } else {
            UE_LOG(LogTemp, Warning, TEXT("No player controller found to set default camera!"));
        }
    } else {
        UE_LOG(LogTemp, Warning, TEXT("No default camera config set!"));
    }
}

void UADSBaseDialoguePartecipantComponent::SetPosition(const FVector& EnforcedPlayerPosition)
{
    const APlayerController* controller = UGameplayStatics::GetPlayerController(this, 0);
    const AActor* dialogueStarter = GetOwner();
    if (controller && dialogueStarter && controller->GetPawn()) {
        UADSDialogueMasterComponent* dialogueMaster = UADSDialogueFunctionLibrary::GetLocalDialogueMaster(dialogueStarter);
        if (dialogueMaster) {
            // Get NPC transform
            const FVector NPCLocation = dialogueStarter->GetActorLocation();
            const FRotator NPCRotation = dialogueStarter->GetActorRotation();

            // Transform offset from local space (relative to NPC forward) to world space
            const FVector WorldOffset = NPCRotation.RotateVector(EnforcedPlayerPosition);
            const FVector PlayerWorldPosition = NPCLocation + WorldOffset;

            // Calculate player rotation to look at NPC
            const FRotator PlayerRotation = UKismetMathLibrary::FindLookAtRotation(PlayerWorldPosition, NPCLocation);

            const FTransform NewPlayerTransform(PlayerRotation, PlayerWorldPosition);
            dialogueMaster->MoveControlledPlayerToPosition(NewPlayerTransform);
        }
    }
}
