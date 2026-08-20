// Authoritative battle encounter orchestrator.
// Adapted from MelodiaMelusina_PROD ΓÇö self-contained, no JRPG template bridge.

#include "MelodiaBattleSession.h"
#include "MelodiaAudioComponent.h"
#include "MelodiaBattleArena.h"
#include "MelodiaEnemyDefinition.h"
#include "MelodiaProgressionComponent.h"
#include "MelodiaRulesGenerated.h"

#include "Engine/World.h"
#include "EngineUtils.h"
#include "MelodiaCombatStateComponent.h"
#include "MelodiaCoreRulesLibrary.h"
#include "MelodiaEncounterTrigger.h"
#include "MelodiaOpeningFlowSubsystem.h"
#include "MelodiaOpeningStateAnchor.h"
#include "MelodiaOpeningStateComponent.h"
#include "MelodiaRoguelikeRunSubsystem.h"
#include "MelodiaKeySystemLibrary.h"
#include "MelodiaRhythmExecutionComponent.h"
#include "MelodiaRhythmHUDWidget.h"
#include "MelodiaRhythmReactivitySubsystem.h"
#include "MelodiaCombatPresentationInterface.h"
#include "MelodiaEnemyPresentationInterface.h"
#include "MelodiaPacingSubsystem.h"
#include "Kismet/GameplayStatics.h"

namespace MelodiaBattleSessionPrivate
{
FString PhaseDisplayName(const EMelodiaBattlePhase Phase)
{
	if (const UEnum* PhaseEnum = StaticEnum<EMelodiaBattlePhase>())
	{
		return PhaseEnum->GetDisplayNameTextByValue(static_cast<int64>(Phase)).ToString();
	}
	return TEXT("Unknown");
}

EMelodiaRhythmGrade GradeFromAverageMultiplier(const float AverageMultiplier)
{
	if (AverageMultiplier >= 1.4f)
	{
		return EMelodiaRhythmGrade::Perfect;
	}
	if (AverageMultiplier >= 1.2f)
	{
		return EMelodiaRhythmGrade::Great;
	}
	if (AverageMultiplier >= 0.9f)
	{
		return EMelodiaRhythmGrade::Good;
	}
	return EMelodiaRhythmGrade::Miss;
}

FString CommandDisplayName(const EMelodiaRhythmCommandType CommandType)
{
	switch (CommandType)
	{
	case EMelodiaRhythmCommandType::Skill:
		return TEXT("Skill");
	case EMelodiaRhythmCommandType::Basic:
		return TEXT("Basic");
	case EMelodiaRhythmCommandType::None:
	default:
		return TEXT("Command");
	}
}

EMelodiaModifierStat ModifierStatFromRule(const TCHAR* Stat)
{
	const FName Id(Stat);
	if (Id == TEXT("defense")) return EMelodiaModifierStat::Defense;
	if (Id == TEXT("speed")) return EMelodiaModifierStat::Speed;
	if (Id == TEXT("rhythm_window")) return EMelodiaModifierStat::RhythmWindow;
	if (Id == TEXT("sp_gain")) return EMelodiaModifierStat::SPGain;
	if (Id == TEXT("ult_gain")) return EMelodiaModifierStat::UltGain;
	if (Id == TEXT("damage_taken")) return EMelodiaModifierStat::DamageTaken;
	return EMelodiaModifierStat::Attack;
}

EMelodiaModifierOp ModifierOpFromRule(const TCHAR* Op)
{
	return FName(Op) == TEXT("add") ? EMelodiaModifierOp::Add : EMelodiaModifierOp::Mul;
}

EMelodiaModifierStacking ModifierStackingFromRule(const TCHAR* Stacking)
{
	const FName Id(Stacking);
	if (Id == TEXT("stack")) return EMelodiaModifierStacking::Stack;
	if (Id == TEXT("ignore")) return EMelodiaModifierStacking::Ignore;
	return EMelodiaModifierStacking::Refresh;
}

/** "Losing power because she's away from her companion": the current Dissonance
 * SongcraftScalar (1.0 = full power, falling toward 0 as she drifts from Sir
 * Melodious) is applied as a multiplicative Attack modifier for the encounter.
 * No anchor in the world (e.g. a combat space with no opening-flow state) means
 * no penalty - EvaluateModifier's base scalar is 1.0 either way. */
void ApplyDissonanceSongcraftModifier(UWorld* World, UMelodiaCombatStateComponent& CombatState)
{
	if (!World)
	{
		return;
	}
	for (TActorIterator<AMelodiaOpeningStateAnchor> It(World); It; ++It)
	{
		if (const UMelodiaDissonanceComponent* Dissonance = It->Dissonance)
		{
			CombatState.ApplyModifier(TEXT("DissonanceSongcraft"), EMelodiaModifierStat::Attack,
				EMelodiaModifierOp::Mul, Dissonance->SongcraftScalar, -1,
				EMelodiaModifierStacking::Refresh, 1);
		}
		break;
	}
}

bool ApplyGeneratedModifier(UMelodiaCombatStateComponent& CombatState, const FName ModifierId)
{
	MelodiaRulesGen::FGeneratedModifier Rule;
	if (!MelodiaRulesGen::FindGeneratedModifier(ModifierId, Rule))
	{
		return false;
	}

	CombatState.ApplyModifier(
		ModifierId,
		ModifierStatFromRule(Rule.Stat),
		ModifierOpFromRule(Rule.Op),
		Rule.Value,
		Rule.DurationTurns,
		ModifierStackingFromRule(Rule.Stacking),
		Rule.MaxStacks);
	return true;
}
}

void UMelodiaBattleSession::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);
	BattlePhase = EMelodiaBattlePhase::None;
	HUDMode = EMelodiaHUDMode::Exploration;
}

UMelodiaBattleSession* UMelodiaBattleSession::Get(const UObject* WorldContextObject)
{
	if (!WorldContextObject)
	{
		return nullptr;
	}

	const UWorld* World = WorldContextObject->GetWorld();
	if (!World)
	{
		return nullptr;
	}

	UGameInstance* GI = World->GetGameInstance();
	return GI ? GI->GetSubsystem<UMelodiaBattleSession>() : nullptr;
}

bool UMelodiaBattleSession::IsEncounterActive() const
{
	return BattlePhase != EMelodiaBattlePhase::None
		&& BattlePhase != EMelodiaBattlePhase::Victory
		&& BattlePhase != EMelodiaBattlePhase::Defeat
		&& BattlePhase != EMelodiaBattlePhase::Fled;
}

bool UMelodiaBattleSession::IsAwaitingPlayerCommand() const
{
	return BattlePhase == EMelodiaBattlePhase::AwaitingPlayerCommand;
}

bool UMelodiaBattleSession::IsRhythmExecutionActive() const
{
	if (const UMelodiaRhythmExecutionComponent* Execution = ActiveBattleController ? ActiveBattleController->FindComponentByClass<UMelodiaRhythmExecutionComponent>() : nullptr)
	{
		return Execution->IsExecutionActive();
	}
	return BattlePhase == EMelodiaBattlePhase::RhythmExecution;
}

UMelodiaCombatStateComponent* UMelodiaBattleSession::GetCombatState() const
{
	return ActiveBattleController ? ActiveBattleController->FindComponentByClass<UMelodiaCombatStateComponent>() : nullptr;
}

