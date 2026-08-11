#pragma once

#include "CoreMinimal.h"
#include "MelodiaMusicClockSubsystem.h"
#include "MelodiaRhythmCombatTypes.generated.h"

/** Item-level effect type for rhythm skill execution requests. */
UENUM(BlueprintType)
enum class EMelodiaRhythmEffectType : uint8
{
	Damage			UMETA(DisplayName = "Damage"),
	Crit			UMETA(DisplayName = "Crit"),
	Heal			UMETA(DisplayName = "Heal"),
	RemoveDebuff	UMETA(DisplayName = "Remove Debuff"),
	Debuff			UMETA(DisplayName = "Debuff"),
	None			UMETA(DisplayName = "None")
};

/** Authoritative grade from the rhythm combat subsystem. */
UENUM(BlueprintType)
enum class EMelodiaSkillGrade : uint8
{
	Miss	UMETA(DisplayName = "Miss"),
	Good	UMETA(DisplayName = "Good"),
	Great	UMETA(DisplayName = "Great"),
	Perfect	UMETA(DisplayName = "Perfect")
};

/** Authoritative result of a rhythm skill execution, routed through the stock resolver. */
USTRUCT(BlueprintType)
struct FMelodiaAuthoritativeRhythmResult
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadOnly, Category = "Melodia|Rhythm")
	bool bValid = false;

	UPROPERTY(BlueprintReadOnly, Category = "Melodia|Rhythm")
	int32 SessionId = 0;

	UPROPERTY(BlueprintReadOnly, Category = "Melodia|Rhythm")
	EMelodiaSkillGrade Grade = EMelodiaSkillGrade::Miss;

	UPROPERTY(BlueprintReadOnly, Category = "Melodia|Rhythm")
	float PresentationScalar = 0.0f;

	UPROPERTY(BlueprintReadOnly, Category = "Melodia|Rhythm")
	int32 HitCount = 0;

	UPROPERTY(BlueprintReadOnly, Category = "Melodia|Rhythm")
	int32 MissCount = 0;

	UPROPERTY(BlueprintReadOnly, Category = "Melodia|Rhythm")
	int32 NoteCount = 0;

	UPROPERTY(BlueprintReadOnly, Category = "Melodia|Rhythm")
	float Accuracy = 0.0f;

	UPROPERTY(BlueprintReadOnly, Category = "Melodia|Rhythm")
	EMelodiaMusicClockSource ClockSource = EMelodiaMusicClockSource::None;
};

/** Effect request submitted by the rhythm combat subsystem to the stock resolver. */
USTRUCT(BlueprintType)
struct FMelodiaRhythmEffectRequest
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadOnly, Category = "Melodia|Rhythm")
	bool bConsumed = false;

	UPROPERTY(BlueprintReadOnly, Category = "Melodia|Rhythm")
	FName SkillId = NAME_None;

	UPROPERTY(BlueprintReadOnly, Category = "Melodia|Rhythm")
	int32 SessionId = 0;

	UPROPERTY(BlueprintReadOnly, Category = "Melodia|Rhythm")
	EMelodiaRhythmEffectType EffectType = EMelodiaRhythmEffectType::Damage;

	UPROPERTY(BlueprintReadOnly, Category = "Melodia|Rhythm")
	float BaseMagnitude = 1.0f;

	UPROPERTY(BlueprintReadOnly, Category = "Melodia|Rhythm")
	float RhythmScalar = 1.0f;

	UPROPERTY(BlueprintReadOnly, Category = "Melodia|Rhythm")
	FName TargetMode = NAME_None;

	UPROPERTY(BlueprintReadOnly, Category = "Melodia|Rhythm")
	int32 TargetCount = 1;

	UPROPERTY(BlueprintReadOnly, Category = "Melodia|Rhythm")
	float Duration = 0.0f;

	UPROPERTY(BlueprintReadOnly, Category = "Melodia|Rhythm")
	int32 TurnShift = 0;

	UPROPERTY(BlueprintReadOnly, Category = "Melodia|Rhythm")
	float Scalar = 1.0f;

	UPROPERTY(BlueprintReadOnly, Category = "Melodia|Rhythm")
	float Magnitude = 1.0f;

	UPROPERTY(BlueprintReadOnly, Category = "Melodia|Rhythm")
	FName TargetId = NAME_None;
};
