#include "MelodiaSaveGameSubsystem.h"

#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "Kismet/GameplayStatics.h"
#include "GameFramework/Pawn.h"
#include "MelodiaBattleSession.h"
#include "MelodiaEntitlementSubsystem.h"
#include "MelodiaOpeningFlowSubsystem.h"
#include "MelodiaPartySubsystem.h"
#include "MelodiaProgressionComponent.h"
#include "MelodiaRoguelikeRunSubsystem.h"
#include "MelodiaQuestManagerBase.h"
#include "MelodiaSaveGame.h"
#include "MelodiaTokenWalletSubsystem.h"

UMelodiaSaveGameSubsystem* UMelodiaSaveGameSubsystem::Get(const UObject* WorldContextObject)
{
	const UWorld* World = WorldContextObject ? WorldContextObject->GetWorld() : nullptr;
	return World && World->GetGameInstance()
		? World->GetGameInstance()->GetSubsystem<UMelodiaSaveGameSubsystem>()
		: nullptr;
}

void UMelodiaSaveGameSubsystem::SaveGame()
{
	SaveToSlot(0);
}

void UMelodiaSaveGameSubsystem::LoadGame()
{
	LoadFromSlot(0);
}

bool UMelodiaSaveGameSubsystem::HasSaveGame() const
{
	return HasSaveInSlot(0);
}

void UMelodiaSaveGameSubsystem::SaveToSlot(const int32 SlotIndex)
{
	UMelodiaSaveGame* Save = Cast<UMelodiaSaveGame>(UGameplayStatics::CreateSaveGameObject(UMelodiaSaveGame::StaticClass()));
	if (!Save)
	{
		OnSaveCompleted.Broadcast(false);
		return;
	}

	if (const UMelodiaOpeningFlowSubsystem* Flow = UMelodiaOpeningFlowSubsystem::Get(this))
	{
		Save->OpeningPhase = Flow->Phase;
		Save->bHeartMelodyTokenGranted = Flow->bHeartMelodyTokenGranted;
	}

	if (const UMelodiaBattleSession* Battle = UMelodiaBattleSession::Get(this))
	{
		Save->PersistentPartyHP = Battle->PersistentPartyHP;
		Save->PersistentPartyMaxHP = Battle->PersistentPartyMaxHP;
		Save->PersistentSkillPoints = Battle->PersistentSkillPoints;
		Save->PersistentSkillPointMax = Battle->PersistentSkillPointMax;
		Save->PersistentUltimateGauge = Battle->PersistentUltimateGauge;
		Save->PersistentEquippedKeyElement = Battle->PersistentEquippedKeyElement;
		Save->bPersistentHarmonicKeyEquipped = Battle->bPersistentHarmonicKeyEquipped;
	}

	if (const UMelodiaPartySubsystem* Party = UMelodiaPartySubsystem::Get(this))
	{
		Save->ActivePartyIndex = Party->ActiveIndex;
		if (const APawn* Active = Party->GetActivePawn())
		{
			Save->PartyPawnTransforms.Add(Party->ActiveIndex, Active->GetActorTransform());
		}
	}
	if (const UWorld* World = GetWorld())
	{
		Save->CurrentMapName = FName(*UGameplayStatics::GetCurrentLevelName(World));
	}

	// Persist monetization / durable-progression state (additive fields, safe for v1 saves)
	if (UMelodiaRoguelikeRunSubsystem* Run = UMelodiaRoguelikeRunSubsystem::Get(this))
	{
		Save->HeartMelodyTokens = Run->HeartMelodyTokens;
		Save->SwirlMelodyTokens = Run->SwirlMelodyTokens;
	}
	// Melody Token wallet joins the canonical save transaction. Without this the wallet would
	// live only in memory and every "survives a restart" test would fail on the restart, not
	// on the arithmetic.
	if (const UMelodiaTokenWalletSubsystem* Wallet = UMelodiaTokenWalletSubsystem::Get(this))
	{
		Wallet->CaptureToSave(Save);
	}
	if (UMelodiaEntitlementSubsystem* Entitlements = UMelodiaEntitlementSubsystem::Get(this))
	{
		Save->OwnedContentPacks = Entitlements->QueryEntitlements();
	}
	if (UMelodiaBattleSession* Battle = UMelodiaBattleSession::Get(this))
	{
		if (const AActor* Controller = Battle->GetBattleController())
		{
			if (const UMelodiaProgressionComponent* Progression = Controller->FindComponentByClass<UMelodiaProgressionComponent>())
			{
				Save->Currency = Progression->Currency;
			}
		}
	}

	if (const UWorld* World = GetWorld())
	{
		if (AMelodiaQuestManagerBase* QuestManager = AMelodiaQuestManagerBase::Get(World))
		{
			Save->SavedCompletedQuestIds = QuestManager->GetCompletedQuestIds();
			for (const FMelodiaQuestDef& Quest : QuestManager->GetActiveQuests())
			{
				Save->SavedActiveQuests.Add(Quest);
			}
		}
	}

	Save->MotionTier = CurrentMotionTier;

	Save->SaveSlotName = SlotNameForIndex(SlotIndex);
	Save->UserIndex = UserIndex();
	Save->SavedAtUtc = FDateTime::UtcNow();

	FAsyncSaveGameToSlotDelegate SavedDelegate;
	SavedDelegate.BindUObject(this, &UMelodiaSaveGameSubsystem::HandleAsyncSaveComplete);
	UGameplayStatics::AsyncSaveGameToSlot(Save, SlotNameForIndex(SlotIndex), UserIndex(), SavedDelegate);
}