void UMelodiaBattleSession::NotifyPlayerCommandPresentation(const FName CommandId, const EMelodiaRhythmGrade RhythmGrade) const
{
	APawn* PlayerPawn = UGameplayStatics::GetPlayerPawn(this, 0);
	if (PlayerPawn && PlayerPawn->GetClass()->ImplementsInterface(UMelodiaCombatPresentationInterface::StaticClass()))
	{
		IMelodiaCombatPresentationInterface::Execute_OnMelodiaCommandResolved(PlayerPawn, CommandId, RhythmGrade);
	}

	// Cozy: HUD gets direct grade feedback regardless of whether the pawn implements the interface.
	if (RhythmGrade == EMelodiaRhythmGrade::Perfect)
	{
		if (UMelodiaRhythmHUDWidget* HUD = UMelodiaRhythmHUDWidget::FindFirst(this))
		{
			HUD->NotifyPerfectHit();
		}
	}
}

void UMelodiaBattleSession::NotifyPlayerDefeatPresentation() const
{
	APawn* PlayerPawn = UGameplayStatics::GetPlayerPawn(this, 0);
	if (PlayerPawn && PlayerPawn->GetClass()->ImplementsInterface(UMelodiaCombatPresentationInterface::StaticClass()))
	{
		IMelodiaCombatPresentationInterface::Execute_OnMelodiaDefeat(PlayerPawn);
	}
}

void UMelodiaBattleSession::NotifyPlayerVictoryPresentation() const
{
	APawn* PlayerPawn = UGameplayStatics::GetPlayerPawn(this, 0);
	if (PlayerPawn && PlayerPawn->GetClass()->ImplementsInterface(UMelodiaCombatPresentationInterface::StaticClass()))
	{
		IMelodiaCombatPresentationInterface::Execute_OnMelodiaVictory(PlayerPawn);
	}
}

void UMelodiaBattleSession::NotifyEnemyIntentPresentation() const
{
	AActor* EnemyActor = ActiveEncounter.EnemyActor;
	if (EnemyActor && EnemyActor->GetClass()->ImplementsInterface(UMelodiaEnemyPresentationInterface::StaticClass()))
	{
		IMelodiaEnemyPresentationInterface::Execute_OnMelodiaEnemyIntentStarted(
			EnemyActor, ActiveEnemyId, FName(*ActiveEnemyIntentName.ToString()));
	}
}

float UMelodiaBattleSession::ComputeEncounterTension() const
{
	// Incoming attack power is the primary driver (staged telegraphs ramp it).
	float Tension = FMath::Clamp(ActiveEnemyIntentDamage / 100.0f, 0.0f, 1.0f);

	// Low remaining enemy HP reads as a tense finish -- the fight feels closing-in.
	if (EnemyMaxHP > 0.0f)
	{
		const float Remaining = FMath::Clamp(EnemyHP / EnemyMaxHP, 0.0f, 1.0f);
		Tension = FMath::Max(Tension, 1.0f - Remaining);
	}

	// Each staged action taken adds a little more dread (bounded).
	Tension = FMath::Min(1.0f, Tension + FMath::Min(StagedActionsTaken, 4) * 0.08f);

	return Tension;
}

void UMelodiaBattleSession::NotifyEnemyHitPresentation(const float Damage, const EMelodiaRhythmGrade RhythmGrade) const
{
	AActor* EnemyActor = ActiveEncounter.EnemyActor;
	if (EnemyActor && EnemyActor->GetClass()->ImplementsInterface(UMelodiaEnemyPresentationInterface::StaticClass()))
	{
		IMelodiaEnemyPresentationInterface::Execute_OnMelodiaEnemyHit(EnemyActor, ActiveEnemyId, Damage, RhythmGrade);
	}
}

void UMelodiaBattleSession::NotifyEnemyBrokenPresentation() const
{
	AActor* EnemyActor = ActiveEncounter.EnemyActor;
	if (EnemyActor && EnemyActor->GetClass()->ImplementsInterface(UMelodiaEnemyPresentationInterface::StaticClass()))
	{
		IMelodiaEnemyPresentationInterface::Execute_OnMelodiaEnemyBroken(EnemyActor, ActiveEnemyId);
	}
	// Feel: weakness break lands hard — freeze frame, heavy shake, dolly push-in.
	if (AMelodiaBattleArena* Arena = Cast<AMelodiaBattleArena>(ActiveBattleController))
	{
		Arena->Hitstop(0.03f, 0.12f);
		Arena->PlayShake(1.0f);
		Arena->PlayBreakDollyIn();
	}
}

void UMelodiaBattleSession::NotifyEnemyDefeatedPresentation() const
{
	AActor* EnemyActor = ActiveEncounter.EnemyActor;
	if (EnemyActor && EnemyActor->GetClass()->ImplementsInterface(UMelodiaEnemyPresentationInterface::StaticClass()))
	{
		IMelodiaEnemyPresentationInterface::Execute_OnMelodiaEnemyDefeated(EnemyActor, ActiveEnemyId);
	}
}

bool UMelodiaBattleSession::CanSubmitBasicCommand() const
{
	if (BattlePhase == EMelodiaBattlePhase::Victory)
	{
		return true; // Confirm reward
	}
	return IsAwaitingPlayerCommand() && !IsRhythmExecutionActive();
}

bool UMelodiaBattleSession::CanSubmitSkillCommand(const FName SkillId) const
{
	if (SkillId.IsNone() || !IsAwaitingPlayerCommand() || IsRhythmExecutionActive())
	{
		return false;
	}

	const UMelodiaCombatStateComponent* CombatState = GetCombatState();
	if (!CombatState)
	{
		return false;
	}

	FMelodiaSongSkillRecipe Recipe;
	if (!UMelodiaSongSkillLibrary::FindSongSkill(SkillId, Recipe))
	{
		return false;
	}

	const int32 SkillCost = Recipe.SPCostOverride > 0 ? Recipe.SPCostOverride : 1;
	return CombatState->CanSpendSkillPoints(SkillCost);
}

bool UMelodiaBattleSession::CanSubmitUltimateCommand() const
{
	if (BattlePhase == EMelodiaBattlePhase::Victory)
	{
		return false;
	}

	const UMelodiaCombatStateComponent* CombatState = GetCombatState();
	return IsAwaitingPlayerCommand() && !IsRhythmExecutionActive() && CombatState && CombatState->bUltimateReady;
}

bool UMelodiaBattleSession::CanSubmitFleeCommand() const
{
	if (BattlePhase == EMelodiaBattlePhase::Victory)
	{
		return false;
	}
	return IsAwaitingPlayerCommand() && !IsRhythmExecutionActive();
}

// --- Encounter lifecycle ---

