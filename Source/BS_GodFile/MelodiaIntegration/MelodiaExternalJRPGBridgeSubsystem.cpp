#include "MelodiaExternalJRPGBridgeSubsystem.h"

#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "MelodiaHybridEncounterComponent.h"
#include "MelodiaJRPGPostBattleLibrary.h"
#include "MelodiaSaveRecoverySubsystem.h"
#include "MelodiaNarrativeSubsystem.h"
#include "MelodiaNarrativeTypes.h"
#include "MelodiaRhythmCombatSubsystem.h"
#include "UObject/StructOnScope.h"
#include "UObject/UnrealType.h"
#include "UObject/Script.h"

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

UMelodiaExternalJRPGBridgeSubsystem::UMelodiaExternalJRPGBridgeSubsystem()
{
	UE_LOG(LogTemp, Log, TEXT("MelodiaExternalJRPGBridgeSubsystem::Constructor called"));
}

UMelodiaExternalJRPGBridgeSubsystem* UMelodiaExternalJRPGBridgeSubsystem::GetGameInstanceSubsystem(UGameInstance* GameInstance)
{
	return GameInstance ? GameInstance->GetSubsystem<UMelodiaExternalJRPGBridgeSubsystem>() : nullptr;
}

void UMelodiaExternalJRPGBridgeSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);
	UE_LOG(LogTemp, Log, TEXT("MelodiaExternalJRPGBridgeSubsystem::Initialize called"));
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
	for (const auto& Pair : WorldDamageBindings)
	{
		if (UMelodiaHybridEncounterComponent* Encounter = Pair.Value.Encounter.Get())
		{
			Encounter->OnWorldEffectRequested.RemoveDynamic(this, &ThisClass::HandleWorldEffectRequested);
		}
	}
	WorldDamageBindings.Reset();
	UnbindActiveBattle();
	Super::Deinitialize();
}

bool UMelodiaExternalJRPGBridgeSubsystem::BindWorldDamageResolver(
	UMelodiaHybridEncounterComponent* Encounter, UObject* StockAttacker,
	UObject* StockDefenderStats, UObject* StockSkill, const int32 PureDamage)
{
	UClass* UnitClass = LoadClass<UObject>(nullptr,
		TEXT("/Game/TurnBasedJRPGTemplate/Blueprints/Units/BP_UnitBase.BP_UnitBase_C"));
	UClass* SkillClass = LoadClass<UObject>(nullptr,
		TEXT("/Game/TurnBasedJRPGTemplate/Blueprints/Skills/BP_BattleSkillBase.BP_BattleSkillBase_C"));
	if (!IsValid(Encounter) || !HasUniqueWorldEncounter(Encounter, Encounter->GetEncounterId())
		|| !UnitClass || !IsValid(StockAttacker) || !StockAttacker->IsA(UnitClass)
		|| !IsValid(StockDefenderStats) || !StockDefenderStats->IsA(UnitClass)
		|| (StockSkill && (!IsValid(StockSkill) || !SkillClass || !StockSkill->IsA(SkillClass))) || PureDamage < 0)
	{
		return false;
	}
	// Binding while a phrase is active would replace its authoritative inputs.
	if (Encounter->GetPresentationMode() != EMelodiaHybridPresentationMode::Flow)
	{
		return false;
	}
	FWorldDamageBinding Binding;
	Binding.Encounter = Encounter;
	Binding.Attacker = StockAttacker;
	Binding.DefenderStats = StockDefenderStats;
	Binding.Skill = StockSkill;
	Binding.PureDamage = PureDamage;
	WorldDamageBindings.Add(FObjectKey(Encounter), Binding);
	Encounter->OnWorldEffectRequested.AddUniqueDynamic(this, &ThisClass::HandleWorldEffectRequested);
	return true;
}

void UMelodiaExternalJRPGBridgeSubsystem::UnbindWorldDamageResolver(UMelodiaHybridEncounterComponent* Encounter)
{
	if (Encounter)
	{
		Encounter->OnWorldEffectRequested.RemoveDynamic(this, &ThisClass::HandleWorldEffectRequested);
		WorldDamageBindings.Remove(FObjectKey(Encounter));
	}
}

