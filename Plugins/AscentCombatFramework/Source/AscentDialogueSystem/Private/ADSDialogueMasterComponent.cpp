// // Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ADSDialogueMasterComponent.h"

#include "ADSBaseDialoguePartecipantComponent.h"
#include "ADSCameraConfigDataAsset.h"
#include "ADSTypes.h"
#include <CineCameraActor.h>
#include <CineCameraComponent.h>
#include <Engine/World.h>
#include <GameFramework/Pawn.h>
#include <GameFramework/PlayerController.h>
#include <Kismet/GameplayStatics.h>
#include <LevelSequence.h>
#include <LevelSequenceActor.h>
#include <LevelSequencePlayer.h>
#include <MovieSceneSequencePlayer.h>

// Sets default values for this component's properties
UADSDialogueMasterComponent::UADSDialogueMasterComponent()
{
    // Set this component to be initialized when the game starts, and to be ticked every frame.  You can turn these features
    // off to improve performance if you don't need them.
    PrimaryComponentTick.bCanEverTick = false;
    SetIsReplicatedByDefault(true);

    // ...
}

void UADSDialogueMasterComponent::AddDialogueVariable(FString key, FString value)
{
    DialogueVariables.Add(key, value);
}

void UADSDialogueMasterComponent::RemoveDialogueVariable(FString key)
{
    DialogueVariables.Remove(key);
}

bool UADSDialogueMasterComponent::GetDialogueVariable(FString key, FString& outValue) const
{
    if (DialogueVariables.Contains(key)) {
        outValue = *DialogueVariables.Find(key);
        return true;
    }
    return false;
}

FText UADSDialogueMasterComponent::ReplaceVariablesInText(const FText& inText)
{
    FString outString = inText.ToString();

    // Iterate over the map
    for (const TPair<FString, FString>& Pair : DialogueVariables) {
        outString = outString.Replace(*Pair.Key, *Pair.Value, ESearchCase::IgnoreCase);
    }

    return FText::FromString(outString);
}

void UADSDialogueMasterComponent::MoveControlledPlayerToPosition_Implementation(const FTransform& finalPoint)
{
    APlayerController* pc = Cast<APlayerController>(GetOwner());

    if (pc && pc->GetPawn()) {
        pc->GetPawn()->SetActorLocation(finalPoint.GetLocation());
        pc->GetPawn()->SetActorRotation(finalPoint.GetRotation());
    }
}

// Called when the game starts
void UADSDialogueMasterComponent::BeginPlay()
{
    Super::BeginPlay();

    // ...
}

void UADSDialogueMasterComponent::ApplyDialogueCinematic(UADSBaseDialoguePartecipantComponent* Speaker, const FDialogueCinematic& NodeCinematic)
{
    if (!Speaker) {

        return;
    }

    APlayerController* PC = UGameplayStatics::GetPlayerController(this, 0);
    switch (NodeCinematic.CinematicType) {
    case EDialogueCinematicType::CameraConfig: {
        UADSCameraConfigDataAsset* ShotToUse = NodeCinematic.CameraConfig;

        if (ShotToUse) {
            ApplyCameralShot(ShotToUse, Speaker->GetOwner(), PC);
        }
        break;
    }
    case EDialogueCinematicType::Sequencer: {
        ULevelSequence* SequenceToUse = NodeCinematic.LevelSequence;

        if (SequenceToUse) {
            PlayLevelSequence(SequenceToUse, PC);
        }
        break;
    }
    case EDialogueCinematicType::None:
    default:
        // No cinematic
        break;
    }
}

void UADSDialogueMasterComponent::EndDialogueCinematic()
{
    APlayerController* PC = GetWorld()->GetFirstPlayerController();

    // Stop sequence if active
    StopLevelSequence();

    if (PC && PC->GetPawn()) {
        // Return to player
        PC->SetViewTargetWithBlend(PC->GetPawn(), .1f, VTBlend_Cubic);
    }
}

// Apply a procedural shot
void UADSDialogueMasterComponent::ApplyCameralShot(UADSCameraConfigDataAsset* ShotAsset, const AActor* Speaker, APlayerController* PlayerController)
{
    if (!ShotAsset || !Speaker || !PlayerController) {
        return;
    }

    TObjectPtr<ACineCameraActor> Camera = GetDialogueCamera();

    ConfigureCamera(Camera, ShotAsset, Speaker);

    CurrentShot = ShotAsset;
    // Blend to camera
    PlayerController->SetViewTargetWithBlend(Camera, ShotAsset->BlendTime, ShotAsset->BlendFunction);
}