bool UMelodiaBattleSession::BeginEncounter(const FMelodiaEncounterDefinition& Encounter)
{
	if (!Encounter.BattleController)
	{
		return false;
	}

	if (IsEncounterActive())
	{
		UE_LOG(LogTemp, Warning, TEXT("Melodia battle session: encounter already active."));
		return false;
	}

	LastEncounterResult = EMelodiaEncounterResult::None;
	CommandSubmitCount = 0;
	EncounterPhaseLogCount = 0;
	LastEncounterPhaseLogEntry.Reset();

	SessionCombo = 0;
	SessionMaxCombo = 0;
	SessionScore = 0.0f;
	LastBattleResults = FMelodiaBattleResultsSummary();

	// GS-003: seed the AV race. Lowest AV acts next; costs accrue per action.
	UltimateInterruptCount = 0;
	PlayerAV = UMelodiaCoreRulesLibrary::CalculateAVCost(GetEffectivePlayerSpeed(), MelodiaRulesGen::BaseAV);
	EnemyAV = UMelodiaCoreRulesLibrary::CalculateAVCost(FMath::Max(1, EnemySpeed), MelodiaRulesGen::BaseAV);

	ActiveEncounter = Encounter;
	ActiveBattleController = Encounter.BattleController;
	if (ActiveBattleController && ActiveBattleController->GetWorld())
	{
		if (UMelodiaRhythmReactivitySubsystem* Reactivity = ActiveBattleController->GetWorld()->GetSubsystem<UMelodiaRhythmReactivitySubsystem>())
		{
			Reactivity->ResetEncounter();
		}
	}
	// Reset combat state on the battle controller
	if (UMelodiaCombatStateComponent* CombatState = GetCombatState())
	{
		HydrateCombatStateFromPersistentParty(*CombatState);
		CombatState->ResetActionEconomy(false);
		// Crescendo is a cross-encounter performance arc. Do not clear it here;
		// activation (or an explicit game-state reset) is responsible for reset.
		CombatState->EnemyElement = UMelodiaKeySystemLibrary::GetEnemyElementForEncounterLevel(Encounter.EncounterLevel);
		MelodiaBattleSessionPrivate::ApplyDissonanceSongcraftModifier(
			ActiveBattleController ? ActiveBattleController->GetWorld() : nullptr, *CombatState);
	}

	bool bUsedNamedEnemy = false;
	ActiveEnemyId = NAME_None;
	ActiveEnemyIntentName = FText::FromString(TEXT("Wild Strike"));
	ActiveEnemyIntentDamage = EnemyBaseDamage;
	ActiveEnemyBPM = 128.0f;
	if (!Encounter.EnemyId.IsNone())
	{
		for (const FMelodiaEnemyDef& Enemy : UMelodiaEnemyDataAsset::GetDemoEnemies())
		{
			if (Enemy.EnemyId == Encounter.EnemyId)
			{
				EnemyMaxHP = Enemy.MaxHP;
				EnemyBaseDamage = Enemy.BaseDamage;
				EnemySpeed = Enemy.Speed;
				ActiveEnemyId = Enemy.EnemyId;
				ActiveEnemyIntentName = Enemy.PrimaryIntentName;
				ActiveEnemyIntentDamage = Enemy.BaseDamage * FMath::Max(0.0f, Enemy.PrimaryIntentDamageMultiplier);
				ActiveEnemyBPM = Enemy.BPMOverride > 0.0f ? Enemy.BPMOverride : ActiveEnemyBPM;
				if (UMelodiaCombatStateComponent* CombatState = GetCombatState())
				{
					CombatState->EnemyElement = Enemy.Element;
					CombatState->EnemyToughnessMax = Enemy.MaxToughness;
					CombatState->ResetEnemyToughness(false);
				}
				if (UMelodiaRhythmExecutionComponent* Execution = ActiveBattleController->FindComponentByClass<UMelodiaRhythmExecutionComponent>())
				{
					Execution->BPM = ActiveEnemyBPM;
				}
				if (AMelodiaEncounterTrigger* Trigger = Cast<AMelodiaEncounterTrigger>(ActiveBattleController))
				{
					Trigger->ConfigureEnemyPresentation(Enemy);
				}
				bUsedNamedEnemy = true;
				break;
			}
		}
	}

	if (!bUsedNamedEnemy)
	{
		// Backward-compatible fallback for existing anonymous level triggers.
		const float LevelScalar = 1.0f + static_cast<float>(FMath::Clamp(Encounter.EncounterLevel, 1, 30) - 1) * 0.12f;
		EnemyMaxHP = 100.0f * LevelScalar;
		EnemyBaseDamage = 12.0f + static_cast<float>(Encounter.EncounterLevel) * 1.5f;
		EnemySpeed = 70 + Encounter.EncounterLevel * 3;
		ActiveEnemyIntentDamage = EnemyBaseDamage;
	}
	EnemyHP = EnemyMaxHP;
	if (UMelodiaCombatStateComponent* CombatState = GetCombatState())
	{
		CombatState->EnemyIntentName = ActiveEnemyIntentName.ToString();
		CombatState->EnemyIntentPower = ActiveEnemyIntentDamage;
	}

	SetBattlePhase(EMelodiaBattlePhase::AwaitingPlayerCommand);

	// Start encounter BGM ΓÇö quantized to the Quartz battle clock when the rhythm component opts in
	// (falls back to the plain PlayBGM path, matching the component's own automatic wall-clock fallback).
	if (ActiveBattleController)
	{
		if (UMelodiaAudioComponent* Audio = ActiveBattleController->FindComponentByClass<UMelodiaAudioComponent>())
		{
			const UMelodiaRhythmExecutionComponent* Rhythm = ActiveBattleController->FindComponentByClass<UMelodiaRhythmExecutionComponent>();
			if (Rhythm && Rhythm->bUseQuartzClock)
			{
				Audio->StartBattleClock(Rhythm->BPM);
				Audio->PlayBGMQuantized();
			}
			else
			{
				Audio->PlayBGM(Encounter.EnemyId);
			}
		}
	}
	UE_LOG(LogTemp, Log, TEXT("Melodia battle session: encounter begin (level %d, enemy HP %.0f)."),
		Encounter.EncounterLevel, EnemyHP);
	return true;
}

void UMelodiaBattleSession::UpdateSessionCombo(const FMelodiaRhythmExecutionResult& Result)
{
	if (Result.MissCount > 0 && Result.HitCount == 0)
	{
		SessionCombo = 0;
	}
	else if (Result.HitCount > 0)
	{
		SessionCombo += Result.HitCount;
	}
	SessionMaxCombo = FMath::Max(SessionMaxCombo, SessionCombo);

	// Aggregate results-screen tallies (PerfectCount is a subset of HitCount).
	LastBattleResults.PerfectCount += Result.PerfectCount;
	LastBattleResults.HitCount += FMath::Max(0, Result.HitCount - Result.PerfectCount);
	LastBattleResults.MissCount += Result.MissCount;
	LastBattleResults.TotalNotes += Result.TotalNotes;
}

void UMelodiaBattleSession::HydrateCombatStateFromPersistentParty(UMelodiaCombatStateComponent& CombatState)
{
	if (!bPersistentPartyStateInitialized)
	{
		StorePersistentPartyFromCombatState(CombatState);
		bPersistentPartyStateInitialized = true;
	}

	CombatState.PartyMaxHP = FMath::Max(1.0f, PersistentPartyMaxHP);
	CombatState.PartyHP = FMath::Clamp(PersistentPartyHP, 0.0f, CombatState.PartyMaxHP);
	CombatState.SkillPointMax = FMath::Max(1, PersistentSkillPointMax);
	CombatState.SkillPoints = FMath::Clamp(PersistentSkillPoints, 0, CombatState.SkillPointMax);
	CombatState.UltimateGauge = FMath::Clamp(PersistentUltimateGauge, 0.0f, CombatState.UltimateMax);
	CombatState.bUltimateReady = CombatState.UltimateGauge >= CombatState.UltimateMax;
	CombatState.EquippedKeyElement = PersistentEquippedKeyElement;
	CombatState.bHasHarmonicKeyEquipped = bPersistentHarmonicKeyEquipped;
}

