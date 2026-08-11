#include "MelodiaSaveSlotLibrary.h"

#include "Kismet/GameplayStatics.h"
#include "Engine/GameInstance.h"
#include "GameFramework/SaveGame.h"
#include "MelodiaInputContextSubsystem.h"
#include "MelodiaNarrativeSubsystem.h"
#include "MelodiaSaveRecoverySubsystem.h"
#include "MelodiaTravelSubsystem.h"
#include "UObject/UnrealType.h"

namespace
{
	UMelodiaNarrativeSubsystem* GetNarrative(const UObject* WorldContextObject)
	{
		return UMelodiaNarrativeSubsystem::GetMelodiaNarrativeSubsystem(WorldContextObject);
	}

	UMelodiaSaveRecoverySubsystem* GetRecovery(const UObject* WorldContextObject)
	{
		return UMelodiaSaveRecoverySubsystem::Get(WorldContextObject);
	}

	/** Validate without calling RestoreNarrativeRecord, which may reset state on an incompatible version. */
	bool HasLoadableNarrativeRecord(const UObject* JRPGSaveObject)
	{
		if (!IsValid(JRPGSaveObject))
		{
			return false;
		}

		const FStructProperty* RecordProperty = FindFProperty<FStructProperty>(JRPGSaveObject->GetClass(), TEXT("melodiaNarrativeRecord"));
		if (!RecordProperty || RecordProperty->Struct != FMelodiaNarrativeRecord::StaticStruct())
		{
			return false;
		}

		const FMelodiaNarrativeRecord* Source = RecordProperty->ContainerPtrToValuePtr<FMelodiaNarrativeRecord>(JRPGSaveObject);
		if (!Source)
		{
			return false;
		}

		FMelodiaNarrativeRecord Candidate = *Source;
		return UMelodiaNarrativeSubsystem::MigrateRecord(Candidate);
	}

	void EndSaveBoundary(UMelodiaSaveRecoverySubsystem* Recovery, const FString& SlotName)
	{
		if (Recovery)
		{
			Recovery->EndSaveBoundary(SlotName);
		}
	}

	void EndLoadBoundary(UMelodiaSaveRecoverySubsystem* Recovery, const FString& SlotName)
	{
		if (Recovery)
		{
			Recovery->EndLoadBoundary(SlotName);
		}
	}
}

bool UMelodiaSaveSlotLibrary::HasCanonicalJRPGSlot(const UObject* WorldContextObject, const FString& SlotName, const int32 UserIndex)
{
	return !SlotName.IsEmpty() && UGameplayStatics::DoesSaveGameExist(SlotName, UserIndex);
}

bool UMelodiaSaveSlotLibrary::LoadCanonicalJRPGSlot(const UObject* WorldContextObject, const FString& SlotName, const int32 UserIndex)
{
	// Legacy bool surface: true exactly when the narrative record was restored.
	return LoadCanonicalJRPGSlotDetailed(WorldContextObject, SlotName, UserIndex) == EMelodiaLoadSlotResult::LoadedNarrativeRestored;
}

