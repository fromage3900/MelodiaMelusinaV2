#include "MelodiaExternalJRPGBridgeSubsystem.h"

#include "Engine/GameInstance.h"
#include "EngineUtils.h"
#include "MelodiaJRPGPostBattleLibrary.h"
#include "MelodiaSaveRecoverySubsystem.h"
#include "MelodiaNarrativeSubsystem.h"
#include "MelodiaNarrativeTypes.h"
#include "UObject/StructOnScope.h"
#include "UObject/UnrealType.h"

namespace
{
	// Blueprint user-defined enums keep internal identifiers such as
	// "NewEnumerator0". The authored terminal semantics live in their display
	// names (PlayerWon, EnemyWon, Fled), so classification must inspect both the
	// internal and display name rather than rely on raw ordinals, which are not
	// guaranteed to match EMelodiaBattleResult.
	constexpr TCHAR JRPGBattleResultPath[] = TEXT("/Game/TurnBasedJRPGTemplate/Blueprints/Battle/E_BattleResult.E_BattleResult");

	EMelodiaBattleResult ClassifyJRPGBattleResult(const uint8 BattleResult)
	{
		UEnum* ResultEnum = LoadObject<UEnum>(nullptr, JRPGBattleResultPath);
		if (!ResultEnum)
		{
			UE_LOG(LogTemp, Warning, TEXT("Melodia JRPG bridge: E_BattleResult enum unavailable; result %u classified as Unavailable."), static_cast<uint32>(BattleResult));
			return EMelodiaBattleResult::Unavailable;
		}

		const FString InternalResultName = ResultEnum->GetNameStringByValue(BattleResult).ToLower();
		const FString DisplayResultName = ResultEnum->GetDisplayNameTextByValue(BattleResult).ToString().ToLower();
		const FString ResultName = InternalResultName + TEXT(" ") + DisplayResultName;
		if (ResultName.Contains(TEXT("playerwon")) || ResultName.Contains(TEXT("victory")) || ResultName.Contains(TEXT("win")))
		{
			return EMelodiaBattleResult::Victory;
		}
		if (ResultName.Contains(TEXT("enemywon")) || ResultName.Contains(TEXT("defeat")) || ResultName.Contains(TEXT("lose")) || ResultName.Contains(TEXT("loss")))
		{
			return EMelodiaBattleResult::Defeat;
		}
		if (ResultName.Contains(TEXT("flee")) || ResultName.Contains(TEXT("fled")) || ResultName.Contains(TEXT("escape")))
		{
			return EMelodiaBattleResult::Fled;
		}
		return EMelodiaBattleResult::Unavailable;
	}
}

UMelodiaExternalJRPGBridgeSubsystem* UMelodiaExternalJRPGBridgeSubsystem::GetGameInstanceSubsystem(UGameInstance* GameInstance)
{
	return GameInstance ? GameInstance->GetSubsystem<UMelodiaExternalJRPGBridgeSubsystem>() : nullptr;
}

void UMelodiaExternalJRPGBridgeSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);
	if (UGameInstance* GI = GetGameInstance())
	{
		NarrativeSubsystem = GI->GetSubsystem<UMelodiaNarrativeSubsystem>();
		if (NarrativeSubsystem)
		{
			NarrativeSubsystem->OnBattleRequested.AddUniqueDynamic(this, &ThisClass::HandleNarrativeBattleRequested);
		}
	}
}

void UMelodiaExternalJRPGBridgeSubsystem::Deinitialize()
{
	UnbindActiveBattle();
	Super::Deinitialize();
}

