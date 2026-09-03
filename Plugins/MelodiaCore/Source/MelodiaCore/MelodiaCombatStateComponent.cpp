// Native reactive combat state for Melodia battle actors.
// Ported from MelodiaMelusina_PROD to MelodiaCore plugin (UE 5.8).

#include "MelodiaCombatStateComponent.h"
#include "MelodiaRulesGenerated.h"

UMelodiaCombatStateComponent::UMelodiaCombatStateComponent()
{
	PrimaryComponentTick.bCanEverTick = false;
}

float UMelodiaCombatStateComponent::AddUltimateGauge(const float Delta)
{
	const float SafeMax = FMath::Max(1.0f, UltimateMax);
	UltimateMax = SafeMax;
	// GS-005: UltGain modifiers (e.g. ResonantFocus) now actually scale gauge gain.
	const float ScaledDelta = EvaluateModifier(EMelodiaModifierStat::UltGain, FMath::Max(0.0f, Delta));
	UltimateGauge = FMath::Clamp(UltimateGauge + FMath::Max(0.0f, ScaledDelta), 0.0f, SafeMax);
	bUltimateReady = UltimateGauge >= SafeMax;
	return UltimateGauge;
}

void UMelodiaCombatStateComponent::ResetUltimateGauge()
{
	UltimateGauge = 0.0f;
	LastUltimateDamage = 0.0f;
	UltimateActivationCount = 0;
	bUltimateReady = false;
}

void UMelodiaCombatStateComponent::RecordUltimateActivated(const float Damage)
{
	LastUltimateDamage = FMath::Max(0.0f, Damage);
	UltimateGauge = 0.0f;
	bUltimateReady = false;
	bUltimateUsedThisBattle = true;
	++UltimateActivationCount;
	++TotalUltimateActivationCount;
}

int32 UMelodiaCombatStateComponent::AddSkillPoints(const int32 Delta)
{
	const int32 SafeMax = FMath::Max(1, SkillPointMax);
	SkillPointMax = SafeMax;
	const int32 PreviousSkillPoints = FMath::Clamp(SkillPoints, 0, SafeMax);
	// GS-005: SPGain modifiers scale positive SP awards; losses (spend) are untouched.
	const int32 ScaledDelta = Delta > 0
		? FMath::RoundToInt(EvaluateModifier(EMelodiaModifierStat::SPGain, static_cast<float>(Delta)))
		: Delta;
	SkillPoints = FMath::Clamp(PreviousSkillPoints + ScaledDelta, 0, SafeMax);
	LastSkillPointDelta = SkillPoints - PreviousSkillPoints;
	if (Delta > 0)
	{
		++BasicActivationCount;
	}
	return SkillPoints;
}

bool UMelodiaCombatStateComponent::SpendSkillPoints(const int32 Cost)
{
	const int32 SafeCost = FMath::Max(0, Cost);
	const int32 SafeMax = FMath::Max(1, SkillPointMax);
	SkillPointMax = SafeMax;
	SkillPoints = FMath::Clamp(SkillPoints, 0, SafeMax);
	if (SkillPoints < SafeCost)
	{
		LastSkillPointDelta = 0;
		return false;
	}

	SkillPoints -= SafeCost;
	LastSkillPointDelta = -SafeCost;
	if (SafeCost > 0)
	{
		++SkillActivationCount;
	}
	return true;
}

bool UMelodiaCombatStateComponent::CanSpendSkillPoints(const int32 Cost) const
{
	return FMath::Clamp(SkillPoints, 0, FMath::Max(1, SkillPointMax)) >= FMath::Max(0, Cost);
}

void UMelodiaCombatStateComponent::ResetActionEconomy(const bool bResetPartyResources)
{
	SkillPointMax = FMath::Max(1, SkillPointMax);
	SkillPoints = bResetPartyResources
		? FMath::Clamp(MelodiaRulesGen::SharedSPStart, 0, SkillPointMax)
		: FMath::Clamp(SkillPoints, 0, SkillPointMax);
	LastSkillPointDelta = 0;
	BasicActivationCount = 0;
	SkillActivationCount = 0;
	CommandSequence = 0;
	ActiveTurnOrderIndex = 0;
	LastCommandName = TEXT("Battle Start");
	EnemyIntentName = TEXT("Waiting");
	EnemyIntentPower = 0.0f;
	bUltimateInterruptWindow = false;
	UltimateInterruptCount = 0;
	bBreakFollowUpAvailable = false;
	bBreakFollowUpConsumed = false;
	LastFollowUpBonusDamage = 0.0f;
	BreakFollowUpAvailableCount = 0;
	BreakFollowUpConsumedCount = 0;
	EnemyTurnDelayStacks = 0;
	LastEnemyTurnDelay = 0;
	EnemyTurnDelayApplyCount = 0;
	bUltimateUsedThisBattle = false;
	ClearAfflictions();
	ClearModifiers();
	ResetEnemyToughness(bResetPartyResources);
}

