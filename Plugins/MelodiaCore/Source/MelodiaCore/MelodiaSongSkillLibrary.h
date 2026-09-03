#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "MelodiaCoreRulesLibrary.h"
#include "MelodiaSpellTypes.h"
#include "MelodiaSongSkillLibrary.generated.h"

class UMelodiaSongDataAsset;

/** Explicit highway chart event ΓÇö preferred over pitch-only Index%4 lane assignment. */
USTRUCT(BlueprintType)
struct MELODIACORE_API FMelodiaChartNote
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Chart", meta = (ClampMin = "0.0"))
	float TargetBeat = 0.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Chart", meta = (ClampMin = "0", ClampMax = "3"))
	int32 LaneIndex = 0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Chart")
	int32 Pitch = 60;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Chart", meta = (ClampMin = "0.05"))
	float DurationBeats = 1.0f;
};

USTRUCT(BlueprintType)
struct MELODIACORE_API FMelodiaSongSkillRecipe
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Song Skill")
	FName SkillId = NAME_None;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Song Skill")
	FText DisplayName;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Song Skill")
	FText Description;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Song Skill")
	EMelodiaSpellElement Element = EMelodiaSpellElement::Forte;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Song Skill")
	EMelodiaInstrument Instrument = EMelodiaInstrument::MusicBox;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Song Skill", meta = (ClampMin = "1"))
	int32 MechanicLevelRequired = 1;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Song Skill")
	TArray<int32> NotePitches;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Song Skill")
	TArray<float> NoteDurations;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Song Skill")
	TArray<FMelodiaChartNote> ChartNotes;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Song Skill")
	TArray<FMelodiaSongMaterialInput> Materials;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Song Skill", meta = (ClampMin = "0", ClampMax = "5"))
	int32 SPCostOverride = 0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Song Skill")
	float PowerScalar = 1.0f;
};

UCLASS()
class MELODIACORE_API UMelodiaSongSkillLibrary : public UBlueprintFunctionLibrary
{
	GENERATED_BODY()

public:
	UFUNCTION(BlueprintPure, Category = "Melodia|Song Skills")
	static TArray<FMelodiaSongSkillRecipe> BuildDemoSongSkills();

	UFUNCTION(BlueprintCallable, Category = "Melodia|Song Skills")
	static void SetSongDataAsset(UMelodiaSongDataAsset* InAsset);

	UFUNCTION(BlueprintPure, Category = "Melodia|Song Skills")
	static UMelodiaSongDataAsset* GetSongDataAsset();

	UFUNCTION(BlueprintPure, Category = "Melodia|Song Skills")
	static bool FindSongSkill(FName SkillId, FMelodiaSongSkillRecipe& OutSkill);

	UFUNCTION(BlueprintPure, Category = "Melodia|Song Skills")
	static FName GetSkillIdForMechanicLevel(int32 MechanicLevel);

	UFUNCTION(BlueprintPure, Category = "Melodia|Song Skills")
	static TArray<FName> GetSkillIdsUnlockedAtOrBelowLevel(int32 MechanicLevel);

private:
	static TArray<FMelodiaSongSkillRecipe>& GetCachedSkills();
	static TMap<FName, FMelodiaSongSkillRecipe>& GetCachedSkillMap();
};
