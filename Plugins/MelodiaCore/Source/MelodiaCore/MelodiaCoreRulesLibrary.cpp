// Core deterministic combat and songcraft rules for Melodia.
// Ported from MelodiaMelusina_PROD to MelodiaCore plugin (UE 5.8).

#include "MelodiaCoreRulesLibrary.h"

#include "MelodiaKeySystemLibrary.h"
#include "MelodiaRulesGenerated.h"
#include "Misc/Crc.h"
#include "RoomData.h"

namespace MelodiaCoreRules
{
	// Values come from Plugins/MelodiaCore/Rules/melodia_rules.json via
	// MelodiaRulesGenerated.h ΓÇö edit the JSON + regenerate, never these.
	constexpr float MissMultiplier = MelodiaRulesGen::MissMultiplier;
	constexpr float GoodMultiplier = MelodiaRulesGen::GoodMultiplier;
	constexpr float GreatMultiplier = MelodiaRulesGen::GreatMultiplier;
	constexpr float PerfectMultiplier = MelodiaRulesGen::PerfectMultiplier;
	constexpr float MaxCombatMultiplier = MelodiaRulesGen::MaxCombatMultiplier;

	float GetRawMultiplier(const EMelodiaRhythmGrade Grade)
	{
		switch (Grade)
		{
		case EMelodiaRhythmGrade::Perfect:
			return PerfectMultiplier;
		case EMelodiaRhythmGrade::Great:
			return GreatMultiplier;
		case EMelodiaRhythmGrade::Good:
			return GoodMultiplier;
		case EMelodiaRhythmGrade::Miss:
		default:
			return MissMultiplier;
		}
	}

	FText GetGradeText(const EMelodiaRhythmGrade Grade)
	{
		switch (Grade)
		{
		case EMelodiaRhythmGrade::Perfect:
			return NSLOCTEXT("MelodiaRhythm", "PerfectGrade", "Perfect");
		case EMelodiaRhythmGrade::Great:
			return NSLOCTEXT("MelodiaRhythm", "GreatGrade", "Great");
		case EMelodiaRhythmGrade::Good:
			return NSLOCTEXT("MelodiaRhythm", "GoodGrade", "Good");
		case EMelodiaRhythmGrade::Miss:
		default:
			return NSLOCTEXT("MelodiaRhythm", "MissGrade", "Miss");
		}
	}

	void HashInt(uint32& Crc, const int32 Value)
	{
		Crc = FCrc::MemCrc32(&Value, sizeof(Value), Crc);
	}

	void HashFloatQuantized(uint32& Crc, const float Value)
	{
		const int32 Quantized = FMath::RoundToInt(Value * 1000.0f);
		HashInt(Crc, Quantized);
	}
}

FMelodiaRhythmGradeResult UMelodiaCoreRulesLibrary::GradeInputFromBeatPosition(const float BeatPosition, const float BeatLengthSeconds, const FMelodiaRhythmWindows Windows)
{
	if (BeatLengthSeconds <= KINDA_SMALL_NUMBER)
	{
		return GradeInputFromTimingErrorMs(FLT_MAX, Windows);
	}

	const float FractionalBeat = FMath::Frac(BeatPosition);
	const float WrappedPhase = FractionalBeat < 0.0f ? FractionalBeat + 1.0f : FractionalBeat;
	const float PhaseDistance = FMath::Min(WrappedPhase, 1.0f - WrappedPhase);
	const float TimingErrorMs = PhaseDistance * BeatLengthSeconds * 1000.0f;

	return GradeInputFromTimingErrorMs(TimingErrorMs, Windows);
}

FMelodiaRhythmGradeResult UMelodiaCoreRulesLibrary::GradeInputFromTimingErrorMs(const float TimingErrorMs, const FMelodiaRhythmWindows Windows)
{
	const float CorrectedErrorMs = FMath::Max(0.0f, FMath::Abs(TimingErrorMs - Windows.LatencyOffsetMs));

	EMelodiaRhythmGrade Grade = EMelodiaRhythmGrade::Miss;
	if (CorrectedErrorMs <= Windows.PerfectWindowMs)
	{
		Grade = EMelodiaRhythmGrade::Perfect;
	}
	else if (CorrectedErrorMs <= Windows.GreatWindowMs)
	{
		Grade = EMelodiaRhythmGrade::Great;
	}
	else if (CorrectedErrorMs <= Windows.GoodWindowMs)
	{
		Grade = EMelodiaRhythmGrade::Good;
	}

	FMelodiaRhythmGradeResult Result;
	Result.Grade = Grade;
	Result.TimingErrorMs = CorrectedErrorMs;
	Result.RawMultiplier = MelodiaCoreRules::GetRawMultiplier(Grade);
	Result.CombatMultiplier = GetRhythmCombatMultiplier(Grade);
	Result.bCountsAsHit = Grade != EMelodiaRhythmGrade::Miss;
	Result.DisplayText = MelodiaCoreRules::GetGradeText(Grade);

	return Result;
}