void UMelodiaBattleSession::StorePersistentPartyFromCombatState(const UMelodiaCombatStateComponent& CombatState)
{
	PersistentPartyMaxHP = FMath::Max(1.0f, CombatState.PartyMaxHP);
	PersistentPartyHP = FMath::Clamp(CombatState.PartyHP, 0.0f, PersistentPartyMaxHP);
	PersistentSkillPointMax = FMath::Max(1, CombatState.SkillPointMax);
	PersistentSkillPoints = FMath::Clamp(CombatState.SkillPoints, 0, PersistentSkillPointMax);
	PersistentUltimateGauge = FMath::Clamp(CombatState.UltimateGauge, 0.0f, CombatState.UltimateMax);
	PersistentEquippedKeyElement = CombatState.EquippedKeyElement;
	bPersistentHarmonicKeyEquipped = CombatState.bHasHarmonicKeyEquipped;
}

bool UMelodiaBattleSession::ResolveRhythmExecutionResult(const FMelodiaRhythmExecutionResult& Result)
{
	UMelodiaCombatStateComponent* CombatState = GetCombatState();
	if (!CombatState)
	{
		return false;
	}

	if (Result.CommandType == EMelodiaRhythmCommandType::None)
	{
		return false;
	}

	if (Result.CommandType == EMelodiaRhythmCommandType::Skill
		&& Result.SkillCost > 0
		&& !CombatState->SpendSkillPoints(Result.SkillCost))
	{
		return false;
	}

	if (Result.CommandType == EMelodiaRhythmCommandType::Basic)
	{
		CombatState->AddSkillPoints(1);
	}

	UpdateSessionCombo(Result);

	const float SkillScalar = Result.CommandType == EMelodiaRhythmCommandType::Skill
		? FMath::Max(0.0f, Result.SkillScalar)
		: 1.0f;
	const float BaseDamage = CombatState->EvaluateModifier(
		EMelodiaModifierStat::Attack,
		25.0f * SkillScalar);
	const float Damage = BaseDamage * FMath::Max(0.0f, Result.AverageGradeMultiplier);
	const float ElementMult = UMelodiaKeySystemLibrary::GetElementDamageMultiplier(
		CombatState->EquippedKeyElement, CombatState->EnemyElement, CombatState->bHasHarmonicKeyEquipped);
	const float FinalDamage = Damage * ElementMult;
	const EMelodiaRhythmGrade RhythmGrade = MelodiaBattleSessionPrivate::GradeFromAverageMultiplier(Result.AverageGradeMultiplier);
	const FString CommandName = MelodiaBattleSessionPrivate::CommandDisplayName(Result.CommandType);
	if (ActiveBattleController && ActiveBattleController->GetWorld())
	{
		if (UMelodiaRhythmReactivitySubsystem* Reactivity = ActiveBattleController->GetWorld()->GetSubsystem<UMelodiaRhythmReactivitySubsystem>())
		{
			const float ComboNormalized = FMath::Clamp(static_cast<float>(SessionCombo) / 10.0f, 0.0f, 1.0f);
			const float CrescendoNormalized = FMath::Clamp(CombatState->UltimateGauge / FMath::Max(1.0f, CombatState->UltimateMax), 0.0f, 1.0f);
			Reactivity->NotifyCommandResolved(RhythmGrade, Result.AverageGradeMultiplier, ComboNormalized, CrescendoNormalized, static_cast<uint8>(CombatState->EnemyElement));
		}
	}

	// Apply elemental affliction on skill hit
	if (Result.CommandType == EMelodiaRhythmCommandType::Skill && Result.HitCount > 0)
	{
		FMelodiaSongSkillRecipe SkillRecipe;
		if (UMelodiaSongSkillLibrary::FindSongSkill(Result.SkillId, SkillRecipe))
		{
			CombatState->ApplyAffliction(SkillRecipe.Element);
		}
	}

	// Apply generated skill effects. Break effects wait until toughness damage
	// establishes whether this command actually broke the enemy.
	float EffectiveToughnessScalar = 1.0f;
	float BonusDamageOnBreak = 0.0f;
	float EnemyDelayOnBreakAvFraction = 0.0f;
	if (Result.CommandType == EMelodiaRhythmCommandType::Skill)
	{
		MelodiaRulesGen::FGeneratedSkillEffect Effect;
		if (MelodiaRulesGen::FindSkillEffect(Result.SkillId, Effect))
		{
			EffectiveToughnessScalar = FMath::Max(0.0f, Effect.ToughnessScalar);

			if (Result.PerfectCount > 0)
			{
				if (Effect.UltGainBonusOnPerfect > 0.0f)
				{
					CombatState->AddUltimateGauge(Effect.UltGainBonusOnPerfect);
				}
				if (Effect.SpGainOnPerfect > 0)
				{
					CombatState->AddSkillPoints(Effect.SpGainOnPerfect);
				}
				if (Effect.ModifierOnPerfect != nullptr)
				{
					MelodiaBattleSessionPrivate::ApplyGeneratedModifier(*CombatState, FName(Effect.ModifierOnPerfect));
				}
			}

			if (Result.HitCount > 0)
			{
				if (Effect.EnemyDelayOnHitAvFraction > 0.0f)
				{
					// GS-003: delay fractions are real AV push-back, not full-turn skips.
					PushBackEnemyAV(Effect.EnemyDelayOnHitAvFraction);
				}
				if (Effect.HealOnHitScalar > 0.0f)
				{
					const float HealAmount = FinalDamage * Effect.HealOnHitScalar;
					CombatState->PartyHP = FMath::Min(CombatState->PartyHP + HealAmount, CombatState->PartyMaxHP);
				}
				if (Effect.ModifierOnHit != nullptr)
				{
					MelodiaBattleSessionPrivate::ApplyGeneratedModifier(*CombatState, FName(Effect.ModifierOnHit));
				}
			}

			BonusDamageOnBreak = FMath::Max(0.0f, Effect.BonusDamageOnBreak);
			EnemyDelayOnBreakAvFraction = FMath::Max(0.0f, Effect.EnemyDelayOnBreakAvFraction);
		}
	}

	EnemyHP = FMath::Max(0.0f, EnemyHP - FinalDamage);
	NotifyEnemyHitPresentation(FinalDamage, RhythmGrade);
	const bool bBrokeNow = CombatState->ApplyEnemyToughnessDamage(FinalDamage * EffectiveToughnessScalar);
	float TotalDamage = FinalDamage;
	if (bBrokeNow)
	{
		if (ActiveBattleController && ActiveBattleController->GetWorld())
		{
			if (UMelodiaRhythmReactivitySubsystem* Reactivity = ActiveBattleController->GetWorld()->GetSubsystem<UMelodiaRhythmReactivitySubsystem>())
			{
				Reactivity->NotifyBreak();
			}
		}
		NotifyEnemyBrokenPresentation();
		if (BonusDamageOnBreak > 0.0f && CombatState->ConsumeBreakFollowUp(BonusDamageOnBreak))
		{
			EnemyHP = FMath::Max(0.0f, EnemyHP - BonusDamageOnBreak);
			TotalDamage += BonusDamageOnBreak;
		}
		if (EnemyDelayOnBreakAvFraction > 0.0f)
		{
			PushBackEnemyAV(EnemyDelayOnBreakAvFraction);
		}
		if (UMelodiaRhythmHUDWidget* HUD = UMelodiaRhythmHUDWidget::FindFirst(this))
		{
			HUD->SetBattlePhaseBanner(TEXT("BREAK!"));
			HUD->PushFloatingCombatText(TEXT("BREAK! Enemy weakened"), true, FLinearColor(1.0f, 0.72f, 0.24f, 1.0f));
			HUD->TriggerSparkleBurst();
		}
	}
	CombatState->AddUltimateGauge(static_cast<float>(UMelodiaCoreRulesLibrary::GetCrescendoGain(RhythmGrade)));
	CombatState->RecordCommandState(CommandName, TEXT("Attacking"), TotalDamage, CombatState->bUltimateReady, false);

	// Accumulate session score with combo bonus
	const float ComboBonus = 1.0f + static_cast<float>(SessionCombo) * MelodiaRulesGen::ComboBonusPerHit;
	SessionScore += TotalDamage * ComboBonus;
	LastBattleResults.DamageDealt += TotalDamage;

	if (UMelodiaRhythmHUDWidget* HUD = UMelodiaRhythmHUDWidget::FindFirst(this))
	{
		const FString GradeName = StaticEnum<EMelodiaRhythmGrade>()->GetDisplayNameTextByValue(static_cast<int64>(RhythmGrade)).ToString();
		const FString ResultText = FString::Printf(TEXT("%s %.0f"), *GradeName, TotalDamage);
		const FString StatusText = FString::Printf(
			TEXT("%s: %d/%d hits, %d miss | Combo %d | Enemy %.0f/%.0f HP | SP %d/%d | Ult %.0f%%"),
			*CommandName,
			Result.HitCount,
			Result.TotalNotes,
			Result.MissCount,
			SessionCombo,
			EnemyHP,
			EnemyMaxHP,
			CombatState->SkillPoints,
			CombatState->SkillPointMax,
			CombatState->UltimateGauge);

		HUD->SetJudgment(FText::FromString(GradeName));
		HUD->PushFloatingCombatText(ResultText, true, FLinearColor(0.98f, 0.82f, 0.38f, 1.0f));
		HUD->TriggerDamageFlash(TotalDamage);
		HUD->ShowBattleStatus(StatusText);
	}

	UE_LOG(LogTemp, Log, TEXT("Melodia: %s resolved! Grade=%s, Notes=%d/%d hits (%d miss), Damage=%.1f (element x%.2f), Enemy HP=%.0f/%.0f"),
		*CommandName,
		*StaticEnum<EMelodiaRhythmGrade>()->GetDisplayNameTextByValue(static_cast<int64>(RhythmGrade)).ToString(),
		Result.HitCount, Result.TotalNotes, Result.MissCount, TotalDamage, ElementMult, EnemyHP, EnemyMaxHP);

	const FName PresentationCommandId = Result.CommandType == EMelodiaRhythmCommandType::Skill
		? Result.SkillId
		: FName(TEXT("Basic"));
	NotifyPlayerCommandPresentation(PresentationCommandId, RhythmGrade);
	++CommandSubmitCount;
	return true;
}