bool UMelodiaExternalJRPGBridgeSubsystem::StartTaggedJRPGBattle(const FName EncounterId)
{
	if (EncounterId.IsNone() || IsValid(ActiveBattleActor))
	{
		UE_LOG(LogTemp, Warning, TEXT("Melodia JRPG bridge rejected %s: invalid encounter id or another battle is active."), *EncounterId.ToString());
		return false;
	}

	UWorld* World = GetWorld();
	if (!World)
	{
		UE_LOG(LogTemp, Error, TEXT("Melodia JRPG bridge rejected %s: gameplay world is unavailable."), *EncounterId.ToString());
		return false;
	}
	AActor* BattleActor = nullptr;
	int32 MatchCount = 0;
	for (TActorIterator<AActor> It(World); It; ++It)
	{
		if (It->ActorHasTag(EncounterId))
		{
			BattleActor = *It;
			++MatchCount;
		}
	}
	if (MatchCount != 1 || !IsValid(BattleActor))
	{
		UE_LOG(LogTemp, Error, TEXT("Melodia JRPG bridge rejected %s: expected exactly one tagged battle actor, found %d."), *EncounterId.ToString(), MatchCount);
		return false;
	}

	UFunction* StartBattle = BattleActor->FindFunction(TEXT("StartBattle"));
	FStructProperty* DataProperty = FindFProperty<FStructProperty>(BattleActor->GetClass(), TEXT("offLevelBattleData"));
	FArrayProperty* EnemyListProperty = FindFProperty<FArrayProperty>(BattleActor->GetClass(), TEXT("enemyList"));
	FMulticastDelegateProperty* BattleOver = FindFProperty<FMulticastDelegateProperty>(BattleActor->GetClass(), TEXT("OnBattleOver"));
	if (!StartBattle || !DataProperty || !EnemyListProperty || !BattleOver)
	{
		UE_LOG(LogTemp, Error, TEXT("Melodia JRPG bridge rejected %s: tagged actor lacks the stock battle contract."), *EncounterId.ToString());
		return false;
	}

	FStructProperty* DataParameter = FindFProperty<FStructProperty>(StartBattle, TEXT("offLevelBattleData"));
	FArrayProperty* EnemyListParameter = FindFProperty<FArrayProperty>(StartBattle, TEXT("enemyList"));
	if (
		!DataParameter
		|| !EnemyListParameter
		|| !DataParameter->SameType(DataProperty)
		|| !EnemyListParameter->SameType(EnemyListProperty)
	)
	{
		UE_LOG(LogTemp, Error, TEXT("Melodia JRPG bridge rejected %s: StartBattle parameters do not match the stock enemy-list and battle-data properties."), *EncounterId.ToString());
		return false;
	}

	FScriptArrayHelper EnemyList(EnemyListProperty, EnemyListProperty->ContainerPtrToValuePtr<void>(BattleActor));
	if (EnemyList.Num() == 0)
	{
		UE_LOG(LogTemp, Error, TEXT("Melodia JRPG bridge rejected %s: tagged battle actor has no authored enemy roster."), *EncounterId.ToString());
		return false;
	}

	FMulticastScriptDelegate* Delegate = BattleOver->ContainerPtrToValuePtr<FMulticastScriptDelegate>(BattleActor);
	if (!Delegate)
	{
		UE_LOG(LogTemp, Error, TEXT("Melodia JRPG bridge rejected %s: OnBattleOver delegate storage is unavailable."), *EncounterId.ToString());
		return false;
	}
	FScriptDelegate Completion;
	Completion.BindUFunction(this, GET_FUNCTION_NAME_CHECKED(ThisClass, HandleBattleOver));
	Delegate->AddUnique(Completion);
	ActiveBattleActor = BattleActor;
	ActiveEncounterId = EncounterId;

	FStructOnScope Parameters(StartBattle);
	EnemyListParameter->CopyCompleteValue(
		EnemyListParameter->ContainerPtrToValuePtr<void>(Parameters.GetStructMemory()),
		EnemyListProperty->ContainerPtrToValuePtr<void>(BattleActor));
	DataParameter->CopyCompleteValue(
		DataParameter->ContainerPtrToValuePtr<void>(Parameters.GetStructMemory()),
		DataProperty->ContainerPtrToValuePtr<void>(BattleActor));
	BattleActor->ProcessEvent(StartBattle, Parameters.GetStructMemory());
	OnJRPGBattleStarted.Broadcast(EncounterId);
	UE_LOG(LogTemp, Log, TEXT("Melodia JRPG bridge started %s on %s."), *EncounterId.ToString(), *BattleActor->GetName());
	return true;
}