float UMelodiaCoreRulesLibrary::GetRhythmCombatMultiplier(const EMelodiaRhythmGrade Grade, const int32 ComboCount, const float ComboBonusPerHit)
{
	const float RawMultiplier = MelodiaCoreRules::GetRawMultiplier(Grade);
	const float ComboBonus = Grade == EMelodiaRhythmGrade::Miss ? 0.0f : FMath::Max(0, ComboCount) * FMath::Max(0.0f, ComboBonusPerHit);
	return FMath::Clamp(RawMultiplier + ComboBonus, MelodiaCoreRules::MissMultiplier, MelodiaCoreRules::MaxCombatMultiplier);
}

float UMelodiaCoreRulesLibrary::CalculateRhythmDamage(const float BaseDamage, const EMelodiaRhythmGrade Grade, const int32 ComboCount, const float SkillScalar)
{
	const float SanitizedBaseDamage = FMath::Max(0.0f, BaseDamage);
	const float SanitizedSkillScalar = FMath::Max(0.0f, SkillScalar);
	return SanitizedBaseDamage * SanitizedSkillScalar * GetRhythmCombatMultiplier(Grade, ComboCount);
}

int32 UMelodiaCoreRulesLibrary::GetCrescendoGain(const EMelodiaRhythmGrade Grade)
{
	switch (Grade)
	{
	case EMelodiaRhythmGrade::Perfect:
		return MelodiaRulesGen::CrescendoGainPerfect;
	case EMelodiaRhythmGrade::Great:
		return MelodiaRulesGen::CrescendoGainGreat;
	case EMelodiaRhythmGrade::Good:
		return MelodiaRulesGen::CrescendoGainGood;
	case EMelodiaRhythmGrade::Miss:
	default:
		return MelodiaRulesGen::CrescendoGainMiss;
	}
}

int32 UMelodiaCoreRulesLibrary::ApplyCrescendoGain(const int32 CurrentCrescendo, const EMelodiaRhythmGrade Grade, const int32 MaxCrescendo)
{
	const int32 SafeMax = FMath::Max(0, MaxCrescendo);
	return FMath::Clamp(CurrentCrescendo + GetCrescendoGain(Grade), 0, SafeMax);
}

int32 UMelodiaCoreRulesLibrary::CalculateAVCost(const int32 Speed, const int32 BaseAV)
{
	// Match GMM's continuous BaseAV / Speed ordering at integer precision.
	// Rounding 62.5 up to 63 breaks an exact 2:1 speed relationship.
	return FMath::Max(1, FMath::FloorToInt(
		static_cast<double>(FMath::Max(1, BaseAV)) /
		static_cast<double>(FMath::Max(1, Speed))));
}

int32 UMelodiaCoreRulesLibrary::AddAVCost(const int32 CurrentAV, const int32 Speed, const int32 BaseAV)
{
	return FMath::Max(0, CurrentAV) + CalculateAVCost(Speed, BaseAV);
}

int32 UMelodiaCoreRulesLibrary::ApplySharedSPDelta(const int32 CurrentSP, const int32 Delta, const int32 MaxSP)
{
	const int32 SafeMax = FMath::Max(0, MaxSP);
	return FMath::Clamp(CurrentSP + Delta, 0, SafeMax);
}

int32 UMelodiaCoreRulesLibrary::MakeCompositionHash(const TArray<int32>& NotePitches, const TArray<float>& NoteDurations, const EMelodiaInstrument Instrument, const TArray<FMelodiaSongMaterialInput>& Materials)
{
	uint32 Crc = 0;

	MelodiaCoreRules::HashInt(Crc, static_cast<int32>(Instrument));
	MelodiaCoreRules::HashInt(Crc, NotePitches.Num());
	MelodiaCoreRules::HashInt(Crc, NoteDurations.Num());

	for (const int32 Pitch : NotePitches)
	{
		MelodiaCoreRules::HashInt(Crc, Pitch);
	}

	for (const float Duration : NoteDurations)
	{
		MelodiaCoreRules::HashFloatQuantized(Crc, Duration);
	}

	for (const FMelodiaSongMaterialInput& Material : Materials)
	{
		const FString MaterialString = Material.MaterialId.ToString();
		Crc = FCrc::StrCrc32(*MaterialString, Crc);
		MelodiaCoreRules::HashInt(Crc, Material.RarityTier);
		MelodiaCoreRules::HashFloatQuantized(Crc, Material.PowerModifier);
	}

	return static_cast<int32>(Crc);
}

