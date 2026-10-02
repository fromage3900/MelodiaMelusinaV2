// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ALSLoadAndSaveSubsystem.h"
#include "ALSFunctionLibrary.h"
#include "ALSLoadAndSaveComponent.h"
#include "ALSSaveGameSettings.h"
#include "ALSSaveInfo.h"
#include "Engine/GameInstance.h"
#include "Kismet/GameplayStatics.h"
#include <GameFramework/Pawn.h>
#include <Serialization/MemoryReader.h>
#include <Serialization/MemoryWriter.h>

void UALSLoadAndSaveSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
	FCoreUObjectDelegates::PostLoadMapWithWorld.AddUObject(this, &UALSLoadAndSaveSubsystem::HandleLoadingFinished);
	bIsNewGame = true;
	StartPlaytimeTracking();
}

void UALSLoadAndSaveSubsystem::Deinitialize()
{
	FCoreUObjectDelegates::PostLoadMapWithWorld.RemoveAll(this);
	currentSavegame = nullptr;

}

void UALSLoadAndSaveSubsystem::SaveGameWorld(const FString& slotName, const FOnSaveFinished& saveCallback,
	const bool bSaveLocalPlayer /*= true*/, const bool bSaveScreenshot /*= true*/, const FString& slotDescription)
{
	if (systemState != ELoadingState::EIdle) {
		saveCallback.ExecuteIfBound(false);
		UE_LOG(LogTemp, Warning, TEXT("You are already loading or saving!"));
		return;
	}
	currentSaveSlot = slotName;
	onSaveFinishedInternal = saveCallback;
	bSaveScreen = bSaveScreenshot;
	currentSavegame = LoadOrCreateSaveGame(slotName);
	systemState = ELoadingState::ESaving;
	(new FAutoDeleteAsyncTask<FSaveWorldTask>(slotName, GetWorld(), bSaveLocalPlayer, slotDescription))->StartBackgroundTask();
}

void UALSLoadAndSaveSubsystem::SaveGameWorldInCurrentSlot(const FOnSaveFinished& saveCallback, const bool bSaveLocalPlayer /*= true*/,
	const bool bSaveScreenshot /*= true*/, const FString& slotDescription)
{
	SaveGameWorld(currentSaveSlot, saveCallback, bSaveLocalPlayer, bSaveScreenshot, slotDescription);
}

void UALSLoadAndSaveSubsystem::LoadGameWorld(const FString& slotName, const FOnLoadFinished& loadCallback, bool reloadPlayer)
{
	if (systemState != ELoadingState::EIdle) {
		loadCallback.ExecuteIfBound(false);
		UE_LOG(LogTemp, Warning, TEXT("You are already loading or saving!"));
		return;
	}

	FALSSaveMetadata saveToBeLoaded;
	if (TryGetSaveMetadata(slotName, saveToBeLoaded)) {
		currentSaveSlot = slotName;
		onLoadedCallbackInternal = loadCallback;
		SetLoadType(ELoadType::EFullReload);
		systemState = ELoadingState::ELoading;
		bReloadPlayer = reloadPlayer;
		bIsNewGame = false;
		UGameplayStatics::OpenLevel(this, *saveToBeLoaded.MapToLoad);
	}
	else if (UGameplayStatics::DoesSaveGameExist(slotName, 0)) {
		UE_LOG(LogTemp, Warning,
			TEXT("[ALS] LoadGameWorld: metadata missing for slot \"%s\" - reloading current map."), *slotName);
		currentSaveSlot = slotName;
		onLoadedCallbackInternal = loadCallback;
		SetLoadType(ELoadType::EFullReload);
		systemState = ELoadingState::ELoading;
		bReloadPlayer = reloadPlayer;
		bIsNewGame = false;
		UGameplayStatics::OpenLevel(this, *UGameplayStatics::GetCurrentLevelName(GetWorld(), true));
	}
	else {
		loadCallback.ExecuteIfBound(false);
	}
}