void UMelodiaSaveGameSubsystem::LoadFromSlot(const int32 SlotIndex)
{
	FAsyncLoadGameFromSlotDelegate LoadedDelegate;
	LoadedDelegate.BindUObject(this, &UMelodiaSaveGameSubsystem::HandleAsyncLoadComplete);
	UGameplayStatics::AsyncLoadGameFromSlot(SlotNameForIndex(SlotIndex), UserIndex(), LoadedDelegate);
}

bool UMelodiaSaveGameSubsystem::HasSaveInSlot(const int32 SlotIndex) const
{
	return UGameplayStatics::DoesSaveGameExist(SlotNameForIndex(SlotIndex), UserIndex());
}

bool UMelodiaSaveGameSubsystem::DeleteSlot(const int32 SlotIndex)
{
	if (!UGameplayStatics::DoesSaveGameExist(SlotNameForIndex(SlotIndex), UserIndex()))
	{
		return false;
	}
	return UGameplayStatics::DeleteGameInSlot(SlotNameForIndex(SlotIndex), UserIndex());
}

FMelodiaSaveSlotSummary UMelodiaSaveGameSubsystem::GetSaveSlotSummary(const int32 SlotIndex) const
{
	FMelodiaSaveSlotSummary Summary;
	Summary.SlotIndex = SlotIndex;

	if (!UGameplayStatics::DoesSaveGameExist(SlotNameForIndex(SlotIndex), UserIndex()))
	{
		return Summary;
	}

	// No lighter header exists for arbitrary USaveGame objects, so read the slot
	// synchronously and copy out only the headline fields the UI needs.
	const UMelodiaSaveGame* Save = Cast<UMelodiaSaveGame>(UGameplayStatics::LoadGameFromSlot(SlotNameForIndex(SlotIndex), UserIndex()));
	if (!Save)
	{
		return Summary;
	}

	Summary.bOccupied = true;
	Summary.CurrentMapName = Save->CurrentMapName.ToString();
	Summary.ActivePartyIndex = Save->ActivePartyIndex;
	Summary.OpeningPhase = Save->OpeningPhase;
	Summary.Timestamp = Save->SavedAtUtc;
	return Summary;
}

TArray<FMelodiaSaveSlotSummary> UMelodiaSaveGameSubsystem::GetAllSaveSlotSummaries() const
{
	TArray<FMelodiaSaveSlotSummary> Summaries;
	Summaries.Reserve(NumSaveSlots);
	for (int32 SlotIndex = 0; SlotIndex < NumSaveSlots; ++SlotIndex)
	{
		Summaries.Add(GetSaveSlotSummary(SlotIndex));
	}
	return Summaries;
}

void UMelodiaSaveGameSubsystem::HandleAsyncSaveComplete(const FString& InSlotName, const int32 InUserIndex, const bool bSuccess)
{
	UE_LOG(LogTemp, Log, TEXT("Melodia: save to slot '%s' (user %d) %s."), *InSlotName, InUserIndex, bSuccess ? TEXT("succeeded") : TEXT("FAILED"));
	OnSaveCompleted.Broadcast(bSuccess);
}