bool UMelodiaExternalJRPGBridgeSubsystem::InvokeStockDamageResolver(
	const FWorldDamageBinding& Binding, const double Multiplier, int32& OutDamage)
{
	OutDamage = 0;
	if (!IsInGameThread() || bResolvingStockDamage || !Binding.Attacker.IsValid()
		|| !Binding.DefenderStats.IsValid() || Binding.Skill.IsStale()
		|| !FMath::IsFinite(Multiplier) || Multiplier < 0.0)
	{
		return false;
	}
	UClass* ControllerClass = LoadClass<UObject>(nullptr,
		TEXT("/Game/TurnBasedJRPGTemplate/Blueprints/Battle/BP_BattleController.BP_BattleController_C"));
	UObject* Calculator = ControllerClass ? ControllerClass->GetDefaultObject() : nullptr;
	UFunction* CalculateDamage = Calculator ? Calculator->FindFunction(TEXT("CalculateDamage")) : nullptr;
	FIntProperty* PureDamage = CalculateDamage ? FindFProperty<FIntProperty>(CalculateDamage, TEXT("pureDamage")) : nullptr;
	FDoubleProperty* DamageMultiplier = CalculateDamage ? FindFProperty<FDoubleProperty>(CalculateDamage, TEXT("damageMultiplier")) : nullptr;
	FIntProperty* Damage = CalculateDamage ? FindFProperty<FIntProperty>(CalculateDamage, TEXT("damage")) : nullptr;
	FObjectPropertyBase* Attacker = ControllerClass ? FindFProperty<FObjectPropertyBase>(ControllerClass, TEXT("currentAttackingUnit")) : nullptr;
	FObjectPropertyBase* Defender = ControllerClass ? FindFProperty<FObjectPropertyBase>(ControllerClass, TEXT("currentTargetUnit")) : nullptr;
	FObjectPropertyBase* Skill = ControllerClass ? FindFProperty<FObjectPropertyBase>(ControllerClass, TEXT("currentSkill")) : nullptr;
	if (!PureDamage || !DamageMultiplier || !Damage || !Damage->HasAnyPropertyFlags(CPF_OutParm)
		|| !Attacker || !Defender || !Skill || CalculateDamage->NumParms != 3)
	{
		UE_LOG(LogTemp, Error, TEXT("MELODIA_HYBRID stock CalculateDamage contract changed; effect remains pending."));
		return false;
	}

	// CalculateDamage/IsHit use function-local multiplier/hitChance and stock
	// stat reads; neither calls DealDamage or writes a unit's HP. Use their
	// existing class function context without spawning a controller/battle/unit.
	// The three contextual references are borrowed synchronously on the game
	// thread and restored before any encounter/delegate callback is dispatched.
	TGuardValue<bool> ResolvingGuard(bResolvingStockDamage, true);
#if WITH_EDITOR
	FEditorScriptExecutionGuard ScriptExecutionGuard;
#endif
	UObject* PreviousAttacker = Attacker->GetObjectPropertyValue_InContainer(Calculator);
	UObject* PreviousDefender = Defender->GetObjectPropertyValue_InContainer(Calculator);
	UObject* PreviousSkill = Skill->GetObjectPropertyValue_InContainer(Calculator);
	Attacker->SetObjectPropertyValue_InContainer(Calculator, Binding.Attacker.Get());
	Defender->SetObjectPropertyValue_InContainer(Calculator, Binding.DefenderStats.Get());
	Skill->SetObjectPropertyValue_InContainer(Calculator, Binding.Skill.Get());
	FStructOnScope Params(CalculateDamage);
	PureDamage->SetPropertyValue_InContainer(Params.GetStructMemory(), Binding.PureDamage);
	DamageMultiplier->SetPropertyValue_InContainer(Params.GetStructMemory(), Multiplier);
	Calculator->ProcessEvent(CalculateDamage, Params.GetStructMemory());
	OutDamage = Damage->GetPropertyValue_InContainer(Params.GetStructMemory());
	Attacker->SetObjectPropertyValue_InContainer(Calculator, PreviousAttacker);
	Defender->SetObjectPropertyValue_InContainer(Calculator, PreviousDefender);
	Skill->SetObjectPropertyValue_InContainer(Calculator, PreviousSkill);
	UE_LOG(LogTemp, Log, TEXT("MELODIA_HYBRID_STOCK_RESOLVED resolver=BP_BattleController.CalculateDamage multiplier=%.3f final=%d"),
		Multiplier, OutDamage);
	return OutDamage >= 0;
}

bool UMelodiaExternalJRPGBridgeSubsystem::ResolveWorldFlowAttack(UMelodiaHybridEncounterComponent* Encounter)
{
	if (!IsValid(Encounter) || !IsValid(Encounter->GetEncounterTarget())
		|| !Encounter->GetEncounterTarget()->CanBeDamaged()
		|| Encounter->GetPresentationMode() != EMelodiaHybridPresentationMode::Flow)
	{
		return false;
	}
	const FWorldDamageBinding* Found = WorldDamageBindings.Find(FObjectKey(Encounter));
	if (!Found)
	{
		return false;
	}
	const FWorldDamageBinding Binding = *Found;
	int32 FinalDamage = 0;
	return InvokeStockDamageResolver(Binding, 1.0, FinalDamage)
		&& (FinalDamage == 0 || Encounter->ApplyResolvedFlowDamage(FinalDamage));
}