bool UMelodiaBattleSession::SubmitBasicCommand()
{
	if (BattlePhase == EMelodiaBattlePhase::Victory)
	{
		return ConfirmVictoryReward();
	}

	if (!CanSubmitBasicCommand())
	{
		return false;
	}

	UMelodiaRhythmExecutionComponent* Execution = ActiveBattleController
		? ActiveBattleController->FindComponentByClass<UMelodiaRhythmExecutionComponent>()
		: nullptr;
	if (!Execution)
	{
		return false;
	}

	return Execution->BeginBasicExecution();
}

bool UMelodiaBattleSession::SubmitSkillCommand(const FName SkillId)
{
	if (BattlePhase == EMelodiaBattlePhase::Victory)
	{
		return ConfirmVictoryReward();
	}

	if (!CanSubmitSkillCommand(SkillId))
	{
		return false;
	}

	FMelodiaSongSkillRecipe Recipe;
	if (!UMelodiaSongSkillLibrary::FindSongSkill(SkillId, Recipe))
	{
		return false;
	}

	UMelodiaRhythmExecutionComponent* Execution = ActiveBattleController
		? ActiveBattleController->FindComponentByClass<UMelodiaRhythmExecutionComponent>()
		: nullptr;
	if (!Execution)
	{
		return false;
	}

	return Execution->BeginSkillExecutionById(SkillId);
}

bool UMelodiaBattleSession::SubmitUltimateCommand()
{
	if (!CanSubmitUltimateCommand())
	{
		return false;
	}

	UMelodiaCombatStateComponent* CombatState = GetCombatState();
	if (!CombatState)
	{
		return false;
	}

	// Snapshot damage now (gauge is consumed at activation); the hit lands
	// after a short camera/dilation beat so the ult actually reads.
	PendingUltimateDamage = 100.0f + CombatState->UltimateGauge * 2.0f;
	++CommandSubmitCount;

	if (AMelodiaBattleArena* Arena = Cast<AMelodiaBattleArena>(ActiveBattleController))
	{
		Arena->SetCameraPhase(EMelodiaArenaCameraPhase::Ult, 0.4f);
		Arena->SetTimeDilation(0.25f, 0.7f);
		Arena->PostProcessPop(1.0f);
		Arena->PlayShake(0.8f);
	}

	if (UMelodiaRhythmHUDWidget* HUD = UMelodiaRhythmHUDWidget::FindFirst(this))
	{
		HUD->DoPulse();
		HUD->TriggerSparkleBurst();
	}

	if (UWorld* World = GetWorld())
	{
		World->GetTimerManager().SetTimer(UltTimer, this,
			&UMelodiaBattleSession::ApplyUltimateDamage, 0.5f, false);
	}
	else
	{
		ApplyUltimateDamage();
	}
	return true;
}

void UMelodiaBattleSession::ApplyUltimateDamage()
{
	UMelodiaCombatStateComponent* CombatState = GetCombatState();
	if (!CombatState)
	{
		return;
	}

	EnemyHP = FMath::Max(0.0f, EnemyHP - PendingUltimateDamage);
	CombatState->RecordUltimateActivated(PendingUltimateDamage);

	UE_LOG(LogTemp, Log, TEXT("Melodia: ULTIMATE! Damage=%.1f, Enemy HP=%.0f/%.0f"),
		PendingUltimateDamage, EnemyHP, EnemyMaxHP);
	PendingUltimateDamage = 0.0f;

	if (CheckVictoryOrDefeat())
	{
		return;
	}

	// GS-004: ultimate is an AV interrupt — it costs no AV, so it never hands
	// the enemy a turn unless the enemy's AV was already due.
	++UltimateInterruptCount;
	RunEnemyAVCatchUp();

	// Return to command framing once the beat has played out.
	if (AMelodiaBattleArena* Arena = Cast<AMelodiaBattleArena>(ActiveBattleController))
	{
		Arena->SetCameraPhase(EMelodiaArenaCameraPhase::Command, 0.6f);
	}
}

bool UMelodiaBattleSession::SubmitFleeCommand()
{
	if (!CanSubmitFleeCommand())
	{
		return false;
	}

	++CommandSubmitCount;
	EndEncounter(EMelodiaEncounterResult::Fled);
	return true;
}

