// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ALSSaveTask.h"
#include "ALSFunctionLibrary.h"
#include "ALSLoadAndSaveSubsystem.h"
#include "ALSSavableInterface.h"
#include "ALSSaveGame.h"
#include "ALSSaveGameSettings.h"
#include "ALSSaveInfo.h"
#include "ALSSaveTypes.h"
#include "Engine/LevelStreaming.h"
#include "GameFramework/Actor.h"
#include "GameFramework/GameMode.h"
#include "GameFramework/GameModeBase.h"
#include "GameFramework/GameState.h"
#include "GameFramework/GameStateBase.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/PlayerState.h"
#include "Kismet/GameplayStatics.h"
#include "Serialization/ObjectAndNameAsStringProxyArchive.h"
#include <Async/TaskGraphInterfaces.h>

void FSaveWorldTask::DoWork()
{
    if (!world) {
        FinishSave(false);
        return;
    }

    const UALSSaveGameSettings* saveSettings = GetMutableDefault<UALSSaveGameSettings>();
    if (!saveSettings) {
        FinishSave(false);
        return;
    }
    UALSLoadAndSaveSubsystem* saveSusbsystem = UGameplayStatics::GetGameInstance(world)->GetSubsystem<UALSLoadAndSaveSubsystem>();

    const TSubclassOf<UALSSaveGame> saveClass = saveSettings->GetSaveGameClass();
    if (!saveClass) {
        FinishSave(false);
        return;
    }
    newSave = saveSusbsystem->GetOrCreateCurrentSaveGame(); // Cast<UALSSaveGame>(UGameplayStatics::CreateSaveGameObject(saveClass));

    if (!newSave) {
        FinishSave(false);
        return;
    }
    FALSLevelData currentLevel;
    const FString levelName = UGameplayStatics::GetCurrentLevelName(world, true);

    const bool bAlreadyAdded = newSave->TryGetLevelData(levelName, currentLevel);

    currentLevel.CleanActors();

    for (const auto& actor : SavableActors) {
        if (!actor) {
            continue;
        }
        if (!UALSFunctionLibrary::ShouldSaveActor(actor)) {
            continue;
        }
        if (UALSFunctionLibrary::IsSpecialActor(world, actor)) {
            continue;
        }
        FALSActorData actorData = SerializeActor(actor);
        currentLevel.AddActorRecord(actorData);
    }
    UALSSaveInfo* saveInfo = saveSusbsystem->LoadOrCreateSaveInfo();
    if (!saveInfo) {
        FinishSave(false);
    }

    const FTimespan SessionDuration = FDateTime::Now() - saveSusbsystem->GetStartPlayTime();

    FALSSaveMetadata saveMetaData;
    saveMetaData.MapToLoad = levelName;
    saveMetaData.Data = FDateTime::Now();
    saveMetaData.SaveName = saveName;
    saveMetaData.SaveDescription = slotDesc;
    saveMetaData.PlayTime = newSave->GetPlayTime() + SessionDuration.GetTotalSeconds();
    saveInfo->AddSlot(saveMetaData);

    newSave->SetPlayTime(saveMetaData.PlayTime);
    saveSusbsystem->StartPlaytimeTracking();

    newSave->AddLevel(saveMetaData.MapToLoad, currentLevel);

    StoreLocalPlayer();

    StoreGameState();

    StorePlayerState();

    newSave->OnSaved();
    UGameplayStatics::SaveGameToSlot(newSave, saveName, 0);

    UGameplayStatics::SaveGameToSlot(saveInfo, saveSettings->GetSaveMetadataName(), 0);

    FinishSave(true);
}

FALSActorData FSaveWorldTask::SerializeActor(AActor* actor)
{
    FALSActorData outData = UALSFunctionLibrary::SerializeActor(actor);
    SuccessfullySavedActors.Add(actor);
    return outData;
}

void FSaveWorldTask::FinishSave(const bool bSuccess)
{
    if (IsInGameThread()) {
        UGameplayStatics::GetGameInstance(this->world)->GetSubsystem<UALSLoadAndSaveSubsystem>()->FinishSaveWork(bSuccess);
    } else {
        FSimpleDelegateGraphTask::CreateAndDispatchWhenReady(
            FSimpleDelegateGraphTask::FDelegate::CreateStatic(
                &GFinishSave, world,
                bSuccess),
            GetStatId(),
            nullptr, ENamedThreads::GameThread);
    }
}

void FSaveWorldTask::StoreLocalPlayer()
{
    APlayerController* playerCont = UGameplayStatics::GetPlayerController(world, 0);
    APawn* pawn = UGameplayStatics::GetPlayerPawn(world, 0);
    if (UALSFunctionLibrary::ShouldSaveActor(playerCont) && UALSFunctionLibrary::ShouldSaveActor(pawn)) {
        const FALSActorData pcData = SerializeActor(playerCont);
        const FALSActorData pawnData = SerializeActor(pawn);
        FALSPlayerData playerData(pcData, pawnData);
        newSave->StoreLocalPlayer(playerData);
    } else {
        UE_LOG(LogTemp, Error,
            TEXT("Player Controller or Pawn does not implement savable interface! - FSaveWorldTask::StoreLocalPlayer"));
    }
}

void FSaveWorldTask::StoreGameState()
{
    AGameStateBase* gameState = UGameplayStatics::GetGameState(world);
    if (!UALSFunctionLibrary::ShouldSaveActor(gameState)) {
        return;
    }
    const FALSActorData gameStateData = SerializeActor(gameState);
    newSave->StoreGameState(gameStateData);
}

void FSaveWorldTask::StorePlayerState()
{
    APlayerController* playerCont = UGameplayStatics::GetPlayerController(world, 0);
    if (!playerCont) {
        return;
    }
    APlayerState* playerState = playerCont->PlayerState;
    if (!UALSFunctionLibrary::ShouldSaveActor(playerState)) {
        return;
    }
    const FALSActorData playerStateData = SerializeActor(playerState);
    newSave->StorePlayerState(playerStateData);
}
