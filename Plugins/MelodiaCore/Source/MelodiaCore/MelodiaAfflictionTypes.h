#pragma once

#include "CoreMinimal.h"
#include "MelodiaSpellTypes.h"
#include "MelodiaAfflictionTypes.generated.h"

UENUM(BlueprintType)
enum class EMelodiaAffliction : uint8
{
	None    UMETA(DisplayName = "None"),
	Burn    UMETA(DisplayName = "Burn"),
	Petrify UMETA(DisplayName = "Petrify"),
	Shadow  UMETA(DisplayName = "Shadow"),
	Arcane  UMETA(DisplayName = "Arcane"),
	Purify  UMETA(DisplayName = "Purify"),
	Gust    UMETA(DisplayName = "Gust"),
	Soak    UMETA(DisplayName = "Soak")
};

UENUM(BlueprintType)
enum class EMelodiaModifierStat : uint8
{
	Attack      UMETA(DisplayName = "Attack"),
	Defense     UMETA(DisplayName = "Defense"),
	Speed       UMETA(DisplayName = "Speed"),
	RhythmWindow UMETA(DisplayName = "Rhythm Window"),
	SPGain      UMETA(DisplayName = "SP Gain"),
	UltGain     UMETA(DisplayName = "Ult Gain"),
	DamageTaken UMETA(DisplayName = "Damage Taken")
};

UENUM(BlueprintType)
enum class EMelodiaModifierOp : uint8
{
	Add UMETA(DisplayName = "Add"),
	Mul UMETA(DisplayName = "Multiply")
};

UENUM(BlueprintType)
enum class EMelodiaModifierStacking : uint8
{
	Stack   UMETA(DisplayName = "Stack"),
	Refresh UMETA(DisplayName = "Refresh"),
	Ignore  UMETA(DisplayName = "Ignore")
};

USTRUCT(BlueprintType)
struct MELODIACORE_API FMelodiaAfflictionEntry
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Afflictions")
	EMelodiaAffliction Affliction = EMelodiaAffliction::None;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Afflictions")
	int32 Stacks = 0;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Afflictions")
	int32 TurnsRemaining = 0;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Afflictions")
	EMelodiaSpellElement SourceElement = EMelodiaSpellElement::Forte;
};

USTRUCT(BlueprintType)
struct MELODIACORE_API FMelodiaModifierEntry
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Modifiers")
	FName ModifierId;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Modifiers")
	EMelodiaModifierStat Stat = EMelodiaModifierStat::Attack;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Modifiers")
	EMelodiaModifierOp Op = EMelodiaModifierOp::Mul;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Modifiers")
	float Value = 1.0f;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Modifiers")
	int32 DurationTurns = 0;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Modifiers")
	int32 Stacks = 1;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Modifiers")
	int32 MaxStacks = 1;
};

UENUM(BlueprintType)
enum class EMelodiaSkillEffectTag : uint8
{
	Opener    UMETA(DisplayName = "Opener"),
	Spark     UMETA(DisplayName = "Spark"),
	Breaker   UMETA(DisplayName = "Breaker"),
	Surge     UMETA(DisplayName = "Surge"),
	Tempo     UMETA(DisplayName = "Tempo"),
	Veil      UMETA(DisplayName = "Veil"),
	Guard     UMETA(DisplayName = "Guard"),
	Mend      UMETA(DisplayName = "Mend"),
	Sustain   UMETA(DisplayName = "Sustain")
};

namespace MelodiaAfflictionUtils
{
	MELODIACORE_API EMelodiaAffliction ElementToAffliction(EMelodiaSpellElement Element);

	MELODIACORE_API FName GetAfflictionDisplayName(EMelodiaAffliction Affliction);

	MELODIACORE_API int32 GetAfflictionMaxStacks(EMelodiaAffliction Affliction);

	MELODIACORE_API float GetAfflictionTickDamage(EMelodiaAffliction Affliction, int32 Stacks);
}