bool UALSLoadAndSaveSubsystem::SaveLocalPlayer(const FString& slotName)
{

	UALSSaveInfo* saveInfo = LoadOrCreateSaveInfo();
	if (!saveInfo) {
		return false;
	}
	FALSSaveMetadata saveMetaData;
	saveMetaData.Data = FDateTime::Now();
	saveMetaData.SaveName = slotName;
	saveInfo->AddSlot(saveMetaData);
	const UALSSaveGameSettings* saveSettings = GetMutableDefault<UALSSaveGameSettings>();
	if (!saveSettings) {
		return false;
	}

	UALSSaveGame* saveGame = LoadOrCreateSaveGame(slotName);
	if (!saveGame) {
		return false;
	}

	FALSPlayerData newData;
	if (CreatePlayerData(newData)) {
		saveGame->StoreLocalPlayer(newData);
		UGameplayStatics::SaveGameToSlot(saveGame, slotName, 0);
		UGameplayStatics::SaveGameToSlot(saveInfo, saveSettings->GetSaveMetadataName(), 0);
		currentSaveSlot = slotName;
		return true;
	}

	return false;
}

bool UALSLoadAndSaveSubsystem::CreatePlayerData(FALSPlayerData& outData)
{
	APlayerController* playerCont = UGameplayStatics::GetPlayerController(GetWorld(), 0);
	APawn* pawn = UGameplayStatics::GetPlayerPawn(GetWorld(), 0);
	if (playerCont, pawn) {
		const FALSActorData pcData = UALSFunctionLibrary::SerializeActor(playerCont);

		const FALSActorData pawnData = UALSFunctionLibrary::SerializeActor(pawn);

		outData = FALSPlayerData(pcData, pawnData);
		return true;
	}
	return false;
}

bool UALSLoadAndSaveSubsystem::SaveActor(AActor* actorToSave)
{
	if (!currentSavegame) {
		UE_LOG(LogTemp, Warning, TEXT("There is no valid savegame!"));
		const UALSSaveGameSettings* saveSettings = GetMutableDefault<UALSSaveGameSettings>();
		currentSavegame = Cast<UALSSaveGame>(UGameplayStatics::CreateSaveGameObject(saveSettings->GetSaveGameClass()));
	}

	if (actorToSave && currentSavegame) {
		const FALSActorData pcData = UALSFunctionLibrary::SerializeActor(actorToSave);
		const FString levelName = UGameplayStatics::GetCurrentLevelName(actorToSave, true);
		currentSavegame->StoreWPActors(levelName, pcData);
		return true;
	}
	return false;
}

bool UALSLoadAndSaveSubsystem::LoadActor(AActor* actorToLoad)
{
	if (!actorToLoad) {
		return false;
	}

	const FString levelName = UGameplayStatics::GetCurrentLevelName(actorToLoad, true);

	FALSActorData outActor;
	if (currentSavegame) {
		// FullDeserializeActor (not DeserializeActor) so this per-actor path invokes
		// IALSSavableInterface::OnLoaded / OnComponentLoaded exactly like the full
		// world-load path does - a savable actor must behave consistently regardless
		// of which reload path restores it.
		//
		// The level record is checked FIRST: it is rebuilt from the live world on every
		// full save, so when both records exist it is the freshest complete snapshot
		// (including the transform). The WPActors record is a per-actor save taken
		// earlier in the session and acts as a fallback for actors that were missing
		// from the last world save (e.g. saved right before being destroyed).
		// The class check mirrors FLoadWorldTask::DeserializeActor: a record whose
		// class differs from the live actor belongs to a different object (stale
		// slot, recompiled BP, key collision) and must never be applied - restoring
		// it would overwrite this actor's data and teleport it to the record's
		// transform.
		FALSLevelData levelData;
		if (currentSavegame->TryGetLevelData(levelName, levelData)) {
			const FALSActorData* actorData = levelData.GetActorData(actorToLoad);
			if (actorData && actorData->Class == actorToLoad->GetClass()) {
				UALSFunctionLibrary::FullDeserializeActor(actorToLoad, *actorData, /*bLoadTransform=*/true);
				return true;
			}
		}

		if (currentSavegame->TryGetStoredWPActor(levelName, actorToLoad, outActor)
			&& outActor.Class == actorToLoad->GetClass()) {
			UALSFunctionLibrary::FullDeserializeActor(actorToLoad, outActor, /*bLoadTransform=*/true);
			return true;
		}
	}
	return false;
}

bool UALSLoadAndSaveSubsystem::LoadLocalPlayer(const FString& slotName, bool bReloadTransform)
{
	const UALSSaveGameSettings* saveSettings = GetMutableDefault<UALSSaveGameSettings>();

	UALSSaveGame* saveGame = LoadOrCreateSaveGame(slotName);
	if (!saveGame) {
		return false;
	}

	if (!saveSettings) {
		return false;
	}
	FALSPlayerData outData;
	saveGame->GetLocalPlayer(outData);
	RestorePlayerData(outData, bReloadTransform);

	currentSaveSlot = slotName;
	return true;
}