void UMelodiaExternalJRPGBridgeSubsystem::HandleWorldEffectRequested(
	AActor* Target, const FMelodiaRhythmEffectRequest& Request)
{
	UMelodiaRhythmCombatSubsystem* Rhythm = UMelodiaRhythmCombatSubsystem::Get(this);
	UMelodiaHybridEncounterComponent* Encounter = IsValid(Target)
		? Target->FindComponentByClass<UMelodiaHybridEncounterComponent>() : nullptr;
	if (!Rhythm || !IsValid(Encounter) || !Request.bConsumed
		|| Request.SessionId != Rhythm->GetActiveSessionId()
		|| Request.SessionId != Encounter->GetSequenceSessionId() || !Encounter->HasPendingSequenceEffect())
	{
		return;
	}
	const FWorldDamageBinding* Found = WorldDamageBindings.Find(FObjectKey(Encounter));
	if (!Found)
	{
		return;
	}
	const FWorldDamageBinding Binding = *Found;
	int32 FinalDamage = 0;
	// RhythmCombat already latched BaseMagnitude * grade once. Pass its FINAL
	// multiplier to stock, exactly as the existing DealDamage sites do; never
	// multiply Request.RhythmScalar (or stats) again in this bridge.
	if (InvokeStockDamageResolver(Binding, Rhythm->GetPendingDamageMultiplier(), FinalDamage))
	{
		Rhythm->ClearPendingDamageMultiplier();
		Encounter->ApplyResolvedSequenceDamage(FinalDamage, Request.SessionId);
	}
}

bool UMelodiaExternalJRPGBridgeSubsystem::HasUniqueWorldEncounter(
	const UMelodiaHybridEncounterComponent* Encounter, const FName EncounterId) const
{
	UWorld* World = GetWorld();
	AActor* Target = IsValid(Encounter) ? Encounter->GetEncounterTarget() : nullptr;
	if (!World || EncounterId.IsNone() || !IsValid(Target) || Target->GetWorld() != World
		|| Encounter->GetEncounterId() != EncounterId)
	{
		return false;
	}

	TArray<UMelodiaHybridEncounterComponent*> TargetComponents;
	Target->GetComponents(TargetComponents);
	if (TargetComponents.Num() != 1 || TargetComponents[0] != Encounter) return false;

	int32 MatchingComponents = 0;
	for (TActorIterator<AActor> It(World); It; ++It)
	{
		AActor* Actor = *It;
		// A tagged stock battle actor with this identity would create a second
		// combat state. The claimed world target may carry its own identity tag.
		if (Actor != Target && Actor->ActorHasTag(EncounterId))
		{
			return false;
		}

		TArray<UMelodiaHybridEncounterComponent*> Components;
		Actor->GetComponents(Components);
		for (UMelodiaHybridEncounterComponent* Candidate : Components)
		{
			if (IsValid(Candidate) && Candidate->GetEncounterId() == EncounterId)
			{
				++MatchingComponents;
				if (Candidate != Encounter || Candidate->GetEncounterTarget() != Actor)
				{
					return false;
				}
			}
		}
	}
	return MatchingComponents == 1;
}

bool UMelodiaExternalJRPGBridgeSubsystem::CompleteWorldEncounter(
	UMelodiaHybridEncounterComponent* Encounter, const EMelodiaBattleResult Result)
{
	if (!IsValid(Encounter))
	{
		return false;
	}
	const FName EncounterId = Encounter->GetEncounterId();
	if (!IsValid(NarrativeSubsystem) || IsValid(ActiveBattleActor)
		|| NarrativeSubsystem->IsWorldEncounterCompleted(EncounterId)
		|| NarrativeSubsystem->IsBattlePending()
		|| !HasUniqueWorldEncounter(Encounter, EncounterId))
	{
		UE_LOG(LogTemp, Warning, TEXT("Melodia world encounter completion rejected for %s: identity, outcome, or narrative state is invalid."),
			*EncounterId.ToString());
		return false;
	}

	// World completion does not request/start a stock battle or stop/resume
	// Quill. Both routes share Narrative's terminal receipt/event implementation;
	// only Narrative's existing durable consumed-intent record guards replay.
	return NarrativeSubsystem->CompleteWorldEncounterOutcome(EncounterId, Result);
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

	// Heal-only party restore before narrative resume (owner decision: no
	// retry-on-defeat). Find the live BP_BattleController the same way the UI
	// bridge does — ActiveBattleActor is the tagged encounter, not the controller.
	if (UWorld* World = GetWorld())
	{
		AActor* BattleController = nullptr;
		for (TActorIterator<AActor> It(World); It; ++It)
		{
			if (It->GetClass()->GetName().StartsWith(TEXT("BP_BattleController")))
			{
				BattleController = *It;
				break;
			}
		}
		if (BattleController)
		{
			UMelodiaJRPGPostBattleLibrary::RestorePartyAfterBattle(BattleController);
		}
		else
		{
			UE_LOG(LogTemp, Warning, TEXT("MELODIA_RECOVERY no BP_BattleController in world at battle-over; party not restored."));
		}
	}

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