void UADSDialogueMasterComponent::StopCurrentShot()
{
    APlayerController* controller = GetWorld()->GetFirstPlayerController();

    if (controller && CurrentShot) {
        controller->SetViewTargetWithBlend(controller->GetPawn(), CurrentShot->BlendTime, CurrentShot->BlendFunction);
    }
}

// Start level sequence
void UADSDialogueMasterComponent::PlayLevelSequence(ULevelSequence* Sequence, APlayerController* PlayerController)
{
    if (!Sequence || !PlayerController) {
        return;
    }

    UWorld* World = PlayerController->GetWorld();
    if (!World) {
        return;
    }

    // Stop previous sequence if active
    StopLevelSequence();

    // Spawn sequence actor
    FActorSpawnParameters SpawnParams;
    SequenceActor = World->SpawnActor<ALevelSequenceActor>(SpawnParams);

    if (SequenceActor) {
        SequenceActor->SetSequence(Sequence);
        SequencePlayer = SequenceActor->GetSequencePlayer();

        if (SequencePlayer) {
            SequencePlayer->Play();
        }
    }
}

// Stop active sequence
void UADSDialogueMasterComponent::StopLevelSequence()
{
    if (SequencePlayer) {
        SequencePlayer->Stop();
        SequencePlayer = nullptr;
    }

    if (SequenceActor) {
        SequenceActor->Destroy();
        SequenceActor = nullptr;
    }
}

// Spawn or reuse camera
TObjectPtr<ACineCameraActor> UADSDialogueMasterComponent::GetDialogueCamera()
{
    if (!DialogueCamera || !IsValid(DialogueCamera)) {
        FActorSpawnParameters SpawnParams;
        DialogueCamera = GetWorld()->SpawnActor<ACineCameraActor>(DialogueCameraClass, SpawnParams);
    }
    return DialogueCamera;
}

// Configure camera with shot parameters
void UADSDialogueMasterComponent::ConfigureCamera(ACineCameraActor* Camera, const UADSCameraConfigDataAsset* ShotAsset, const AActor* Speaker)
{
    if (!Camera || !ShotAsset || !Speaker) {
        return;
    }

    // Get speaker transform
    const FVector SpeakerLocation = Speaker->GetActorLocation();
    const FRotator SpeakerRotation = Speaker->GetActorRotation();

    // Transform offset from local space (relative to speaker forward) to world space
    const FVector WorldOffset = SpeakerRotation.RotateVector(ShotAsset->CameraOffset);
    const FVector CameraLocation = SpeakerLocation + WorldOffset;

    // Calculate rotation
    FRotator CameraRotation = FRotator::ZeroRotator;
    if (ShotAsset->LookatTrackingSettings.bEnableLookAtTracking) {
        const FVector LookDirection = (SpeakerLocation - CameraLocation).GetSafeNormal();
        CameraRotation = LookDirection.Rotation();
    } else {
        // Keep same rotation as speaker + any offset from shot asset
        CameraRotation = SpeakerRotation;
    }

    // Position camera
    Camera->SetActorLocation(CameraLocation);
    Camera->SetActorRotation(CameraRotation);

    // Configure camera parameters
    TObjectPtr<UCineCameraComponent> CameraComp = Camera->GetCineCameraComponent();
    if (CameraComp) {
        CameraComp->SetFieldOfView(ShotAsset->FOV);
        CameraComp->CurrentFocalLength = ShotAsset->FocalLength;
        CameraComp->CurrentAperture = ShotAsset->Aperture;

        // Apply complete camera settings
        CameraComp->SetFocusSettings(ShotAsset->FocusSettings);
        Camera->LookatTrackingSettings = ShotAsset->LookatTrackingSettings;

        // Override tracking target to current speaker
        if (ShotAsset->LookatTrackingSettings.bEnableLookAtTracking) {
            Camera->LookatTrackingSettings.ActorToTrack = const_cast<AActor*>(Speaker);
        }

        if (ShotAsset->FocusSettings.FocusMethod == ECameraFocusMethod::Tracking) {
            CameraComp->FocusSettings.TrackingFocusSettings.ActorToTrack = const_cast<AActor*>(Speaker);
        }
    }
}
