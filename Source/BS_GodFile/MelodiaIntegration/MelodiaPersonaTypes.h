#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "MelodiaPersonaTypes.generated.h"

class USoundBase;
class UTexture2D;

UENUM(BlueprintType)
enum class EMelodiaQuestState : uint8
{
	Locked,
	Available,
	Active,
	Completed
};

UENUM(BlueprintType)
enum class EMelodiaMinimapMarkerType : uint8
{
	Objective,
	NPC,
	Encounter,
	Exit,
	SavePoint
};

UENUM(BlueprintType)
enum class EMelodiaCompendiumCategory : uint8
{
	Character,
	MotifCreature,
	Instrument,
	Place,
	Phenomenon,
	Song,
	Relic
};

USTRUCT(BlueprintType)
struct BS_GODFILE_API FMelodiaAbilityDefinition
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadOnly)
	FName AbilityId;

	UPROPERTY(EditAnywhere, BlueprintReadOnly)
	FText DisplayName;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, meta=(MultiLine=true))
	FText Description;

	UPROPERTY(EditAnywhere, BlueprintReadOnly)
	FName StockSkillAssetId;

	UPROPERTY(EditAnywhere, BlueprintReadOnly)
	FName Element;

	UPROPERTY(EditAnywhere, BlueprintReadOnly)
	int32 MPCost = 0;

	UPROPERTY(EditAnywhere, BlueprintReadOnly)
	int32 UnlockLevel = 1;
};

USTRUCT(BlueprintType)
struct BS_GODFILE_API FMelodiaEquipmentDefinition
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadOnly)
	FName EquipmentId;

	UPROPERTY(EditAnywhere, BlueprintReadOnly)
	FText DisplayName;

	/**
	 * Legacy lookup key into the hardcoded StockEquipmentPaths table in
	 * MelodiaPersonaSubsystem.cpp. Adding equipment through this route requires a
	 * C++ edit and a rebuild, which does not scale past the three entries it has.
	 * Prefer StockItemClass below; this stays for already-authored content.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadOnly)
	FName StockItemAssetId;

	/**
	 * The stock equipment Blueprint this definition describes. Authoring-side, so a
	 * new piece of equipment is a data change rather than an engineering change.
	 * When set, this wins over StockItemAssetId.
	 *
	 * The stock item remains the mechanical authority (Decision 009/029c) -- this
	 * points AT it, it does not replace it.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadOnly)
	TSoftClassPtr<UObject> StockItemClass;

	UPROPERTY(EditAnywhere, BlueprintReadOnly)
	FName Slot;

	UPROPERTY(EditAnywhere, BlueprintReadOnly)
	int32 AttackBonus = 0;

	UPROPERTY(EditAnywhere, BlueprintReadOnly)
	int32 DefenseBonus = 0;

	UPROPERTY(EditAnywhere, BlueprintReadOnly)
	int32 MagicBonus = 0;

	UPROPERTY(EditAnywhere, BlueprintReadOnly)
	int32 SpeedBonus = 0;
};

USTRUCT(BlueprintType)
struct BS_GODFILE_API FMelodiaQuestDefinition
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadOnly)
	FName QuestId;

	UPROPERTY(EditAnywhere, BlueprintReadOnly)
	FName GiverNPCId;

	UPROPERTY(EditAnywhere, BlueprintReadOnly)
	FText DisplayName;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, meta=(MultiLine=true))
	FText Objective;

	UPROPERTY(EditAnywhere, BlueprintReadOnly)
	FName PrerequisiteQuestId;

	/** Optional Persona-lite stat gate. Empty means no social-stat requirement. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly)
	FName RequiredSocialStatId;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, meta=(ClampMin="0"))
	int32 RequiredSocialStatValue = 0;

	UPROPERTY(EditAnywhere, BlueprintReadOnly)
	FName CompletionFlagId;

	UPROPERTY(EditAnywhere, BlueprintReadOnly)
	FName RewardId;
};

USTRUCT(BlueprintType)
struct BS_GODFILE_API FMelodiaMinimapMarkerDefinition
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadOnly)
	FName MarkerId;

	UPROPERTY(EditAnywhere, BlueprintReadOnly)
	FName ActorTag;

	UPROPERTY(EditAnywhere, BlueprintReadOnly)
	FText Label;

	UPROPERTY(EditAnywhere, BlueprintReadOnly)
	EMelodiaMinimapMarkerType Type = EMelodiaMinimapMarkerType::Objective;

	UPROPERTY(EditAnywhere, BlueprintReadOnly)
	FName RequiredQuestId;
};

/**
 * Player-facing Compendium presentation data.
 *
 * This structure never owns gameplay truth. EntryId points at authored knowledge,
 * UnlockFlagId reads the canonical narrative record, and RelatedEntryIds link other
 * Compendium entries. The UI is free to present these fields without inventing a
 * second save, quest, creature, instrument, or world-state authority.
 */
USTRUCT(BlueprintType)
struct BS_GODFILE_API FMelodiaCompendiumEntry
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadOnly)
	FName EntryId;

	UPROPERTY(EditAnywhere, BlueprintReadOnly)
	EMelodiaCompendiumCategory Category = EMelodiaCompendiumCategory::Phenomenon;

	UPROPERTY(EditAnywhere, BlueprintReadOnly)
	FText DisplayName;

	UPROPERTY(EditAnywhere, BlueprintReadOnly)
	FText Subtitle;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, meta=(MultiLine=true))
	FText Summary;

	/** Optional musical identity: pitch, interval, mode, rhythmic cell, or motif description. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, meta=(MultiLine=true))
	FText MusicalIdentity;

	/** Melusina's authored marginalia. Keep this in character; it may be voiced. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, meta=(MultiLine=true))
	FText FieldNote;

	UPROPERTY(EditAnywhere, BlueprintReadOnly)
	TSoftObjectPtr<UTexture2D> Artwork;

	/** Optional spoken field note / performance snippet from the voicebank. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly)
	TSoftObjectPtr<USoundBase> VoiceNote;

	/** Empty = visible from the start. Otherwise reads this flag from the canonical narrative record. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly)
	FName UnlockFlagId;

	UPROPERTY(EditAnywhere, BlueprintReadOnly)
	TArray<FName> RelatedEntryIds;

	UPROPERTY(EditAnywhere, BlueprintReadOnly)
	TArray<FName> Tags;
};

UCLASS(BlueprintType)
class BS_GODFILE_API UMelodiaPersonaContent : public UDataAsset
{
	GENERATED_BODY()

public:
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Persona|Combat")
	TArray<FMelodiaAbilityDefinition> Abilities;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Persona|Equipment")
	TArray<FMelodiaEquipmentDefinition> Equipment;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Persona|Quests")
	TArray<FMelodiaQuestDefinition> Quests;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Persona|Minimap")
	TArray<FMelodiaMinimapMarkerDefinition> MinimapMarkers;

	/** Player-facing knowledge catalog. Runtime truth remains in the systems referenced by each entry. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Persona|Compendium")
	TArray<FMelodiaCompendiumEntry> Compendium;

	/**
	 * Allowlisted reward id -> EquipmentId that granting it should equip.
	 *
	 * Explicit rather than derived from a name convention: reward ids and
	 * equipment ids are authored independently (melodia_reward_tuning_fork vs
	 * melodia_tuning_fork), and a string transform would silently mis-resolve
	 * the moment either side is renamed. A reward with no entry here is a
	 * narrative-only reward -- it is still consumed exactly once, and
	 * UMelodiaPersonaSubsystem logs that nothing was equipped.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Persona|Equipment")
	TMap<FName, FName> RewardEquipment;
};