void UMelodiaCombatStateComponent::EquipHarmonicKey(const EMelodiaSpellElement NewKeyElement)
{
	EquippedKeyElement = NewKeyElement;
	bHasHarmonicKeyEquipped = true;
}

void UMelodiaCombatStateComponent::RecordCommandState(const FString& CommandName, const FString& IntentName, const float IntentPower, const bool bUltimateWindow, const bool bUltimateInterrupt)
{
	LastCommandName = CommandName.IsEmpty() ? TEXT("Command") : CommandName;
	EnemyIntentName = IntentName.IsEmpty() ? TEXT("Waiting") : IntentName;
	EnemyIntentPower = FMath::Max(0.0f, IntentPower);
	bUltimateInterruptWindow = bUltimateWindow;
	++CommandSequence;
	ActiveTurnOrderIndex = EnemyTurnDelayStacks > 0 ? 0 : CommandSequence % 4;
	if (bUltimateInterrupt)
	{
		++UltimateInterruptCount;
	}
}

bool UMelodiaCombatStateComponent::ApplyEnemyToughnessDamage(const float Damage)
{
	const float SafeMax = FMath::Max(1.0f, EnemyToughnessMax);
	EnemyToughnessMax = SafeMax;
	const float PreviousToughness = FMath::Clamp(EnemyToughness, 0.0f, SafeMax);
	const bool bWasBroken = PreviousToughness <= 0.0f || bEnemyBroken;
	LastToughnessDamage = FMath::Max(0.0f, Damage) * MelodiaRulesGen::ToughnessReduction;
	EnemyToughness = FMath::Clamp(PreviousToughness - LastToughnessDamage, 0.0f, SafeMax);
	bEnemyBroken = EnemyToughness <= 0.0f;

	if (bEnemyBroken && !bWasBroken)
	{
		++EnemyBreakCount;
		++TotalEnemyBreakCount;
		OpenBreakFollowUpWindow();
		return true;
	}

	return false;
}

void UMelodiaCombatStateComponent::OpenBreakFollowUpWindow()
{
	bBreakFollowUpAvailable = true;
	bBreakFollowUpConsumed = false;
	LastFollowUpBonusDamage = 0.0f;
	++BreakFollowUpAvailableCount;
}

bool UMelodiaCombatStateComponent::ConsumeBreakFollowUp(const float BonusDamage)
{
	if (!bBreakFollowUpAvailable || bBreakFollowUpConsumed)
	{
		LastFollowUpBonusDamage = 0.0f;
		return false;
	}

	bBreakFollowUpAvailable = false;
	bBreakFollowUpConsumed = true;
	LastFollowUpBonusDamage = FMath::Max(0.0f, BonusDamage);
	++BreakFollowUpConsumedCount;
	++TotalBreakFollowUpConsumedCount;
	return true;
}

int32 UMelodiaCombatStateComponent::ApplyEnemyTurnDelay(const int32 DelayAmount)
{
	const int32 SafeDelay = FMath::Clamp(DelayAmount, 0, 4);
	LastEnemyTurnDelay = SafeDelay;
	if (SafeDelay <= 0)
	{
		return EnemyTurnDelayStacks;
	}

	EnemyTurnDelayStacks = FMath::Clamp(EnemyTurnDelayStacks + SafeDelay, 0, 6);
	++EnemyTurnDelayApplyCount;
	++TotalEnemyTurnDelayApplyCount;
	return EnemyTurnDelayStacks;
}

int32 UMelodiaCombatStateComponent::ConsumeEnemyTurnDelay()
{
	if (EnemyTurnDelayStacks > 0)
	{
		--EnemyTurnDelayStacks;
	}
	return EnemyTurnDelayStacks;
}

void UMelodiaCombatStateComponent::ResetEnemyToughness(const bool bResetPartyHP)
{
	EnemyToughnessMax = FMath::Max(1.0f, EnemyToughnessMax);
	EnemyToughness = EnemyToughnessMax;
	LastToughnessDamage = 0.0f;
	bEnemyBroken = false;
	EnemyBreakCount = 0;
	bBreakFollowUpAvailable = false;
	bBreakFollowUpConsumed = false;
	LastFollowUpBonusDamage = 0.0f;
	EnemyTurnDelayStacks = 0;
	LastEnemyTurnDelay = 0;
	if (bResetPartyHP)
	{
		PartyHP = PartyMaxHP;
	}
	LastPartyDamageTaken = 0.0f;
	EnemyTurnCount = 0;
}

float UMelodiaCombatStateComponent::ApplyPartyDamage(const float Damage)
{
	const float SafeDamage = FMath::Max(0.0f, Damage);
	LastPartyDamageTaken = SafeDamage;
	PartyMaxHP = FMath::Max(1.0f, PartyMaxHP);
	PartyHP = FMath::Max(0.0f, PartyHP - SafeDamage);
	return LastPartyDamageTaken;
}