bool UALSLoadAndSaveSubsystem::RestorePlayerData(const FALSPlayerData& inData, bool bReloadTransform)
{
	APlayerController* playerCont = UGameplayStatics::GetPlayerController(GetWorld(), 0);
	APawn* pawn = UGameplayStatics::GetPlayerPawn(GetWorld(), 0);
	FALSActorData playerData;
	if (playerCont) {
		UALSFunctionLibrary::FullDeserializeActor(pawn,
			inData.Pawn, bReloadTransform);
		UALSFunctionLibrary::FullDeserializeActor(playerCont,
			inData.PlayerController, bReloadTransform);
		return true;
	}

	return false;
}

bool UALSLoadAndSaveSubsystem::SavePlayer(const FString& slotName, const FString& playerID, APlayerController* playerToSave)
{
	UALSSaveGame* saveGame = LoadOrCreateSaveGame(slotName);
	if (!saveGame) {
		return false;
	}
	const FALSActorData pcData = UALSFunctionLibrary::SerializeActor(playerToSave);
	APawn* pawn = playerToSave->GetPawn();
	const FALSActorData pawnData = UALSFunctionLibrary::SerializeActor(pawn);

	FALSPlayerData playerData(pcData, pawnData);
	saveGame->StorePlayer(slotName, playerData);
	CreateOrUpdateSlotInfo(slotName);
	currentSaveSlot = slotName;

	return UGameplayStatics::SaveGameToSlot(saveGame, slotName, 0);
}

bool UALSLoadAndSaveSubsystem::CreateOrUpdateSlotInfo(const FString& slotName)
{
	UALSSaveInfo* saveInfo = LoadOrCreateSaveInfo();
	if (!saveInfo) {
		return false;
	}
	FALSSaveMetadata saveMetaData;
	saveMetaData.Data = FDateTime::Now();
	saveMetaData.SaveName = slotName;

	saveInfo->AddSlot(saveMetaData);
	const UALSSaveGameSettings* saveSettings = GetMutableDefault<UALSSaveGameSettings>();
	if (!saveSettings) {
		return false;
	}
	return UGameplayStatics::SaveGameToSlot(saveInfo, saveSettings->GetSaveMetadataName(), 0);
}

bool UALSLoadAndSaveSubsystem::RemoveSlotInfo(const FString& slotName)
{
	UALSSaveInfo* saveInfo = LoadOrCreateSaveInfo();
	if (!saveInfo) {
		return false;
	}

	saveInfo->DeleteSlot(slotName);
	const UALSSaveGameSettings* saveSettings = GetMutableDefault<UALSSaveGameSettings>();
	if (!saveSettings) {
		return false;
	}
	return UGameplayStatics::SaveGameToSlot(saveInfo, saveSettings->GetSaveMetadataName(), 0);
}

bool UALSLoadAndSaveSubsystem::LoadPlayer(const FString& slotName, const FString& playerID, APlayerController* playerToLoad, bool bReloadTransform)
{
	UALSSaveGame* saveGame = LoadOrCreateSaveGame(slotName);
	if (!saveGame) {
		return false;
	}
	if (!playerToLoad) {
		return false;
	}

	FALSPlayerData outData;
	if (saveGame->TryGetPlayer(playerID, outData)) {
		UALSFunctionLibrary::FullDeserializeActor(playerToLoad, outData.PlayerController, bReloadTransform);
		UALSFunctionLibrary::FullDeserializeActor(playerToLoad->GetPawn(), outData.Pawn, bReloadTransform);
		currentSaveSlot = slotName;
		return true;
	}
	else {
		UE_LOG(LogTemp, Warning, TEXT("There are no Players with the provided ID in SaveSlot !"));
		return false;
	}
}

void UALSLoadAndSaveSubsystem::LoadCurrentLevel(const FString& slotName, const FOnLoadFinished& loadCallback, bool bReloadLocalPlayer /*= false*/)
{
	const FString levelName = UGameplayStatics::GetCurrentLevelName(GetWorld());
	LoadLevelFromSaveGame(slotName, levelName, loadCallback, bReloadLocalPlayer);
}

