// Core deterministic combat and songcraft rules for Melodia.
// Ported from MelodiaMelusina_PROD to MelodiaCore plugin (UE 5.8).

#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "MelodiaSpellTypes.h"
#include "MelodiaCoreRulesLibrary.generated.h"

class URoomData;

UENUM(BlueprintType)
enum class EMelodiaRhythmGrade : uint8
{
	Miss UMETA(DisplayName="Miss"),
	Good UMETA(DisplayName="Good"),
	Great UMETA(DisplayName="Great"),
	Perfect UMETA(DisplayName="Perfect")
};

UENUM(BlueprintType)
enum class EMelodiaInstrument : uint8
{
	MusicBox UMETA(DisplayName="Music Box"),
	Violin UMETA(DisplayName="Violin"),
	Drums UMETA(DisplayName="Drums"),
	Harp UMETA(DisplayName="Harp"),
	Trumpet UMETA(DisplayName="Trumpet")
};

USTRUCT(BlueprintType)
struct FMelodiaRhythmWindows
{
	GENERATED_BODY()

	/** +/-90 ms ΓÇö canonical per FOUNDATION 4A. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Rhythm")
	float PerfectWindowMs = 90.0f;

	/** +/-120 ms ΓÇö intermediate tier between Perfect and Good. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Rhythm")
	float GreatWindowMs = 120.0f;

	/** +/-160 ms ΓÇö canonical per FOUNDATION 4A. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Rhythm")
	float GoodWindowMs = 160.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Rhythm")
	float LatencyOffsetMs = 0.0f;
};

USTRUCT(BlueprintType)
struct FMelodiaRhythmGradeResult
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Rhythm")
	EMelodiaRhythmGrade Grade = EMelodiaRhythmGrade::Miss;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Rhythm")
	float TimingErrorMs = 0.0f;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Rhythm")
	float RawMultiplier = 0.4f;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Rhythm")
	float CombatMultiplier = 0.4f;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Rhythm")
	bool bCountsAsHit = false;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Rhythm")
	FText DisplayText;
};

USTRUCT(BlueprintType)
struct FMelodiaSongMaterialInput
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Songcraft")
	FName MaterialId = NAME_None;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Songcraft", meta=(ClampMin="1", ClampMax="5"))
	int32 RarityTier = 1;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Songcraft")
	float PowerModifier = 1.0f;
};

USTRUCT(BlueprintType)
struct FMelodiaGeneratedSpell
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Songcraft")
	FName SpellId = NAME_None;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Songcraft")
	int32 CompositionHash = 0;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Songcraft")
	EMelodiaInstrument Instrument = EMelodiaInstrument::MusicBox;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Songcraft")
	EMelodiaSpellElement SpellElement = EMelodiaSpellElement::Forte;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Songcraft")
	int32 SPCost = 1;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Songcraft")
	float Power = 1.0f;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Songcraft")
	int32 HitCount = 1;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Songcraft")
	float SecondaryChance = 0.0f;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Songcraft")
	FText DebugSummary;
};

/**
 * Deterministic, side-effect-free rules used by Blueprint combat and songcraft.
 */
UCLASS()
class MELODIACORE_API UMelodiaCoreRulesLibrary : public UBlueprintFunctionLibrary
{
	GENERATED_BODY()

public:
	UFUNCTION(BlueprintPure, Category="Melodia|Rhythm")
	static FMelodiaRhythmGradeResult GradeInputFromBeatPosition(float BeatPosition, float BeatLengthSeconds, FMelodiaRhythmWindows Windows);

	UFUNCTION(BlueprintPure, Category="Melodia|Rhythm")
	static FMelodiaRhythmGradeResult GradeInputFromTimingErrorMs(float TimingErrorMs, FMelodiaRhythmWindows Windows);

	UFUNCTION(BlueprintPure, Category="Melodia|Rhythm")
	static float GetRhythmCombatMultiplier(EMelodiaRhythmGrade Grade, int32 ComboCount = 0, float ComboBonusPerHit = 0.05f);

	UFUNCTION(BlueprintPure, Category="Melodia|Rhythm")
	static float CalculateRhythmDamage(float BaseDamage, EMelodiaRhythmGrade Grade, int32 ComboCount = 0, float SkillScalar = 1.0f);

	UFUNCTION(BlueprintPure, Category="Melodia|Rhythm")
	static int32 GetCrescendoGain(EMelodiaRhythmGrade Grade);

	UFUNCTION(BlueprintPure, Category="Melodia|Rhythm")
	static int32 ApplyCrescendoGain(int32 CurrentCrescendo, EMelodiaRhythmGrade Grade, int32 MaxCrescendo = 100);

	UFUNCTION(BlueprintPure, Category="Melodia|Turn Economy")
	static int32 CalculateAVCost(int32 Speed, int32 BaseAV = 10000);

	UFUNCTION(BlueprintPure, Category="Melodia|Turn Economy")
	static int32 AddAVCost(int32 CurrentAV, int32 Speed, int32 BaseAV = 10000);

	UFUNCTION(BlueprintPure, Category="Melodia|Turn Economy")
	static int32 ApplySharedSPDelta(int32 CurrentSP, int32 Delta, int32 MaxSP = 5);

	UFUNCTION(BlueprintPure, Category="Melodia|Songcraft")
	static int32 MakeCompositionHash(const TArray<int32>& NotePitches, const TArray<float>& NoteDurations, EMelodiaInstrument Instrument, const TArray<FMelodiaSongMaterialInput>& Materials);

	UFUNCTION(BlueprintPure, Category="Melodia|Songcraft")
	static FMelodiaGeneratedSpell GenerateSpellFromSong(const TArray<int32>& NotePitches, const TArray<float>& NoteDurations, EMelodiaInstrument Instrument, const TArray<FMelodiaSongMaterialInput>& Materials);

	UFUNCTION(BlueprintPure, Category="Melodia|Songcraft")
	static float GetInstrumentPowerScalar(EMelodiaInstrument Instrument);

	UFUNCTION(BlueprintPure, Category="Melodia|Songcraft")
	static EMelodiaSpellElement DeriveSpellElementFromSong(const TArray<int32>& NotePitches, EMelodiaInstrument Instrument);

	UFUNCTION(BlueprintPure, Category="Melodia|Songcraft")
	static float CalculateElementalDamageMultiplier(EMelodiaSpellElement AttackElement, EMelodiaSpellElement DefenseElement, bool bHasMatchingKey);

	UFUNCTION(BlueprintPure, Category="Melodia|Songcraft")
	static FText GetElementDisplayName(EMelodiaSpellElement Element);

	UFUNCTION(BlueprintPure, Category="Melodia|Scoring")
	static FText GetRankFromScore(float Score, float &OutScorePercent);

	UFUNCTION(BlueprintPure, Category="Melodia|Scoring")
	static FLinearColor GetRankColor(float Score);

	/** Resolves a FMelodiaAuthoritativeStageRecipe::RoomDataId (e.g. "RD_MelodiaGrove_V1") to its
	 * URoomData asset under /Game/Melodia/Roguelike/RoomData/. Returns nullptr if not found. */
	UFUNCTION(BlueprintPure, Category="Melodia|Roguelike")
	static URoomData* ResolveRoomDataById(FName RoomDataId);
};