// --- Afflictions ---

void UMelodiaCombatStateComponent::ApplyAffliction(EMelodiaSpellElement Element)
{
	const EMelodiaAffliction Affliction = MelodiaAfflictionUtils::ElementToAffliction(Element);
	if (Affliction == EMelodiaAffliction::None)
	{
		return;
	}

	const int32 MaxStacks = MelodiaAfflictionUtils::GetAfflictionMaxStacks(Affliction);

	for (FMelodiaAfflictionEntry& Entry : ActiveAfflictions)
	{
		if (Entry.Affliction == Affliction)
		{
			Entry.Stacks = FMath::Min(Entry.Stacks + 1, MaxStacks);
			Entry.TurnsRemaining = FMath::Max(Entry.TurnsRemaining, 3);
			return;
		}
	}

	FMelodiaAfflictionEntry NewEntry;
	NewEntry.Affliction = Affliction;
	NewEntry.Stacks = 1;
	NewEntry.TurnsRemaining = 3;
	NewEntry.SourceElement = Element;
	ActiveAfflictions.Add(NewEntry);
}

void UMelodiaCombatStateComponent::TickAfflictions()
{
	for (int32 i = ActiveAfflictions.Num() - 1; i >= 0; --i)
	{
		FMelodiaAfflictionEntry& Entry = ActiveAfflictions[i];
		Entry.TurnsRemaining--;

		if (Entry.TurnsRemaining <= 0)
		{
			ActiveAfflictions.RemoveAt(i);
		}
	}
}

void UMelodiaCombatStateComponent::ClearAfflictions()
{
	ActiveAfflictions.Empty();
}

float UMelodiaCombatStateComponent::GetAfflictionTickDamageTotal() const
{
	float Total = 0.0f;
	for (const FMelodiaAfflictionEntry& Entry : ActiveAfflictions)
	{
		Total += MelodiaAfflictionUtils::GetAfflictionTickDamage(Entry.Affliction, Entry.Stacks);
	}
	return Total;
}

// --- Modifiers ---

void UMelodiaCombatStateComponent::ApplyModifier(FName ModifierId, EMelodiaModifierStat Stat, EMelodiaModifierOp Op, float Value, int32 DurationTurns, EMelodiaModifierStacking Stacking, int32 MaxStacks)
{
	for (FMelodiaModifierEntry& Entry : ActiveModifiers)
	{
		if (Entry.ModifierId == ModifierId)
		{
			if (Stacking == EMelodiaModifierStacking::Refresh)
			{
				Entry.DurationTurns = FMath::Max(Entry.DurationTurns, DurationTurns);
			}
			else if (Stacking == EMelodiaModifierStacking::Stack)
			{
				Entry.Stacks = FMath::Min(Entry.Stacks + 1, MaxStacks);
				Entry.DurationTurns = FMath::Max(Entry.DurationTurns, DurationTurns);
			}
			return;
		}
	}

	FMelodiaModifierEntry NewEntry;
	NewEntry.ModifierId = ModifierId;
	NewEntry.Stat = Stat;
	NewEntry.Op = Op;
	NewEntry.Value = Value;
	NewEntry.DurationTurns = DurationTurns;
	NewEntry.Stacks = 1;
	NewEntry.MaxStacks = MaxStacks;
	ActiveModifiers.Add(NewEntry);
}

void UMelodiaCombatStateComponent::TickModifiers()
{
	for (int32 i = ActiveModifiers.Num() - 1; i >= 0; --i)
	{
		ActiveModifiers[i].DurationTurns--;
		if (ActiveModifiers[i].DurationTurns == 0)
		{
			ActiveModifiers.RemoveAt(i);
		}
	}
}

float UMelodiaCombatStateComponent::EvaluateModifier(EMelodiaModifierStat Stat, float BaseValue) const
{
	float Additive = 0.0f;
	float Multiplicative = 1.0f;

	for (const FMelodiaModifierEntry& Entry : ActiveModifiers)
	{
		if (Entry.Stat != Stat)
		{
			continue;
		}

		const float EffectiveValue = Entry.Op == EMelodiaModifierOp::Add
			? Entry.Value * static_cast<float>(Entry.Stacks)
			: FMath::Pow(Entry.Value, static_cast<float>(Entry.Stacks));

		if (Entry.Op == EMelodiaModifierOp::Add)
		{
			Additive += EffectiveValue;
		}
		else
		{
			Multiplicative *= EffectiveValue;
		}
	}

	return (BaseValue + Additive) * Multiplicative;
}

void UMelodiaCombatStateComponent::ClearModifiers()
{
	ActiveModifiers.Empty();
}