bool UMelodiaBattleSession::ConfirmVictoryReward()
{
	if (BattlePhase != EMelodiaBattlePhase::Victory)
	{
		return false;
	}

	// Grant rewards based on enemy defeated
	if (UMelodiaProgressionComponent* Progression = ActiveBattleController ? ActiveBattleController->FindComponentByClass<UMelodiaProgressionComponent>() : nullptr)
	{
		const int32 XPGained = FMath::RoundToInt(EnemyMaxHP * 0.5f) + SessionCombo * 2;
		const int32 CurrencyGained = FMath::RoundToInt(EnemyMaxHP * 0.1f) + FMath::Max(0, CommandSubmitCount - 1);

		Progression->AddXP(XPGained);
		Progression->AddCurrency(CurrencyGained);

		UE_LOG(LogTemp, Log, TEXT("Melodia: Victory rewards ΓÇö XP +%d, Currency +%d (Level %d, %d/%d XP)"),
			XPGained, CurrencyGained, Progression->Level, Progression->CurrentXP, Progression->XPToNextLevel);

		if (UMelodiaRhythmHUDWidget* HUD = UMelodiaRhythmHUDWidget::FindFirst(this))
		{
			HUD->ShowBattleStatus(FString::Printf(TEXT("Rewards: %d XP, %d C | Level %d"), XPGained, CurrencyGained, Progression->Level));
		}
	}

	EndEncounter(EMelodiaEncounterResult::Victory);
	return true;
}

float UMelodiaBattleSession::RestorePersistentPartyHealth(const float Amount)
{
	if (Amount <= 0.0f)
	{
		return 0.0f;
	}
	const float PreviousHP = PersistentPartyHP;
	PersistentPartyHP = FMath::Clamp(PersistentPartyHP + Amount, 0.0f, PersistentPartyMaxHP);
	const float Restored = PersistentPartyHP - PreviousHP;
	UE_LOG(LogTemp, Log, TEXT("Melodia: Heart Melody Token restored %.1f HP (%.1f/%.1f)."),
		Restored, PersistentPartyHP, PersistentPartyMaxHP);
	return Restored;
}

int32 UMelodiaBattleSession::RestorePersistentSkillPoints(const int32 Amount)
{
	if (Amount <= 0)
	{
		return 0;
	}
	const int32 PreviousSP = PersistentSkillPoints;
	PersistentSkillPoints = FMath::Clamp(PersistentSkillPoints + Amount, 0, PersistentSkillPointMax);
	const int32 Restored = PersistentSkillPoints - PreviousSP;
	UE_LOG(LogTemp, Log, TEXT("Melodia: Swirl Melody Token restored %d SP (%d/%d)."), Restored, PersistentSkillPoints, PersistentSkillPointMax);
	return Restored;
}

void UMelodiaBattleSession::RestorePersistentPartyState(const float HP, const float MaxHP, const int32 SkillPoints,
	const int32 SkillPointMax, const float UltimateGauge, const EMelodiaSpellElement KeyElement, const bool bHarmonicKeyEquipped)
{
	PersistentPartyMaxHP = FMath::Max(1.0f, MaxHP);
	PersistentPartyHP = FMath::Clamp(HP, 0.0f, PersistentPartyMaxHP);
	PersistentSkillPointMax = FMath::Max(1, SkillPointMax);
	PersistentSkillPoints = FMath::Clamp(SkillPoints, 0, PersistentSkillPointMax);
	PersistentUltimateGauge = FMath::Max(0.0f, UltimateGauge);
	PersistentEquippedKeyElement = KeyElement;
	bPersistentHarmonicKeyEquipped = bHarmonicKeyEquipped;
	bPersistentPartyStateInitialized = true;
	UE_LOG(LogTemp, Log, TEXT("Melodia: persistent party state restored from save (HP=%.1f/%.1f, SP=%d/%d, Ultimate=%.1f)."),
		PersistentPartyHP, PersistentPartyMaxHP, PersistentSkillPoints, PersistentSkillPointMax, PersistentUltimateGauge);
}

void UMelodiaBattleSession::ExecuteEnemyTurn()
{
	// Immediate path: phase + intent presentation + resolution in one call.
	SetBattlePhase(EMelodiaBattlePhase::EnemyTurn);
	NotifyEnemyIntentPresentation();
	if (ActiveBattleController && ActiveBattleController->GetWorld())
	{
		if (UMelodiaRhythmReactivitySubsystem* Reactivity = ActiveBattleController->GetWorld()->GetSubsystem<UMelodiaRhythmReactivitySubsystem>())
		{
			Reactivity->NotifyEnemyIntent(ComputeEncounterTension());
		}
	}
	ResolveEnemyAction();
}

void UMelodiaBattleSession::ResolveEnemyAction()
{
	UMelodiaCombatStateComponent* CombatState = GetCombatState();
	if (!CombatState)
	{
		return;
	}

	// Check delay stacks
	if (CombatState->EnemyTurnDelayStacks > 0)
	{
		CombatState->ConsumeEnemyTurnDelay();
		if (UMelodiaRhythmHUDWidget* HUD = UMelodiaRhythmHUDWidget::FindFirst(this))
		{
			HUD->PushFloatingCombatText(TEXT("Delayed"), true, FLinearColor(0.62f, 0.92f, 1.0f, 1.0f));
			HUD->ShowBattleStatus(FString::Printf(TEXT("Enemy turn delayed. %d delay stack(s) remain."), CombatState->EnemyTurnDelayStacks));
		}
		UE_LOG(LogTemp, Log, TEXT("Melodia: Enemy turn delayed (%d stacks remain)."), CombatState->EnemyTurnDelayStacks);
		return;
	}

	// Tick afflictions (Burn/Arcane DoT)
	const float AfflictionDotDamage = CombatState->GetAfflictionTickDamageTotal();
	if (AfflictionDotDamage > 0.0f)
	{
		EnemyHP = FMath::Max(0.0f, EnemyHP - AfflictionDotDamage);
		UE_LOG(LogTemp, Log, TEXT("Melodia: Affliction DoT %.1f damage. Enemy HP=%.0f/%.0f"),
			AfflictionDotDamage, EnemyHP, EnemyMaxHP);
		if (UMelodiaRhythmHUDWidget* HUD = UMelodiaRhythmHUDWidget::FindFirst(this))
		{
			HUD->PushFloatingCombatText(FString::Printf(TEXT("DoT %.0f"), AfflictionDotDamage), true, FLinearColor(1.0f, 0.5f, 0.0f, 1.0f));
		}
	}
	CombatState->TickAfflictions();
	CombatState->TickModifiers();
	if (CheckVictoryOrDefeat())
	{
		return;
	}

	// Enemy attacks
	const float BreakMultiplier = CombatState->bEnemyBroken
		? MelodiaRulesGen::ToughnessBrokenEnemyDamageMult
		: 1.0f;
	const float DamageMult = CombatState->EvaluateModifier(EMelodiaModifierStat::DamageTaken, BreakMultiplier);
	const float EnemyDamage = ActiveEnemyIntentDamage * DamageMult;
	CombatState->ApplyPartyDamage(EnemyDamage);
	// Feel: impact beat (hitstop + shake) on the presentation host.
	if (AMelodiaBattleArena* Arena = Cast<AMelodiaBattleArena>(ActiveBattleController))
	{
		Arena->Hitstop(0.10f, 0.06f);
		Arena->PlayShake(0.6f);
	}
	++CombatState->EnemyTurnCount;

	CombatState->RecordCommandState(TEXT("Enemy Attack"), ActiveEnemyIntentName.ToString(), EnemyDamage, false, false);

	if (UMelodiaRhythmHUDWidget* HUD = UMelodiaRhythmHUDWidget::FindFirst(this))
	{
		HUD->PushFloatingCombatText(FString::Printf(TEXT("-%.0f HP"), EnemyDamage), false, FLinearColor(0.96f, 0.28f, 0.42f, 1.0f));
		HUD->ShowBattleStatus(FString::Printf(TEXT("Enemy hits for %.0f. Party %.0f/%.0f HP."), EnemyDamage, CombatState->PartyHP, CombatState->PartyMaxHP));
	}

	UE_LOG(LogTemp, Log, TEXT("Melodia: Enemy attacks for %.1f damage. Party HP=%.0f/%.0f"),
		EnemyDamage, CombatState->PartyHP, CombatState->PartyMaxHP);
}