void UMelodiaExternalJRPGBridgeSubsystem::HandleNarrativeBattleRequested(FName EncounterId)
{
	if (!StartTaggedJRPGBattle(EncounterId))
	{
		UE_LOG(LogTemp, Warning, TEXT("Melodia JRPG bridge: OnBattleRequested(%s) could not start tagged battle."), *EncounterId.ToString());
		if (NarrativeSubsystem)
		{
			// No battle started, so there is no terminal result. Release the
			// pending encounter without fabricating a battle outcome; the Quill
			// resume happens on the abort path with result unavailable.
			NarrativeSubsystem->AbortPendingBattle(TEXT("no tagged JRPG encounter could start"));
		}
	}
}

void UMelodiaExternalJRPGBridgeSubsystem::HandleBattleOver(uint8 BattleResult)
{
	// Restore party before the stock sync writes battle state back. This is the
	// proven CompleteBattle -> ResumeQuillOnce path (M1) - heal only, curentMP
	// spelling is the stock struct's typo.
	if (IsValid(ActiveBattleActor))
	{
		UObject* BattleController = nullptr;
		if (FObjectPropertyBase* BattleControllerProp = FindFProperty<FObjectPropertyBase>(ActiveBattleActor->GetClass(), TEXT("battleController")))
		{
			BattleController = BattleControllerProp->GetObjectPropertyValue_InContainer(ActiveBattleActor);
		}
		if (!IsValid(BattleController) && GetWorld())
		{
			for (TActorIterator<AActor> It(GetWorld()); It; ++It)
			{
				if (It->GetClass()->GetName().Contains(TEXT("BattleController")))
				{
					BattleController = *It;
					break;
				}
			}
		}
		if (IsValid(BattleController))
		{
			UMelodiaJRPGPostBattleLibrary::RestorePartyAfterBattle(BattleController);
		}
	}
	// The stock battle actor has already resolved its terminal result when this
	// delegate fires. Clear only the non-authoritative rhythm transient state
	// around the relay; do not classify the result, grant rewards, or restart the
	// stock battle here. The pre-relay call protects the defeat/death boundary,
	// while the post-relay call covers an authored retry/recovery listener.
	if (UGameInstance* GameInstance = GetGameInstance())
	{
		if (UMelodiaSaveRecoverySubsystem* Recovery = GameInstance->GetSubsystem<UMelodiaSaveRecoverySubsystem>())
		{
			Recovery->InvalidateRhythmTransientState(
				FString::Printf(TEXT("stock OnBattleOver before relay result=%u"), static_cast<uint32>(BattleResult)));
		}
	}

	OnJRPGBattleEnded.Broadcast(BattleResult);

	if (NarrativeSubsystem)
	{
		const EMelodiaBattleResult MelodiaResult = ClassifyJRPGBattleResult(BattleResult);
		NarrativeSubsystem->CompleteBattle(MelodiaResult);
		UE_LOG(LogTemp, Log, TEXT("MELUSINA_LOOP_BATTLE_COMPLETED encounter=%s result=%u typed=%d"), *ActiveEncounterId.ToString(), BattleResult, static_cast<int32>(MelodiaResult));
	}

	if (UGameInstance* GameInstance = GetGameInstance())
	{
		if (UMelodiaSaveRecoverySubsystem* Recovery = GameInstance->GetSubsystem<UMelodiaSaveRecoverySubsystem>())
		{
			Recovery->InvalidateRhythmTransientState(
				FString::Printf(TEXT("stock OnBattleOver after relay result=%u"), static_cast<uint32>(BattleResult)));
		}
	}

	UnbindActiveBattle();
}

void UMelodiaExternalJRPGBridgeSubsystem::UnbindActiveBattle()
{
	if (IsValid(ActiveBattleActor))
	{
		if (FMulticastDelegateProperty* Property = FindFProperty<FMulticastDelegateProperty>(ActiveBattleActor->GetClass(), TEXT("OnBattleOver")))
		{
			if (FMulticastScriptDelegate* Delegate = Property->ContainerPtrToValuePtr<FMulticastScriptDelegate>(ActiveBattleActor))
			{
				FScriptDelegate Completion;
				Completion.BindUFunction(this, GET_FUNCTION_NAME_CHECKED(ThisClass, HandleBattleOver));
				Delegate->Remove(Completion);
			}
		}
	}
	ActiveBattleActor = nullptr;
	ActiveEncounterId = NAME_None;
}