void UMelodiaSaveGameSubsystem::HandleAsyncLoadComplete(const FString& InSlotName, const int32 InUserIndex, USaveGame* LoadedSave)
{
	const UMelodiaSaveGame* Save = Cast<UMelodiaSaveGame>(LoadedSave);
	if (!Save)
	{
		UE_LOG(LogTemp, Warning, TEXT("Melodia: load from slot '%s' (user %d) failed or found no save."), *InSlotName, InUserIndex);
		OnLoadCompleted.Broadcast(false);
		return;
	}

	CurrentMotionTier = Save->MotionTier;

	if (UMelodiaOpeningFlowSubsystem* Flow = UMelodiaOpeningFlowSubsystem::Get(this))
	{
		Flow->RestoreFromSave(Save->OpeningPhase, Save->bHeartMelodyTokenGranted);
	}

	if (const UWorld* World = GetWorld())
	{
		if (AMelodiaQuestManagerBase* QuestManager = AMelodiaQuestManagerBase::Get(World))
		{
			QuestManager->RestoreQuestState(Save->SavedActiveQuests, Save->SavedCompletedQuestIds);
		}
	}

	if (UMelodiaBattleSession* Battle = UMelodiaBattleSession::Get(this))
	{
		Battle->RestorePersistentPartyState(
			Save->PersistentPartyHP,
			Save->PersistentPartyMaxHP,
			Save->PersistentSkillPoints,
			Save->PersistentSkillPointMax,
			Save->PersistentUltimateGauge,
			Save->PersistentEquippedKeyElement,
			Save->bPersistentHarmonicKeyEquipped);

		if (AActor* Controller = Battle->GetBattleController())
		{
			if (UMelodiaProgressionComponent* Progression = Controller->FindComponentByClass<UMelodiaProgressionComponent>())
			{
				Progression->RestoreCurrency(Save->Currency);
			}
		}
	}

	if (UMelodiaRoguelikeRunSubsystem* Run = UMelodiaRoguelikeRunSubsystem::Get(this))
	{
		Run->RestoreDurableTokens(Save->HeartMelodyTokens, Save->SwirlMelodyTokens);
	}

	// Restored AFTER the roguelike run subsystem so the legacy-token migration reads values
	// that are already settled for this load.
	if (UMelodiaTokenWalletSubsystem* Wallet = UMelodiaTokenWalletSubsystem::Get(this))
	{
		Wallet->RestoreFromSave(Save);
	}

	if (UMelodiaEntitlementSubsystem* Entitlements = UMelodiaEntitlementSubsystem::Get(this))
	{
		Entitlements->RestoreFromSave(Save->OwnedContentPacks);
	}

	// Explore party restore: only when we're already on the saved map — cross-map
	// travel stays the caller's decision (load-from-menu flows OpenLevel first).
	if (UWorld* World = GetWorld())
	{
		const FName CurrentMap = FName(*UGameplayStatics::GetCurrentLevelName(World));
		if (Save->CurrentMapName.IsNone() || CurrentMap == Save->CurrentMapName)
		{
			if (UMelodiaPartySubsystem* Party = UMelodiaPartySubsystem::Get(this))
			{
				if (APlayerController* PC = UGameplayStatics::GetPlayerController(World, 0))
				{
					Party->SetActiveIndex(Save->ActivePartyIndex, PC);
				}
				if (APawn* Active = Party->GetActivePawn())
				{
					if (const FTransform* Where = Save->PartyPawnTransforms.Find(Save->ActivePartyIndex))
					{
						Active->SetActorTransform(*Where, false, nullptr, ETeleportType::TeleportPhysics);
					}
				}
			}
		}
		else
		{
			UE_LOG(LogTemp, Log, TEXT("Melodia: save was taken on map '%s' (currently '%s') - transform restore skipped."),
				*Save->CurrentMapName.ToString(), *CurrentMap.ToString());
		}
	}

	UE_LOG(LogTemp, Log, TEXT("Melodia: load from slot '%s' (user %d) succeeded."), *InSlotName, InUserIndex);
	OnLoadCompleted.Broadcast(true);
}