FMelodiaGeneratedSpell UMelodiaCoreRulesLibrary::GenerateSpellFromSong(const TArray<int32>& NotePitches, const TArray<float>& NoteDurations, const EMelodiaInstrument Instrument, const TArray<FMelodiaSongMaterialInput>& Materials)
{
	FMelodiaGeneratedSpell Spell;
	Spell.Instrument = Instrument;
	Spell.CompositionHash = MakeCompositionHash(NotePitches, NoteDurations, Instrument, Materials);
	Spell.SpellId = FName(*FString::Printf(TEXT("Spell_%08X"), static_cast<uint32>(Spell.CompositionHash)));
	Spell.SpellElement = DeriveSpellElementFromSong(NotePitches, Instrument);

	int32 ActiveNotes = 0;
	float DurationTotal = 0.0f;
	int32 PitchTotal = 0;
	for (int32 Index = 0; Index < NotePitches.Num(); ++Index)
	{
		const int32 Pitch = NotePitches[Index];
		const bool bIsRest = Pitch < 0;
		if (!bIsRest)
		{
			++ActiveNotes;
			PitchTotal += Pitch;
		}

		if (NoteDurations.IsValidIndex(Index))
		{
			DurationTotal += FMath::Max(0.0f, NoteDurations[Index]);
		}
	}

	float MaterialPower = 1.0f;
	int32 RarityTotal = 0;
	for (const FMelodiaSongMaterialInput& Material : Materials)
	{
		MaterialPower *= FMath::Max(0.1f, Material.PowerModifier);
		RarityTotal += FMath::Clamp(Material.RarityTier, 1, 5);
	}

	const int32 SafeActiveNotes = FMath::Max(1, ActiveNotes);
	const float AveragePitch = static_cast<float>(PitchTotal) / static_cast<float>(SafeActiveNotes);
	const float DurationScalar = FMath::Clamp(DurationTotal / 4.0f, 0.5f, 2.0f);
	const float PitchScalar = FMath::Clamp((AveragePitch - 48.0f) / 36.0f, 0.0f, 1.0f);
	const float RarityScalar = 1.0f + static_cast<float>(RarityTotal) * 0.05f;

	Spell.Power = FMath::RoundToFloat(100.0f * GetInstrumentPowerScalar(Instrument) * MaterialPower * RarityScalar * (0.8f + PitchScalar * 0.4f) / DurationScalar);
	Spell.HitCount = FMath::Clamp(1 + SafeActiveNotes / 4, 1, 4);
	Spell.SPCost = FMath::Clamp(1 + SafeActiveNotes / 5 + RarityTotal / 8, 1, 5);
	Spell.SecondaryChance = FMath::Clamp(0.05f + static_cast<float>(RarityTotal) * 0.03f, 0.05f, 0.65f);
	Spell.DebugSummary = FText::Format(
		NSLOCTEXT("MelodiaSongcraft", "GeneratedSpellSummary", "{0} [{1}]: Power {2}, Hits {3}, SP {4}"),
		FText::FromName(Spell.SpellId),
		GetElementDisplayName(Spell.SpellElement),
		FText::AsNumber(Spell.Power),
		FText::AsNumber(Spell.HitCount),
		FText::AsNumber(Spell.SPCost)
	);

	return Spell;
}

float UMelodiaCoreRulesLibrary::GetInstrumentPowerScalar(const EMelodiaInstrument Instrument)
{
	switch (Instrument)
	{
	case EMelodiaInstrument::Violin:
		return 0.9f;
	case EMelodiaInstrument::Drums:
		return 1.15f;
	case EMelodiaInstrument::Harp:
		return 1.0f;
	case EMelodiaInstrument::Trumpet:
		return 1.3f;
	case EMelodiaInstrument::MusicBox:
	default:
		return 1.0f;
	}
}