EMelodiaLoadSlotResult UMelodiaSaveSlotLibrary::LoadCanonicalJRPGSlotDetailed(const UObject* WorldContextObject, const FString& SlotName, const int32 UserIndex)
{
	if (!HasCanonicalJRPGSlot(WorldContextObject, SlotName, UserIndex))
	{
		return EMelodiaLoadSlotResult::Missing;
	}

	UMelodiaSaveRecoverySubsystem* Recovery = GetRecovery(WorldContextObject);
	if (Recovery)
	{
		Recovery->BeginLoadBoundary(SlotName);
	}

	UGameInstance* GameInstance = UGameplayStatics::GetGameInstance(WorldContextObject);
	USaveGame* LoadedSave = UGameplayStatics::LoadGameFromSlot(SlotName, UserIndex);
	if (!GameInstance || !LoadedSave)
	{
		EndLoadBoundary(Recovery, SlotName);
		return EMelodiaLoadSlotResult::Refused;
	}

	UMelodiaNarrativeSubsystem* Narrative = GetNarrative(WorldContextObject);
	if (!Narrative || !HasLoadableNarrativeRecord(LoadedSave))
	{
		UE_LOG(LogTemp, Warning,
			TEXT("MELODIA_LOAD refused canonical slot '%s': no compatible narrative record was available."),
			*SlotName);
		EndLoadBoundary(Recovery, SlotName);
		return EMelodiaLoadSlotResult::Refused;
	}

	// Preserve the selected slot for subsequent stock saves. This is the
	// existing BP_JRPGGameInstance variable, not a second persistence owner.
	if (FStrProperty* SlotNameProperty = FindFProperty<FStrProperty>(GameInstance->GetClass(), TEXT("slotName")))
	{
		SlotNameProperty->SetPropertyValue_InContainer(GameInstance, SlotName);
	}
	if (FObjectPropertyBase* SaveProperty = FindFProperty<FObjectPropertyBase>(GameInstance->GetClass(), TEXT("jRPGSaveGame")))
	{
		SaveProperty->SetObjectPropertyValue_InContainer(GameInstance, LoadedSave);
	}

	// The first canonical save is created before the opening map has been
	// recorded. The stock LoadThisGame event opens currentMap, so do not feed it
	// NAME_None; return that valid initial slot to the authored opening route.
	FName SavedMap = NAME_None;
	if (const FNameProperty* CurrentMapProperty = FindFProperty<FNameProperty>(LoadedSave->GetClass(), TEXT("currentMap")))
	{
		SavedMap = CurrentMapProperty->GetPropertyValue_InContainer(LoadedSave);
	}
	if (SavedMap.IsNone())
	{
		// There is no stock load event for a fresh slot, so restore the canonical
		// narrative record before taking the authored opening route.
		if (!Narrative->RestoreNarrativeRecordFromSave(LoadedSave))
		{
			UE_LOG(LogTemp, Warning, TEXT("MELODIA_LOAD refused canonical slot '%s': narrative restore failed."), *SlotName);
			EndLoadBoundary(Recovery, SlotName);
			return EMelodiaLoadSlotResult::Refused;
		}

		// Route through the single travel authority (Decision 023) so this path gets
		// allowlist validation, spawn placement and the input-context clear on arrival.
		//
		// CORRECTION 2026-07-31: an earlier version of this comment claimed this was
		// "the last direct OpenLevel call left in the project". That was wrong — it was
		// the last one in the BS_GodFile *game module*. MelodiaCore still has seven
		// (OrreryMainMenuGameMode x5, MelodiaSirMelodiousIntroActor, MelodiaOpeningPortal).
		// Those cannot call this subsystem as-is: UMelodiaTravelSubsystem lives in the
		// game module and MelodiaCore is a plugin, so reaching it would invert the
		// dependency. See _TASK_QUEUE.md "Travel authority cannot reach MelodiaCore".
		static const FName OpeningRoute(TEXT("/Game/Melodia/Levels/Opening/L_MelusinaMorning"));
		UE_LOG(LogTemp, Log, TEXT("Melodia canonical load: slot '%s' has no saved map; travelling to the authored first route."), *SlotName);

		EndLoadBoundary(Recovery, SlotName);
		if (UMelodiaTravelSubsystem* Travel = UMelodiaTravelSubsystem::Get(WorldContextObject))
		{
			if (Travel->TravelTo(OpeningRoute, NAME_None))
			{
				return EMelodiaLoadSlotResult::LoadedNarrativeRestored;
			}

			// Refused means the ID is not in DA_MelodiaIntegrationConfig->TravelLevelIds.
			// Fall through rather than stranding the player on a dead slot, but say
			// loudly what to fix -- a silent fallback here is how this became a bypass
			// in the first place.
			UE_LOG(LogTemp, Warning,
				TEXT("MELODIA_TRAVEL refused '%s' from the canonical-load fallback. Add it to "
					 "DA_MelodiaIntegrationConfig -> Travel Level Ids. Using a direct OpenLevel for now, "
					 "which skips spawn placement and the input-context clear."),
				*OpeningRoute.ToString());
		}
		else
		{
			UE_LOG(LogTemp, Warning,
				TEXT("MELODIA_TRAVEL unavailable from the canonical-load fallback (no travel subsystem); using a direct OpenLevel."));
		}

		UGameplayStatics::OpenLevel(WorldContextObject, OpeningRoute);
		return EMelodiaLoadSlotResult::LoadedNarrativeRestored;
	}

	UFunction* LoadThisGame = GameInstance->FindFunction(TEXT("LoadThisGame"));
	if (!LoadThisGame)
	{
		EndLoadBoundary(Recovery, SlotName);
		return EMelodiaLoadSlotResult::Refused;
	}

	FObjectPropertyBase* SaveParameter = nullptr;
	for (TFieldIterator<FProperty> It(LoadThisGame); It; ++It)
	{
		if (It->HasAnyPropertyFlags(CPF_Parm) && It->GetFName() == TEXT("jRPGSaveGame"))
		{
			SaveParameter = CastField<FObjectPropertyBase>(*It);
			break;
		}
	}
	if (!SaveParameter)
	{
		EndLoadBoundary(Recovery, SlotName);
		return EMelodiaLoadSlotResult::Refused;
	}

	uint8* Parameters = static_cast<uint8*>(FMemory_Alloca(LoadThisGame->ParmsSize));
	FMemory::Memzero(Parameters, LoadThisGame->ParmsSize);
	SaveParameter->SetObjectPropertyValue_InContainer(Parameters, LoadedSave);
	GameInstance->ProcessEvent(LoadThisGame, Parameters);

	// This call is deliberately after the stock GameInstance event. It closes the
	// native save boundary without replacing stock map, party, reward, or battle
	// restoration. If the authored event already restores the record, this is an
	// idempotent state restore; the exact Blueprint node order remains a runtime
	// verification item rather than an assumption here.
	const bool bNarrativeRestored = Narrative->RestoreNarrativeRecordFromSave(LoadedSave);
	EndLoadBoundary(Recovery, SlotName);
	return bNarrativeRestored ? EMelodiaLoadSlotResult::LoadedNarrativeRestored : EMelodiaLoadSlotResult::LoadedNarrativeDegraded;
}

