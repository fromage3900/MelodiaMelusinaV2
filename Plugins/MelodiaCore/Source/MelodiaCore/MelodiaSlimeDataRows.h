// Row types for the Melody Slime DataTables.
//
// Content/Melodia/DataStuctures/DT_MelodySlime_{Enemies,Skills,RoomMods}.json hold
// 48 enemy variants across 7 elements, 24 skills and 21 room mods, authored
// 2026-08-11 and never imported -- no DT_MelodySlime*.uasset existed anywhere in
// Content. A DataTable needs a matching USTRUCT row type or it imports empty, so
// these exist to unblock that import.
//
// Field names deliberately match the JSON keys exactly (snake_case). UE's DataTable
// JSON importer matches on property name, so renaming these to UE style would
// silently drop every column.

#pragma once

#include "CoreMinimal.h"
#include "Engine/DataTable.h"
#include "MelodiaSlimeDataRows.generated.h"

/** One Melody Slime enemy variant. Data only -- battle authority stays in the stock JRPG systems. */
USTRUCT(BlueprintType)
struct MELODIACORE_API FMelodiaSlimeEnemyRow : public FTableRowBase
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Slime")
	FString enemy_id;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Slime")
	FString display_name;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Slime")
	float max_hp = 0.f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Slime")
	float max_toughness = 0.f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Slime")
	float base_damage = 0.f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Slime")
	int32 speed = 0;

	/** Forte, Tide, Gale, Arcane, Radiant, Umbral, Stone. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Slime")
	FString element;

	/** Drives rhythm pacing for this variant. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Slime")
	float bpm = 0.f;
};

/** A rhythm skill chart. note_pitches and note_durations are parallel arrays. */
USTRUCT(BlueprintType)
struct MELODIACORE_API FMelodiaSlimeSkillRow : public FTableRowBase
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Slime|Skill")
	FString skill_id;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Slime|Skill")
	FString display_name;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Slime|Skill")
	FString element;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Slime|Skill")
	FString instrument;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Slime|Skill")
	int32 mechanic_level = 0;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Slime|Skill")
	int32 sp_cost = 0;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Slime|Skill")
	float power_scalar = 1.f;

	/** MIDI note numbers. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Slime|Skill")
	TArray<int32> note_pitches;

	/** Beat durations, parallel to note_pitches. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Slime|Skill")
	TArray<float> note_durations;
};

/** A run modifier: paired blessing and curse. */
USTRUCT(BlueprintType)
struct MELODIACORE_API FMelodiaSlimeRoomModRow : public FTableRowBase
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Slime|RoomMod")
	FString blessing_id;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Slime|RoomMod")
	FString display_name;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Slime|RoomMod")
	FString description;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Slime|RoomMod")
	int32 token_cost = 0;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Slime|RoomMod")
	FString effect_type;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Slime|RoomMod")
	float effect_value = 0.f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Slime|RoomMod")
	FString effect_str;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Slime|RoomMod")
	FString curse;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Slime|RoomMod")
	FString curse_effect;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Slime|RoomMod")
	FString flavor;
};
