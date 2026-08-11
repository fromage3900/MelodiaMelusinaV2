// Copyright Brennan Shepherd 2026 - Melodia Roguelike Dungeon Bridge
// Bridges ProceduralDungeon plugin with MelodiaCore battle system and GMM roguelike rules.

#pragma once

#include "CoreMinimal.h"
#include "RoguelikeRoomCustomData.generated.h"

class URoomData;
class AMelodiaEncounterTrigger;

/** Room type classification ΓÇö mirrors gmm.game.roguelike_dungeon.DungeonRoomType */
UENUM(BlueprintType)
enum class ERoguelikeRoomType : uint8
{
	Start		UMETA(DisplayName = "Start (Melodia Grove)"),
	Standard	UMETA(DisplayName = "Standard (Whispering Grove)"),
	Elite		UMETA(DisplayName = "Elite (Everburning Clearing)"),
	Boss		UMETA(DisplayName = "Boss (Boss Arena)"),
	Shop		UMETA(DisplayName = "Shop (Token Shrine)"),
	Treasure	UMETA(DisplayName = "Treasure (Abandoned Cache)"),
	Event		UMETA(DisplayName = "Event (Nikki Photo Spot)"),
	Blessing	UMETA(DisplayName = "Blessing (Altar Room)")
};

/** Infinity Nikki NPC archetype for room theming */
UENUM(BlueprintType)
enum class ENikkiNPCArchetype : uint8
{
	SakuraDreamer	UMETA(DisplayName = "Sakura Dreamer (Support/Healer)"),
	CosmicWeaver	UMETA(DisplayName = "Cosmic Weaver (Controller/Buffer)"),
	MirageDancer	UMETA(DisplayName = "Mirage Dancer (DPS/Evasion)"),
	None			UMETA(DisplayName = "None")
};

/** Nikki lighting preset for room atmosphere */
UENUM(BlueprintType)
enum class ENikkiLightingPreset : uint8
{
	Nikki		UMETA(DisplayName = "Nikki (Soft Dream)"),
	Jewelry		UMETA(DisplayName = "Jewelry (Glitter/Glam)"),
	Silhouette	UMETA(DisplayName = "Silhouette (Dramatic)"),
	None		UMETA(DisplayName = "None (Level Default)")
};

/**
 * RoomCustomData subclass that carries roguelike metadata through ProceduralDungeon.
 *
 * Attached to each URoomData asset. When ProceduralDungeon instantiates a room,
 * BP_RoguelikeDungeonGenerator reads this data to:
 *   - Configure EncounterTrigger actors with correct enemy pools
 *   - Apply Nikki-appropriate post-process and lighting presets
 *   - Spawn themed NPCs from the archetype library
 *   - Set up shop inventories / treasure drops / blessing altars
 *
 * Usage flow:
 *   URoomData > CustomData array > URoguelikeRoomCustomData
 *   ADungeonGenerator::OnRoomAdded ΓåÆ Read CustomData ΓåÆ configure room level
 */
UCLASS(BlueprintType, EditInlineNew, meta = (DisplayName = "Roguelike Room Custom Data"))
class MELODIACORE_API URoguelikeRoomCustomData : public UObject
{
	GENERATED_BODY()

public:
	// ---- Room Identity ----

	/** Room type for generation rules (floor gen picks based on this) */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Roguelike|Identity")
	ERoguelikeRoomType RoomType = ERoguelikeRoomType::Standard;

	/** Display name for UI (mini-map, HUD) */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Roguelike|Identity")
	FText DisplayName;

	/** Minimum floor for this room variant to appear */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Roguelike|Identity")
	int32 FloorTierMin = 1;

	/** Maximum floor for this room variant to appear */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Roguelike|Identity")
	int32 FloorTierMax = 99;

	// ---- Encounter Configuration ----

	/** Enemy IDs that can spawn in this room (maps to FMelodiaEnemyDef::EnemyId) */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Roguelike|Encounter")
	TArray<FName> EnemyPool;

	/** Whether this room is a one-shot encounter (cleared = gone) */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Roguelike|Encounter")
	bool bOneShot = true;

	/** Cooldown in seconds before encounter can re-trigger */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Roguelike|Encounter")
	float EncounterCooldownSeconds = 5.0f;

	/** Light color for encounter presentation */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Roguelike|Encounter")
	FLinearColor EncounterLightColor = FLinearColor(1.0f, 0.84f, 0.38f, 1.0f);

	// ---- Infinity Nikki Theme ----

	/** NPC archetype that determines room NPCs and visual theme */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Roguelike|Nikki Theme")
	ENikkiNPCArchetype NPCArchetype = ENikkiNPCArchetype::SakuraDreamer;

	/** Lighting preset for room atmosphere */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Roguelike|Nikki Theme")
	ENikkiLightingPreset LightingPreset = ENikkiLightingPreset::Nikki;

	/** Whether this room is marked as an Infinity Nikki photo spot */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Roguelike|Nikki Theme")
	bool bPhotoSpot = false;

	/** Mood descriptor (used for UI labeling, not gameplay) */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Roguelike|Nikki Theme")
	FString MoodDescriptor;

	// ---- Shop/Treasure Configuration ----

	/** Golden token cost to enter this room (for shop/treasure rooms) */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Roguelike|Economy")
	int32 GoldenTokenEntryCost = 0;

	/** Chance for bonus artifact drop (0.0 - 1.0)  */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Roguelike|Economy")
	float BonusArtifactDropChance = 0.0f;

	// ---- NPC Population ----

	/** NPC IDs to spawn in this room (from gmm.npc level_populator) */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Roguelike|NPCs")
	TArray<FName> NPCIds;

	/** Zone population reference for procedural NPC placement */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Roguelike|NPCs")
	FString PopulationReference;

public:
	/** Get the enemy pool as a formatted string array */
	UFUNCTION(BlueprintPure, Category = "Roguelike")
	TArray<FString> GetEnemyPoolAsString() const;

	/** Check if this room is valid for a given floor number */
	UFUNCTION(BlueprintPure, Category = "Roguelike")
	bool IsValidForFloor(int32 FloorNumber) const;

	/** Get the Nikki lighting preset as a string for level Blueprint */
	UFUNCTION(BlueprintPure, Category = "Roguelike")
	FString GetLightingPresetName() const;
};