EMelodiaSpellElement UMelodiaCoreRulesLibrary::DeriveSpellElementFromSong(const TArray<int32>& NotePitches, const EMelodiaInstrument Instrument)
{
	int32 PitchTotal = 0;
	int32 ActiveNotes = 0;
	for (const int32 Pitch : NotePitches)
	{
		if (Pitch >= 0)
		{
			PitchTotal += Pitch;
			++ActiveNotes;
		}
	}

	const int32 SafeNotes = FMath::Max(1, ActiveNotes);
	const float AveragePitch = static_cast<float>(PitchTotal) / static_cast<float>(SafeNotes);
	const int32 InstrumentBias = static_cast<int32>(Instrument);
	const int32 ElementIndex = (FMath::RoundToInt(AveragePitch) + InstrumentBias * 2) % 7;
	return static_cast<EMelodiaSpellElement>(FMath::Clamp(ElementIndex, 0, 6));
}

float UMelodiaCoreRulesLibrary::CalculateElementalDamageMultiplier(const EMelodiaSpellElement AttackElement, const EMelodiaSpellElement DefenseElement, const bool bHasMatchingKey)
{
	return UMelodiaKeySystemLibrary::GetElementDamageMultiplier(AttackElement, DefenseElement, bHasMatchingKey);
}

FText UMelodiaCoreRulesLibrary::GetElementDisplayName(const EMelodiaSpellElement Element)
{
	switch (Element)
	{
	case EMelodiaSpellElement::Forte:   return NSLOCTEXT("MelodiaElement", "Forte", "Forte");
	case EMelodiaSpellElement::Tide:    return NSLOCTEXT("MelodiaElement", "Tide", "Tide");
	case EMelodiaSpellElement::Gale:    return NSLOCTEXT("MelodiaElement", "Gale", "Gale");
	case EMelodiaSpellElement::Stone:   return NSLOCTEXT("MelodiaElement", "Stone", "Stone");
	case EMelodiaSpellElement::Radiant: return NSLOCTEXT("MelodiaElement", "Radiant", "Radiant");
	case EMelodiaSpellElement::Umbral:  return NSLOCTEXT("MelodiaElement", "Umbral", "Umbral");
	case EMelodiaSpellElement::Arcane:
	default:                            return NSLOCTEXT("MelodiaElement", "Arcane", "Arcane");
	}
}

FText UMelodiaCoreRulesLibrary::GetRankFromScore(float Score, float& OutScorePercent)
{
	// Ranks based on score thresholds (enemy HP * golden target)
	constexpr float Threshold_S = 1000.0f;
	constexpr float Threshold_A = 700.0f;
	constexpr float Threshold_B = 450.0f;
	constexpr float Threshold_C = 250.0f;

	OutScorePercent = Score / FMath::Max(1.0f, Threshold_S);

	if (Score >= Threshold_S)
	{
		return NSLOCTEXT("MelodiaRank", "RankS", "S");
	}
	if (Score >= Threshold_A)
	{
		return NSLOCTEXT("MelodiaRank", "RankA", "A");
	}
	if (Score >= Threshold_B)
	{
		return NSLOCTEXT("MelodiaRank", "RankB", "B");
	}
	if (Score >= Threshold_C)
	{
		return NSLOCTEXT("MelodiaRank", "RankC", "C");
	}
	return NSLOCTEXT("MelodiaRank", "RankD", "D");
}

FLinearColor UMelodiaCoreRulesLibrary::GetRankColor(float Score)
{
	constexpr float Threshold_S = 1000.0f;
	constexpr float Threshold_A = 700.0f;
	constexpr float Threshold_B = 450.0f;
	constexpr float Threshold_C = 250.0f;

	if (Score >= Threshold_S) return FLinearColor(1.0f, 0.86f, 0.0f, 1.0f);   // Gold
	if (Score >= Threshold_A) return FLinearColor(0.62f, 0.92f, 1.0f, 1.0f);  // Cyan
	if (Score >= Threshold_B) return FLinearColor(0.42f, 1.0f, 0.72f, 1.0f);  // Mint
	if (Score >= Threshold_C) return FLinearColor(0.98f, 0.88f, 0.36f, 1.0f); // Gold
	return FLinearColor(0.96f, 0.28f, 0.42f, 1.0f);                            // Rose
}

URoomData* UMelodiaCoreRulesLibrary::ResolveRoomDataById(FName RoomDataId)
{
	if (RoomDataId.IsNone())
	{
		return nullptr;
	}

	const FString AssetName = RoomDataId.ToString();
	const FString AssetPath = FString::Printf(
		TEXT("/Game/Melodia/Roguelike/RoomData/%s.%s"), *AssetName, *AssetName);

	return LoadObject<URoomData>(nullptr, *AssetPath);
}