bool UMelodiaBattleSession::CheckVictoryOrDefeat()
{
	if (EnemyHP <= 0.0f)
	{
		const bool bNewVictory = BattlePhase != EMelodiaBattlePhase::Victory;
		SetBattlePhase(EMelodiaBattlePhase::Victory);

		// Show results in HUD
		float ScorePercent = 0.0f;
		const FText Rank = UMelodiaCoreRulesLibrary::GetRankFromScore(SessionScore, ScorePercent);
		const FLinearColor RankColor = UMelodiaCoreRulesLibrary::GetRankColor(SessionScore);

		UE_LOG(LogTemp, Log, TEXT("Melodia: Victory! Score=%.0f, Rank=%s, MaxCombo=%d"),
			SessionScore, *Rank.ToString(), SessionMaxCombo);

		if (UMelodiaRhythmHUDWidget* HUD = UMelodiaRhythmHUDWidget::FindFirst(this))
		{
			HUD->SetBattlePhaseBanner(FString::Printf(TEXT("VICTORY! Rank %s ΓÇö Score %.0f ΓÇö Combo %d"),
				*Rank.ToString(), SessionScore, SessionMaxCombo));
		}
		if (bNewVictory)
		{
			if (ActiveBattleController && ActiveBattleController->GetWorld())
			{
				if (UMelodiaRhythmReactivitySubsystem* Reactivity = ActiveBattleController->GetWorld()->GetSubsystem<UMelodiaRhythmReactivitySubsystem>())
				{
					Reactivity->NotifyVictory();
				}
			}
			NotifyEnemyDefeatedPresentation();
			NotifyPlayerVictoryPresentation();
		}

		return true;
	}

	const UMelodiaCombatStateComponent* CombatState = GetCombatState();
	if (CombatState && CombatState->PartyHP <= 0.0f)
	{
		// Enter the Defeat phase first so HUD mode, arena, and any listeners
		// see it; tear the encounter down after a short presentation hold.
		if (BattlePhase != EMelodiaBattlePhase::Defeat)
		{
			SetBattlePhase(EMelodiaBattlePhase::Defeat);
			if (UMelodiaRhythmHUDWidget* HUD = UMelodiaRhythmHUDWidget::FindFirst(this))
			{
				HUD->SetBattlePhaseBanner(TEXT("DEFEAT... the melody fades."));
			}
			NotifyPlayerDefeatPresentation();
			if (UWorld* World = GetWorld())
			{
				World->GetTimerManager().SetTimer(DefeatTimer, this,
					&UMelodiaBattleSession::FinishDefeat, 2.0f, false);
			}
			else
			{
				FinishDefeat();
			}
		}
		return true;
	}

	return false;
}

void UMelodiaBattleSession::FinishDefeat()
{
	EndEncounter(EMelodiaEncounterResult::Defeat);
}

// --- Internal ---

void UMelodiaBattleSession::SetBattlePhase(const EMelodiaBattlePhase NewPhase)
{
	if (BattlePhase == NewPhase)
	{
		return;
	}

	const EMelodiaBattlePhase PreviousPhase = BattlePhase;
	BattlePhase = NewPhase;
	++EncounterPhaseLogCount;
	LastEncounterPhaseLogEntry = FString::Printf(
		TEXT("%s -> %s"),
		*MelodiaBattleSessionPrivate::PhaseDisplayName(PreviousPhase),
		*MelodiaBattleSessionPrivate::PhaseDisplayName(NewPhase));
	UE_LOG(LogTemp, Log, TEXT("Melodia battle session phase: %s"), *LastEncounterPhaseLogEntry);
	OnBattlePhaseChanged.Broadcast(NewPhase, PreviousPhase);
	SyncHUDMode();
}

void UMelodiaBattleSession::SyncHUDMode()
{
	switch (BattlePhase)
	{
	case EMelodiaBattlePhase::AwaitingPlayerCommand:
	case EMelodiaBattlePhase::EnemyTurn:
		HUDMode = EMelodiaHUDMode::BattleCompact;
		break;
	case EMelodiaBattlePhase::RhythmExecution:
		HUDMode = EMelodiaHUDMode::BattleHighway;
		break;
	case EMelodiaBattlePhase::Victory:
		HUDMode = EMelodiaHUDMode::Victory;
		break;
	case EMelodiaBattlePhase::Defeat:
		HUDMode = EMelodiaHUDMode::Defeat;
		break;
	case EMelodiaBattlePhase::None:
	case EMelodiaBattlePhase::Fled:
	default:
		HUDMode = EMelodiaHUDMode::Exploration;
		break;
	}
}

void UMelodiaBattleSession::NotifyRhythmExecutionStarted()
{
	SetBattlePhase(EMelodiaBattlePhase::RhythmExecution);
}

void UMelodiaBattleSession::NotifyRhythmExecutionFinished(const FMelodiaRhythmExecutionResult& Result)
{
	if (!ResolveRhythmExecutionResult(Result))
	{
		SetBattlePhase(EMelodiaBattlePhase::AwaitingPlayerCommand);
		return;
	}

	if (CheckVictoryOrDefeat())
	{
		return;
	}

	// GS-003: charge the player's action, then let the enemy act only for as
	// long as its AV lags the player's. A fast player can act twice in a row.
	PlayerAV = UMelodiaCoreRulesLibrary::AddAVCost(PlayerAV, GetEffectivePlayerSpeed(), MelodiaRulesGen::BaseAV);
	RunEnemyAVCatchUp();
}

int32 UMelodiaBattleSession::GetEffectivePlayerSpeed() const
{
	const UMelodiaCombatStateComponent* CombatState = GetCombatState();
	const float Base = static_cast<float>(FMath::Max(1, PlayerBaseSpeed));
	const float Effective = CombatState
		? CombatState->EvaluateModifier(EMelodiaModifierStat::Speed, Base)
		: Base;
	return FMath::Max(1, FMath::RoundToInt(Effective));
}

bool UMelodiaBattleSession::ShouldEnemyActAgain(const int32 ActionsTaken) const
{
	// Exact condition of the original catch-up loop, incl. the 8-action soft-lock bound.
	constexpr int32 MaxEnemyActionsPerCatchUp = 8;
	return IsEncounterActive() && EnemyAV <= PlayerAV && ActionsTaken < MaxEnemyActionsPerCatchUp;
}

