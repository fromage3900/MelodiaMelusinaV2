#include "MelodiaRoguelikePersistence.h"

#include "Kismet/GameplayStatics.h"
#include "MelodiaBattleSession.h"
#include "MelodiaEntitlementSubsystem.h"
#include "MelodiaRoguelikeRunSubsystem.h"

void UMelodiaRoguelikePersistenceSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);
	CachedProfile = Cast<UMelodiaRoguelikeProfileSaveGame>(
		UGameplayStatics::CreateSaveGameObject(UMelodiaRoguelikeProfileSaveGame::StaticClass()));
	CachedHistory = Cast<UMelodiaRoguelikeRunHistorySaveGame>(
		UGameplayStatics::CreateSaveGameObject(UMelodiaRoguelikeRunHistorySaveGame::StaticClass()));
}

UMelodiaRoguelikePersistenceSubsystem* UMelodiaRoguelikePersistenceSubsystem::Get(const UObject* WorldContextObject)
{
	const UWorld* World = WorldContextObject ? WorldContextObject->GetWorld() : nullptr;
	return World && World->GetGameInstance()
		? World->GetGameInstance()->GetSubsystem<UMelodiaRoguelikePersistenceSubsystem>()
		: nullptr;
}

void UMelodiaRoguelikePersistenceSubsystem::SaveProfile()
{
	if (!CachedProfile) return;
	CachedProfile->SavedAtUtc = FDateTime::UtcNow();
	if (const UMelodiaRoguelikeRunSubsystem* Run = GetGameInstance()->GetSubsystem<UMelodiaRoguelikeRunSubsystem>())
	{
		CachedProfile->CompanionBond = Run->CompanionBond;
	}
	if (const UMelodiaEntitlementSubsystem* Entitlements = GetGameInstance()->GetSubsystem<UMelodiaEntitlementSubsystem>())
	{
		CachedProfile->EntitlementCache = Entitlements->QueryEntitlements();
	}
	UGameplayStatics::AsyncSaveGameToSlot(CachedProfile, ProfileSlot(), 0,
		FAsyncSaveGameToSlotDelegate::CreateUObject(this, &ThisClass::HandleSaveComplete));
}

void UMelodiaRoguelikePersistenceSubsystem::LoadProfile()
{
	UGameplayStatics::AsyncLoadGameFromSlot(ProfileSlot(), 0,
		FAsyncLoadGameFromSlotDelegate::CreateUObject(this, &ThisClass::HandleProfileLoaded));
}

void UMelodiaRoguelikePersistenceSubsystem::SaveRunCheckpoint()
{
	UMelodiaRoguelikeRunSubsystem* Run = GetGameInstance()->GetSubsystem<UMelodiaRoguelikeRunSubsystem>();
	UMelodiaBattleSession* Battle = GetGameInstance()->GetSubsystem<UMelodiaBattleSession>();
	if (!Run || !Battle)
	{
		OnOperationCompleted.Broadcast(TEXT("SaveRunCheckpoint"), false);
		return;
	}
	UMelodiaRoguelikeRunCheckpointSaveGame* Save = Cast<UMelodiaRoguelikeRunCheckpointSaveGame>(
		UGameplayStatics::CreateSaveGameObject(UMelodiaRoguelikeRunCheckpointSaveGame::StaticClass()));
	Save->Snapshot = Run->ExportSnapshot();
	Save->PartyHP = Battle->PersistentPartyHP;
	Save->PartyMaxHP = Battle->PersistentPartyMaxHP;
	Save->SkillPoints = Battle->PersistentSkillPoints;
	Save->SkillPointMax = Battle->PersistentSkillPointMax;
	Save->UltimateGauge = Battle->PersistentUltimateGauge;
	Save->KeyElement = Battle->PersistentEquippedKeyElement;
	Save->bHarmonicKeyEquipped = Battle->bPersistentHarmonicKeyEquipped;
	Save->SavedAtUtc = FDateTime::UtcNow();
	UGameplayStatics::AsyncSaveGameToSlot(Save, CheckpointSlot(), 0,
		FAsyncSaveGameToSlotDelegate::CreateUObject(this, &ThisClass::HandleSaveComplete));
}

void UMelodiaRoguelikePersistenceSubsystem::LoadRunCheckpoint()
{
	UGameplayStatics::AsyncLoadGameFromSlot(CheckpointSlot(), 0,
		FAsyncLoadGameFromSlotDelegate::CreateUObject(this, &ThisClass::HandleCheckpointLoaded));
}

bool UMelodiaRoguelikePersistenceSubsystem::ClearRunCheckpoint()
{
	return !HasRunCheckpoint() || UGameplayStatics::DeleteGameInSlot(CheckpointSlot(), 0);
}