void UALSLoadAndSaveSubsystem::LoadLevelFromSaveGame(const FString& slotName, const FString& levelName, const FOnLoadFinished& loadCallback, bool bReloadLocalPlayer /*= false*/)
{
	if (systemState != ELoadingState::EIdle) {
		loadCallback.ExecuteIfBound(false);
		UE_LOG(LogTemp, Warning, TEXT("You are already loading or saving!"));
		return;
	}

	FALSSaveMetadata saveToBeLoaded;
	if (TryGetSaveMetadata(slotName, saveToBeLoaded)) {
		onLoadedCallbackInternal = loadCallback;
		SetLoadType(ELoadType::EFullReload);
		systemState = ELoadingState::ELoading;
		currentSaveSlot = slotName;
		bReloadPlayer = bReloadLocalPlayer;
		bIsNewGame = false;
		AsyncLoadSaveGame(currentSaveSlot);
	}
	else {
		loadCallback.ExecuteIfBound(false);
	}
}

bool UALSLoadAndSaveSubsystem::TravelLocalPlayer()
{
	SetLoadType(ELoadType::EPlayerOnly);
	return CreatePlayerData(TravelingPlayer);
}

bool UALSLoadAndSaveSubsystem::LoadTraveledPlayer()
{
	if (loadType == ELoadType::EPlayerOnly) {
		SetLoadType(ELoadType::EDontReload);
		return RestorePlayerData(TravelingPlayer, false);
	}
	return false;
}

void UALSLoadAndSaveSubsystem::DeleteSlot(const FString tempSlot)
{
	UGameplayStatics::DeleteGameInSlot(tempSlot, 0);
	RemoveSlotInfo(tempSlot);
}

class UALSSaveGame* UALSLoadAndSaveSubsystem::GetOrCreateCurrentSaveGame()
{
	if (currentSavegame) {
		return currentSavegame;
	}
	const UALSSaveGameSettings* saveSettings = GetMutableDefault<UALSSaveGameSettings>();
	return Cast<UALSSaveGame>(UGameplayStatics::CreateSaveGameObject(saveSettings->GetSaveGameClass()));
}

bool UALSLoadAndSaveSubsystem::TryGetSaveMetadata(const FString& slotName, FALSSaveMetadata& outSaveMetadata) const
{
	const UALSSaveGameSettings* saveSettings = GetMutableDefault<UALSSaveGameSettings>();
	const UALSSaveInfo* saveMetadata = Cast<UALSSaveInfo>(UGameplayStatics::LoadGameFromSlot(saveSettings->GetSaveMetadataName(), 0));

	if (!saveMetadata) {
		return false;
	}

	return saveMetadata->TryGetSaveSlotData(slotName, outSaveMetadata);
}

TArray<FALSSaveMetadata> UALSLoadAndSaveSubsystem::GetAllSaveGames() const
{
	const UALSSaveGameSettings* saveSettings = GetMutableDefault<UALSSaveGameSettings>();
	const UALSSaveInfo* saveMetadata = Cast<UALSSaveInfo>(UGameplayStatics::LoadGameFromSlot(saveSettings->GetSaveMetadataName(), 0));

	if (saveMetadata) {
		return saveMetadata->GetSaveSlots();
	}

	return TArray<FALSSaveMetadata>();
}

bool UALSLoadAndSaveSubsystem::HasAnySaveGame() const
{
	return GetAllSaveGames().Num() > 0;
}

int32 UALSLoadAndSaveSubsystem::GetCurrentSlotNum() const
{
	return GetAllSaveGames().Num();
}

int32 UALSLoadAndSaveSubsystem::GetMaxSlotsNum() const
{
	const UALSSaveGameSettings* saveSettings = GetMutableDefault<UALSSaveGameSettings>();

	if (saveSettings) {
		return saveSettings->GetMaxSlotsNum();
	}

	return -1;
}

bool UALSLoadAndSaveSubsystem::CanAddNewSlot() const
{
	return GetAllSaveGames().Num() < GetMaxSlotsNum();
}

bool UALSLoadAndSaveSubsystem::IsSlotNameUnique(const FString& slotName) const
{
	return !GetAllSaveGames().Contains(slotName);
}

UTexture2D* UALSLoadAndSaveSubsystem::GetScreenshotForSave(const FString& saveName) const
{
	return UALSFunctionLibrary::GetScreenshotByName(saveName);
}

FString UALSLoadAndSaveSubsystem::GetDefaultSaveName() const
{
	const UALSSaveGameSettings* saveSettings = GetMutableDefault<UALSSaveGameSettings>();
	return saveSettings->GetDefaultSaveName();
}

/*
// class UALSSaveGame* UALSLoadAndSaveSubsystem::GetCurrentSaveGame() const
// {
//     return currentSavegame;
// }
*/