void UMelodiaBattleSession::RunEnemyAVCatchUp()
{
	UWorld* World = ActiveBattleController ? ActiveBattleController->GetWorld() : nullptr;
	if (bStageEnemyTurns && World && !bStagedSequenceRunning)
	{
		BeginStagedEnemyTurns();
		return;
	}
	if (bStagedSequenceRunning)
	{
		return; // sequence already pacing itself
	}

	// Immediate fallback: original loop, math untouched.
	int32 ActionsTaken = 0;
	while (ShouldEnemyActAgain(ActionsTaken))
	{
		ExecuteEnemyTurn();
		EnemyAV = UMelodiaCoreRulesLibrary::AddAVCost(EnemyAV, FMath::Max(1, EnemySpeed), MelodiaRulesGen::BaseAV);
		++ActionsTaken;
		if (CheckVictoryOrDefeat())
		{
			return;
		}
	}
	if (IsEncounterActive())
	{
		SetBattlePhase(EMelodiaBattlePhase::AwaitingPlayerCommand);
	}
}

void UMelodiaBattleSession::BeginStagedEnemyTurns()
{
	StagedActionsTaken = 0;
	bStagedSequenceRunning = true;
	StagedEnemyTelegraph();
}

void UMelodiaBattleSession::StagedEnemyTelegraph()
{
	if (!ShouldEnemyActAgain(StagedActionsTaken))
	{
		FinishStagedEnemyTurns();
		return;
	}

	SetBattlePhase(EMelodiaBattlePhase::EnemyTurn);
	NotifyEnemyIntentPresentation();
	UWorld* World = ActiveBattleController ? ActiveBattleController->GetWorld() : nullptr;
	if (World)
	{
		if (UMelodiaRhythmReactivitySubsystem* Reactivity = World->GetSubsystem<UMelodiaRhythmReactivitySubsystem>())
		{
			Reactivity->NotifyEnemyIntent(ComputeEncounterTension());
		}
		// Telegraph beat, then the attack-anim beat, then impact. Pacing subsystem
		// is optional polish (same degrade contract as MelodiaSirMelodiousIntroActor):
		// on a false return the authored staging durations are used unchanged.
		float TelegraphWindow = EnemyTelegraphDuration + EnemyAttackAnimDuration;
		if (UMelodiaPacingSubsystem* Pacing = UMelodiaPacingSubsystem::Get(this))
		{
			Pacing->ResolveDuration(TEXT("BattleEnemyTelegraphWindow"), TelegraphWindow);
		}
		World->GetTimerManager().SetTimer(EnemyStageTimer, this, &UMelodiaBattleSession::StagedEnemyImpact,
			FMath::Max(0.05f, TelegraphWindow), false);
	}
	else
	{
		StagedEnemyImpact();
	}
}

void UMelodiaBattleSession::StagedEnemyImpact()
{
	ResolveEnemyAction();
	EnemyAV = UMelodiaCoreRulesLibrary::AddAVCost(EnemyAV, FMath::Max(1, EnemySpeed), MelodiaRulesGen::BaseAV);
	++StagedActionsTaken;
	if (CheckVictoryOrDefeat())
	{
		bStagedSequenceRunning = false;
		return;
	}

	UWorld* World = ActiveBattleController ? ActiveBattleController->GetWorld() : nullptr;
	if (World)
	{
		float PostImpactWindow = EnemyPostImpactDuration;
		if (UMelodiaPacingSubsystem* Pacing = UMelodiaPacingSubsystem::Get(this))
		{
			Pacing->ResolveDuration(TEXT("BattleEnemyPostImpact"), PostImpactWindow);
		}
		World->GetTimerManager().SetTimer(EnemyStageTimer, this, &UMelodiaBattleSession::StagedEnemyTelegraph,
			FMath::Max(0.05f, PostImpactWindow), false);
	}
	else
	{
		StagedEnemyTelegraph();
	}
}

void UMelodiaBattleSession::FinishStagedEnemyTurns()
{
	bStagedSequenceRunning = false;
	if (IsEncounterActive())
	{
		SetBattlePhase(EMelodiaBattlePhase::AwaitingPlayerCommand);
	}
}

void UMelodiaBattleSession::PushBackEnemyAV(const float AvFraction)
{
	if (AvFraction <= 0.0f)
	{
		return;
	}
	const int32 EnemyActionCost = UMelodiaCoreRulesLibrary::CalculateAVCost(FMath::Max(1, EnemySpeed), MelodiaRulesGen::BaseAV);
	const int32 Delay = FMath::Max(1, FMath::RoundToInt(AvFraction * static_cast<float>(EnemyActionCost)));
	EnemyAV += Delay;
	UE_LOG(LogTemp, Log, TEXT("Melodia AV: enemy pushed back %d AV (%.0f%% of an action). PlayerAV=%d EnemyAV=%d"),
		Delay, AvFraction * 100.0f, PlayerAV, EnemyAV);
}

void UMelodiaBattleSession::EndEncounter(const EMelodiaEncounterResult Result)
{
	LastEncounterResult = Result;
	// Finalize the aggregated results summary for the results screen.
	LastBattleResults.Result = Result;
	LastBattleResults.Score = SessionScore;
	LastBattleResults.MaxCombo = SessionMaxCombo;
	{
		float ScorePercent = 0.0f;
		LastBattleResults.Rank = UMelodiaCoreRulesLibrary::GetRankFromScore(SessionScore, ScorePercent);
	}
	if (Result == EMelodiaEncounterResult::Victory)
	{
		if (UMelodiaOpeningFlowSubsystem* OpeningFlow = UMelodiaOpeningFlowSubsystem::Get(this))
		{
			if (OpeningFlow->NotifyZenEncounterVictory(ActiveEnemyId))
			{
				if (UMelodiaRoguelikeRunSubsystem* Run = UMelodiaRoguelikeRunSubsystem::Get(this))
				{
					Run->GrantHeartMelodyTokens(MelodiaRulesGen::OpeningHeartTokensOnUnlock);
				}
			}
		}
	}
	if (ActiveBattleController && ActiveBattleController->GetWorld())
	{
		if (UMelodiaRhythmReactivitySubsystem* Reactivity = ActiveBattleController->GetWorld()->GetSubsystem<UMelodiaRhythmReactivitySubsystem>())
		{
			Reactivity->ResetEncounter();
		}
	}
	UE_LOG(LogTemp, Log, TEXT("Melodia battle session: encounter ended (%s) after %d commands."),
		*StaticEnum<EMelodiaEncounterResult>()->GetDisplayNameTextByValue(static_cast<int64>(Result)).ToString(),
		CommandSubmitCount);

	// Clean up execution component
	if (UMelodiaCombatStateComponent* CombatState = GetCombatState())
	{
		StorePersistentPartyFromCombatState(*CombatState);
	}
	if (ActiveBattleController)
	{
		if (UMelodiaRhythmExecutionComponent* Execution = ActiveBattleController->FindComponentByClass<UMelodiaRhythmExecutionComponent>())
		{
			if (Execution->IsExecutionActive())
			{
				Execution->CancelExecution();
			}
		}
	}

	// Stop encounter BGM
	if (ActiveBattleController)
	{
		if (UMelodiaAudioComponent* Audio = ActiveBattleController->FindComponentByClass<UMelodiaAudioComponent>())
		{
			Audio->StopBGM();
		}
	}
	if (AMelodiaEncounterTrigger* Trigger = Cast<AMelodiaEncounterTrigger>(ActiveBattleController))
	{
		Trigger->SetEnemyPresentationVisible(false);
	}

	ActiveBattleController = nullptr;
	ActiveEncounter = FMelodiaEncounterDefinition();
	SetBattlePhase(EMelodiaBattlePhase::None);
	OnEncounterEnded.Broadcast(Result);
}
