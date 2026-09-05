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

	/**
	 * Validate invariants that belong to the canonical record itself before the
	 * stock JRPG load event is allowed to mutate runtime state.
	 *
	 * Keep this deliberately module-neutral: catalog existence, authored meshes
	 * and cosmetic-to-slot semantics belong to MelodiaWardrobe and must not be
	 * pulled into BS_GodFile through a reverse dependency. The persistence layer
	 * can still prove the intrinsic invariant that an equipped persistent ID is
	 * non-empty and is part of the same record's owned set.
	 */
	bool ValidateIntrinsicNarrativeRecord(const FMelodiaNarrativeRecord& Candidate, FString& OutReason)
	{
		for (const TPair<EMelodiaWardrobeSlot, FName>& EquippedPair : Candidate.EquippedCosmeticIds)
		{
			if (EquippedPair.Value.IsNone())
			{
				OutReason = TEXT("wardrobe_equipped_none");
				return false;
			}

			if (!Candidate.OwnedCosmeticIds.Contains(EquippedPair.Value))
			{
				OutReason = FString::Printf(
					TEXT("wardrobe_equipped_not_owned cosmetic=%s"),
					*EquippedPair.Value.ToString());
				return false;
			}
		}

		OutReason.Reset();
		return true;
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
		if (!UMelodiaNarrativeSubsystem::MigrateRecord(Candidate))
		{
			return false;
		}

		FString ValidationFailure;
		if (!ValidateIntrinsicNarrativeRecord(Candidate, ValidationFailure))
		{
			UE_LOG(LogTemp, Warning,
				TEXT("MELODIA_LOAD candidate rejected: %s"),
				*ValidationFailure);
			return false;
		}

		return true;
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

	if (FStrProperty* SlotNameProperty = FindFProperty<FStrProperty>(GameInstance->GetClass(), TEXT("slotName")))
	{
		SlotNameProperty->SetPropertyValue_InContainer(GameInstance, SlotName);
	}
	if (FObjectPropertyBase* SaveProperty = FindFProperty<FObjectPropertyBase>(GameInstance->GetClass(), TEXT("jRPGSaveGame")))
	{
		SaveProperty->SetObjectPropertyValue_InContainer(GameInstance, LoadedSave);
	}

	FName SavedMap = NAME_None;
	if (const FNameProperty* CurrentMapProperty = FindFProperty<FNameProperty>(LoadedSave->GetClass(), TEXT("currentMap")))
	{
		SavedMap = CurrentMapProperty->GetPropertyValue_InContainer(LoadedSave);
	}
	if (SavedMap.IsNone())
	{
		if (!Narrative->RestoreNarrativeRecordFromSave(LoadedSave))
		{
			UE_LOG(LogTemp, Warning, TEXT("MELODIA_LOAD refused canonical slot '%s': narrative restore failed."), *SlotName);
			EndLoadBoundary(Recovery, SlotName);
			return EMelodiaLoadSlotResult::Refused;
		}

		static const FName OpeningRoute(TEXT("/Game/Melodia/Levels/Opening/L_MelusinaMorning"));
		UE_LOG(LogTemp, Log, TEXT("Melodia canonical load: slot '%s' has no saved map; travelling to the authored first route."), *SlotName);

		EndLoadBoundary(Recovery, SlotName);
		if (UMelodiaTravelSubsystem* Travel = UMelodiaTravelSubsystem::Get(WorldContextObject))
		{
			if (Travel->TravelTo(OpeningRoute, NAME_None))
			{
				return EMelodiaLoadSlotResult::LoadedNarrativeRestored;
			}

			UE_LOG(LogTemp, Warning,
				TEXT("MELODIA_TRAVEL refused '%s' from the canonical-load fallback. Add it to DA_MelodiaIntegrationConfig -> Travel Level Ids. Using a direct OpenLevel for now, which skips spawn placement and the input-context clear."),
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