void UALSLoadAndSaveSubsystem::FinishSaveWork(const bool bSuccess)
{

	const UALSSaveGameSettings* saveSettings = GetMutableDefault<UALSSaveGameSettings>();
	if (bSuccess && bSaveScreen) {
		UALSFunctionLibrary::TrySaveScreenshot(currentSaveSlot, saveSettings->GetDefaultScreenshotWidth(), saveSettings->GetDefaultScreenshotHeight());
	}
	onSaveFinishedInternal.ExecuteIfBound(bSuccess);
	systemState = ELoadingState::EIdle;
}

void UALSLoadAndSaveSubsystem::FinishLoadWork(const bool bSuccess)
{
	OnLoadFinished.Broadcast(bSuccess);
	onLoadedCallbackInternal.ExecuteIfBound(bSuccess);

	systemState = ELoadingState::EIdle;
	StartPlaytimeTracking();
}

void UALSLoadAndSaveSubsystem::HandleLoadingFinished(UWorld* world)
{
	if (systemState == ELoadingState::ELoading) {
		AsyncLoadSaveGame(currentSaveSlot);
	}
}

void UALSLoadAndSaveSubsystem::HandleLoadCompleted(const FString& SaveSlot, const int32 UserIndex, USaveGame* LoadedSaveData)
{
	if (!LoadedSaveData) {
		onLoadedCallbackInternal.ExecuteIfBound(false);
		systemState = ELoadingState::EIdle;
		return;
	}
	currentSaveSlot = SaveSlot;
	currentSavegame = Cast<UALSSaveGame>(LoadedSaveData);
	bIsNewGame = false;
	if (!currentSavegame) {
		onLoadedCallbackInternal.ExecuteIfBound(false);
		systemState = ELoadingState::EIdle;
		SetLoadType(ELoadType::EDontReload);
		return;
	}
	(new FAsyncTask<FLoadWorldTask>(currentSaveSlot, GetWorld(), UGameplayStatics::GetCurrentLevelName(GetWorld()), bReloadPlayer))->StartBackgroundTask();
}

void UALSLoadAndSaveSubsystem::AsyncLoadSaveGame(const FString& savegameName)
{
	FAsyncLoadGameFromSlotDelegate LoadedDelegate;
	LoadedDelegate.BindUObject(this, &UALSLoadAndSaveSubsystem::HandleLoadCompleted);

	UGameplayStatics::AsyncLoadGameFromSlot(savegameName, 0, LoadedDelegate);
}

void UALSLoadAndSaveSubsystem::SerializeObject(UObject* objectToSerialize, FALSObjectData& outData)
{
	FALSObjectData Record = { objectToSerialize };

	FMemoryWriter MemoryWriter(Record.Data, true);
	FALSSaveGameArchive Archive(MemoryWriter, false);
	objectToSerialize->Serialize(Archive);
	outData = Record;
}

void UALSLoadAndSaveSubsystem::DeserializeObject(UObject* settingsObject, const FALSObjectData& objectData)
{
	FMemoryReader MemoryReader(objectData.Data, true);
	FALSSaveGameArchive Archive(MemoryReader, false);
	settingsObject->Serialize(Archive);
}

UALSSaveGame* UALSLoadAndSaveSubsystem::LoadOrCreateSaveGame(const FString& slotName)
{
	const UALSSaveGameSettings* saveSettings = GetMutableDefault<UALSSaveGameSettings>();

	if (slotName == currentSaveSlot && currentSavegame) {
		return currentSavegame;
	}
	UALSSaveGame* saveGame = Cast<UALSSaveGame>(UGameplayStatics::LoadGameFromSlot(slotName, 0));
	if (saveGame) {
		return saveGame;
	}

	return Cast<UALSSaveGame>(UGameplayStatics::CreateSaveGameObject(saveSettings->GetSaveGameClass()));
}

UALSSaveInfo* UALSLoadAndSaveSubsystem::LoadOrCreateSaveInfo()
{
	const UALSSaveGameSettings* saveSettings = GetMutableDefault<UALSSaveGameSettings>();
	UALSSaveInfo* saveMetadata = Cast<UALSSaveInfo>(UGameplayStatics::LoadGameFromSlot(saveSettings->GetSaveMetadataName(), 0));
	if (saveMetadata) {
		return saveMetadata;
	}

	return Cast<UALSSaveInfo>(UGameplayStatics::CreateSaveGameObject(UALSSaveInfo::StaticClass()));
}
