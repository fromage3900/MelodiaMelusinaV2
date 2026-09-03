#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "MelodiaRhythmCombatTypes.h"
#include "MelodiaRhythmSkillDefinition.generated.h"

/**
 * The emotional niche a rhythm skill fills. Maps to an effect family:
 *   Sad      -> Debuff (enemy debuff)
 *   Calm     -> Heal + RemoveDebuff (ally recovery)
 *   Vigorous -> Damage + Crit (offense)
 */
UENUM(BlueprintType)
enum class EMelodiaRhythmNiche : uint8
{
	Sad			UMETA(DisplayName = "Sad"),
	Calm		UMETA(DisplayName = "Calm"),
	Vigorous	UMETA(DisplayName = "Vigorous")
};

/**
 * Grade multipliers for one effect family. Each skill row carries its own
 * balance so new skills are data, not code.
 */
USTRUCT(BlueprintType)
struct FMelodiaRhythmGradeMultipliers
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Rhythm Skill")
	float Miss = 0.70f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Rhythm Skill")
	float Good = 1.00f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Rhythm Skill")
	float Great = 1.20f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Rhythm Skill")
	float Perfect = 1.45f;

	float Get(EMelodiaSkillGrade Grade) const
	{
		switch (Grade)
		{
		case EMelodiaSkillGrade::Miss:    return Miss;
		case EMelodiaSkillGrade::Good:    return Good;
		case EMelodiaSkillGrade::Great:   return Great;
		case EMelodiaSkillGrade::Perfect: return Perfect;
		default:                           return 1.0f;
		}
	}
};

/**
 * Data-driven rhythm skill definition.
 *
 * New skills are authored as DataAsset rows -- no code changes required.
 * Each row carries its MIDI parameters, effect family, niche, base magnitude,
 * targeting, and per-grade multipliers.
 */
UCLASS(BlueprintType)
class BS_GODFILE_API UMelodiaRhythmSkillDefinition final : public UPrimaryDataAsset
{
	GENERATED_BODY()

public:
	/** Stable skill ID used by the rhythm combat subsystem and stock resolver. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Rhythm Skill")
	FName SkillId = NAME_None;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Rhythm Skill")
	FText DisplayName;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Rhythm Skill")
	FText Description;

	/** Emotional niche -> effect family. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Rhythm Skill")
	EMelodiaRhythmNiche Niche = EMelodiaRhythmNiche::Vigorous;

	/** Effect family requested through the stock resolver. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Rhythm Skill")
	EMelodiaRhythmEffectType EffectType = EMelodiaRhythmEffectType::Damage;

	// --- MIDI parameters (adjustable per skill) ---

	/** Tempo in BPM for the authored pattern. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Rhythm Skill|MIDI", meta = (ClampMin = "1.0"))
	float TempoBPM = 128.0f;

	/** Musical key (e.g. "C minor", "A major") for presentation/audio. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Rhythm Skill|MIDI")
	FString MusicalKey = TEXT("C minor");

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Rhythm Skill|MIDI", meta = (ClampMin = "1"))
	int32 TimeSignatureNumerator = 4;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Rhythm Skill|MIDI", meta = (ClampMin = "1"))
	int32 TimeSignatureDenominator = 4;

	/** Optional authored MIDI pattern asset (Harmonix UMidiFile). */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Rhythm Skill|MIDI")
	TSoftObjectPtr<UObject> PatternAsset;

	/** Notes per beat (1 = quarter, 2 = eighths, 4 = sixteenths). */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Rhythm Skill|MIDI", meta = (ClampMin = "1", ClampMax = "8"))
	int32 NoteDensity = 2;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Rhythm Skill|MIDI", meta = (ClampMin = "0"))
	int32 IntroBeats = 2;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Rhythm Skill|MIDI", meta = (ClampMin = "1"))
	int32 ActiveBeats = 4;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Rhythm Skill|MIDI", meta = (ClampMin = "0"))
	int32 OutroBeats = 1;

	// --- Effect parameters ---

	/** Base magnitude before the rhythm scalar (damage/heal/SP amount). */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Rhythm Skill|Effect")
	float BaseMagnitude = 1.0f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Rhythm Skill|Effect")
	FName TargetMode = TEXT("SingleEnemy");

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Rhythm Skill|Effect", meta = (ClampMin = "1"))
	int32 TargetCount = 1;

	/** Effect duration in seconds (debuffs, buffs, shields). */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Rhythm Skill|Effect")
	float Duration = 0.0f;

	/** SP cost to use the skill. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Rhythm Skill|Effect", meta = (ClampMin = "0"))
	int32 SPCost = 0;

	/** Bounded turn-order shift on strong grades. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Rhythm Skill|Effect", meta = (ClampMin = "0", ClampMax = "2"))
	int32 MaxTurnShift = 1;

	// --- Grade multipliers ---

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Rhythm Skill|Balance")
	FMelodiaRhythmGradeMultipliers DamageMultipliers;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Rhythm Skill|Balance")
	FMelodiaRhythmGradeMultipliers HealMultipliers;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Rhythm Skill|Balance")
	FMelodiaRhythmGradeMultipliers ResourceMultipliers;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Rhythm Skill|Balance")
	FMelodiaRhythmGradeMultipliers SpeedMultipliers;

	// --- Presentation theme ---

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Rhythm Skill|Presentation")
	FLinearColor LaneColor = FLinearColor::White;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Rhythm Skill|Presentation")
	FName CrestTheme = NAME_None;
};