void UMelodiaRoguelikePersistenceSubsystem::SaveRunHistory()
{
	if (!CachedHistory) return;
	UGameplayStatics::AsyncSaveGameToSlot(CachedHistory, HistorySlot(), 0,
		FAsyncSaveGameToSlotDelegate::CreateUObject(this, &ThisClass::HandleSaveComplete));
}

void UMelodiaRoguelikePersistenceSubsystem::LoadRunHistory()
{
	UGameplayStatics::AsyncLoadGameFromSlot(HistorySlot(), 0,
		FAsyncLoadGameFromSlotDelegate::CreateUObject(this, &ThisClass::HandleHistoryLoaded));
}

void UMelodiaRoguelikePersistenceSubsystem::AppendRunHistory(const FMelodiaRunHistoryEntry& Entry)
{
	if (!CachedHistory)
	{
		CachedHistory = Cast<UMelodiaRoguelikeRunHistorySaveGame>(
			UGameplayStatics::CreateSaveGameObject(UMelodiaRoguelikeRunHistorySaveGame::StaticClass()));
	}
	FMelodiaRunHistoryEntry Stored = Entry;
	Stored.FinishedAtUtc = Stored.FinishedAtUtc == FDateTime() ? FDateTime::UtcNow() : Stored.FinishedAtUtc;
	CachedHistory->Entries.Add(Stored);
	SaveRunHistory();
}

bool UMelodiaRoguelikePersistenceSubsystem::HasRunCheckpoint() const
{
	return UGameplayStatics::DoesSaveGameExist(CheckpointSlot(), 0);
}

void UMelodiaRoguelikePersistenceSubsystem::HandleSaveComplete(
	const FString& SlotName, const int32 UserIndex, const bool bSuccess)
{
	FName Operation = TEXT("SaveUnknown");
	if (SlotName == ProfileSlot()) Operation = TEXT("SaveProfile");
	else if (SlotName == CheckpointSlot()) Operation = TEXT("SaveRunCheckpoint");
	else if (SlotName == HistorySlot()) Operation = TEXT("SaveRunHistory");
	OnOperationCompleted.Broadcast(Operation, bSuccess);
}

void UMelodiaRoguelikePersistenceSubsystem::HandleProfileLoaded(
	const FString& SlotName, const int32 UserIndex, USaveGame* Loaded)
{
	UMelodiaRoguelikeProfileSaveGame* Profile = Cast<UMelodiaRoguelikeProfileSaveGame>(Loaded);
	const bool bValid = Profile && Profile->SchemaVersion == 1;
	if (bValid)
	{
		CachedProfile = Profile;
		if (UMelodiaRoguelikeRunSubsystem* Run = GetGameInstance()->GetSubsystem<UMelodiaRoguelikeRunSubsystem>())
		{
			Run->SetCompanionState(Run->bCompanionPresent, Run->bResonanceAvailable,
				Run->bCompanionPlayable, Profile->CompanionBond);
		}
	}
	OnOperationCompleted.Broadcast(TEXT("LoadProfile"), bValid);
}

void UMelodiaRoguelikePersistenceSubsystem::HandleCheckpointLoaded(
	const FString& SlotName, const int32 UserIndex, USaveGame* Loaded)
{
	UMelodiaRoguelikeRunCheckpointSaveGame* Save = Cast<UMelodiaRoguelikeRunCheckpointSaveGame>(Loaded);
	UMelodiaRoguelikeRunSubsystem* Run = GetGameInstance()->GetSubsystem<UMelodiaRoguelikeRunSubsystem>();
	UMelodiaBattleSession* Battle = GetGameInstance()->GetSubsystem<UMelodiaBattleSession>();
	const bool bValid = Save && Save->SchemaVersion == 1 && Run && Battle && Run->ImportSnapshot(Save->Snapshot);
	if (bValid)
	{
		Battle->RestorePersistentPartyState(Save->PartyHP, Save->PartyMaxHP,
			Save->SkillPoints, Save->SkillPointMax, Save->UltimateGauge,
			Save->KeyElement, Save->bHarmonicKeyEquipped);
	}
	OnOperationCompleted.Broadcast(TEXT("LoadRunCheckpoint"), bValid);
}

void UMelodiaRoguelikePersistenceSubsystem::HandleHistoryLoaded(
	const FString& SlotName, const int32 UserIndex, USaveGame* Loaded)
{
	UMelodiaRoguelikeRunHistorySaveGame* History = Cast<UMelodiaRoguelikeRunHistorySaveGame>(Loaded);
	const bool bValid = History && History->SchemaVersion == 1;
	if (bValid) CachedHistory = History;
	OnOperationCompleted.Broadcast(TEXT("LoadRunHistory"), bValid);
}