bool UMelodiaSaveSlotLibrary::CreateCanonicalJRPGSlot(const UObject* WorldContextObject, const FString& SlotName, const int32 UserIndex)
{
	if (SlotName.IsEmpty())
	{
		return false;
	}

	// _VERTICAL_SLICE_SCOPE.md requires manual saving be unavailable during an active
	// narrative battle. Enforced here rather than left to each caller: a mid-battle
	// save cannot represent turn state, and a rule that lives only in a document gets
	// missed. The input authority owns the answer; this just honours it.
	if (const UMelodiaInputContextSubsystem* Input = UMelodiaInputContextSubsystem::Get(WorldContextObject))
	{
		if (!Input->IsSavingAllowed())
		{
			UE_LOG(LogTemp, Warning,
				TEXT("MELODIA_SAVE refused: saving not permitted in context %s (slot=%s)"),
				*UEnum::GetValueAsString(Input->GetActiveContext()), *SlotName);
			return false;
		}
	}

	UGameInstance* GameInstance = UGameplayStatics::GetGameInstance(WorldContextObject);
	UMelodiaNarrativeSubsystem* Narrative = GetNarrative(WorldContextObject);
	UClass* SaveGameClass = LoadClass<USaveGame>(nullptr, TEXT("/Game/TurnBasedJRPGTemplate/Blueprints/Controllers/BP_JRPGSaveGame.BP_JRPGSaveGame_C"));
	if (!GameInstance || !Narrative || !SaveGameClass)
	{
		return false;
	}

	UMelodiaSaveRecoverySubsystem* Recovery = GetRecovery(WorldContextObject);
	if (Recovery)
	{
		Recovery->BeginSaveBoundary(SlotName);
	}

	// This is the native New Game creation path. Reset only the Melodia narrative
	// subsystem, then copy that canonical record into the stock save object before
	// the stock serializer writes it. No combat or reward state is touched here.
	Narrative->ResetNarrativeRecord();
	USaveGame* NewSave = UGameplayStatics::CreateSaveGameObject(SaveGameClass);
	if (!NewSave || !Narrative->SyncNarrativeRecordToSave(NewSave))
	{
		UE_LOG(LogTemp, Warning, TEXT("MELODIA_SAVE refused canonical slot '%s': narrative sync failed."), *SlotName);
		EndSaveBoundary(Recovery, SlotName);
		return false;
	}

	const bool bSaved = UGameplayStatics::SaveGameToSlot(NewSave, SlotName, UserIndex);
	EndSaveBoundary(Recovery, SlotName);
	if (!bSaved)
	{
		return false;
	}

	if (FStrProperty* SlotNameProperty = FindFProperty<FStrProperty>(GameInstance->GetClass(), TEXT("slotName")))
	{
		SlotNameProperty->SetPropertyValue_InContainer(GameInstance, SlotName);
	}
	if (FObjectPropertyBase* SaveProperty = FindFProperty<FObjectPropertyBase>(GameInstance->GetClass(), TEXT("jRPGSaveGame")))
	{
		SaveProperty->SetObjectPropertyValue_InContainer(GameInstance, NewSave);
	}

	return true;
}
