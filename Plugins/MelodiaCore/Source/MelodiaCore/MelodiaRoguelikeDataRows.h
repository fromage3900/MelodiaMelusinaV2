// Row types for the roguelike DataTables that shipped as JSON-only or with UserDefinedStruct.
// Content/Melodia/DataStuctures/DT_{Burdens,Blessings,Artifacts,MelodiaTokens,RoguelikeRooms}.json
// are the source contracts. DT_Burdens was imported with a UserDefinedStruct (not FTableRowBase-
// derived native), the other four were never imported (no .uasset). A DataTable needs a native
// USTRUCT : FTableRowBase or it imports empty / with Generic row type, so these unblock that.
//
// Field names match JSON keys exactly (snake_case). UE's DataTable JSON importer matches on
// property name, so renaming to UE style would silently drop every column.

#pragma once

#include "CoreMinimal.h"
#include "Engine/DataTable.h"
#include "MelodiaRoguelikeDataRows.generated.h"

/** Roguelike burden/curse — paired with a blessing. Source: DT_Burdens.json */
USTRUCT(BlueprintType)
struct MELODIACORE_API FMelodiaRoguelikeBurdenRow : public FTableRowBase
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Roguelike")
	FString burden_id;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Roguelike")
	FString display_name;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Roguelike")
	FString description;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Roguelike")
	FString rule_type;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Roguelike")
	float magnitude = 0.f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Roguelike")
	FString duration_or_scope;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Roguelike")
	FString stack_policy;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Roguelike")
	FString source_content_pack;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Roguelike")
	FString paired_blessing_id;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Roguelike")
	FString source_row;
};

/** Roguelike blessing — source: DT_Blessings.json */
USTRUCT(BlueprintType)
struct MELODIACORE_API FMelodiaRoguelikeBlessingRow : public FTableRowBase
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Roguelike")
	FString blessing_id;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Roguelike")
	FString display_name;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Roguelike")
	FString description;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Roguelike")
	int32 token_cost = 0;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Roguelike")
	FString effect_type;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Roguelike")
	float effect_value = 0.f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Roguelike")
	FString effect_str;
};

/** Roguelike artifact — source: DT_Artifacts.json */
USTRUCT(BlueprintType)
struct MELODIACORE_API FMelodiaRoguelikeArtifactRow : public FTableRowBase
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Roguelike")
	FString artifact_id;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Roguelike")
	FString display_name;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Roguelike")
	FString description;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Roguelike")
	FString modifier_id;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Roguelike")
	int32 cost_golden_tokens = 0;
};

/** Token type — source: DT_MelodiaTokens.json (capitalised keys preserved) */
USTRUCT(BlueprintType)
struct MELODIACORE_API FMelodiaTokenTypeRow : public FTableRowBase
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Token")
	FString TokenID;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Token")
	FString DisplayName;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Token")
	FString Description;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Token")
	FString Element;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Token")
	int32 Value = 0;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Token")
	FString Rarity;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Token")
	FString TexturePath;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Token")
	FString MaterialPath;
};

/** Roguelike room — source: DT_RoguelikeRooms.json */
USTRUCT(BlueprintType)
struct MELODIACORE_API FMelodiaRoguelikeRoomRow : public FTableRowBase
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Roguelike")
	FString room_id;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Roguelike")
	FString display_name;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Roguelike")
	TArray<FString> enemy_pool;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Roguelike")
	float token_shrine_chance = 0.f;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Roguelike")
	bool is_boss_room = false;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Roguelike")
	bool is_shop_room = false;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Roguelike")
	bool is_treasure_room = false;
};
