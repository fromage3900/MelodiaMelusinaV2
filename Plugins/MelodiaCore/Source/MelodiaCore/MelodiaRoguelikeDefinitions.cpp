#include "MelodiaRoguelikeDefinitions.h"

#include "RoomData.h"

FPrimaryAssetId UMelodiaRoguelikeDefinition::GetPrimaryAssetId() const
{
	return StableId.IsNone() ? Super::GetPrimaryAssetId() : FPrimaryAssetId(GetDefinitionType(), StableId);
}

bool UMelodiaRoguelikeDefinition::ValidateDefinition(TArray<FText>& OutErrors) const
{
	if (StableId.IsNone())
	{
		OutErrors.Add(FText::FromString(TEXT("StableId is required.")));
	}
	if (SchemaVersion <= 0)
	{
		OutErrors.Add(FText::FromString(TEXT("SchemaVersion must be positive.")));
	}
	if (bRequiresEntitlement && ContentPackId.IsNone())
	{
		OutErrors.Add(FText::FromString(TEXT("Entitlement-gated content requires ContentPackId.")));
	}
	return OutErrors.IsEmpty();
}

bool UMelodiaRoomDefinition::ValidateDefinition(TArray<FText>& OutErrors) const
{
	Super::ValidateDefinition(OutErrors);
	if (Level.IsNull()) OutErrors.Add(FText::FromString(TEXT("Room level is required.")));
	if (RoomData.IsNull()) OutErrors.Add(FText::FromString(TEXT("ProceduralDungeon RoomData is required.")));
	if (TopologyTags.IsEmpty()) OutErrors.Add(FText::FromString(TEXT("At least one topology tag is required.")));
	if (MinimumTier > MaximumTier) OutErrors.Add(FText::FromString(TEXT("MinimumTier exceeds MaximumTier.")));
	if (MinimumDissonance < 0.0f || MaximumDissonance > 100.0f || MinimumDissonance > MaximumDissonance)
	{
		OutErrors.Add(FText::FromString(TEXT("Dissonance range must be ordered within 0..100.")));
	}
	return OutErrors.IsEmpty();
}

bool UMelodiaRoguelikeEncounterDefinition::ValidateDefinition(TArray<FText>& OutErrors) const
{
	Super::ValidateDefinition(OutErrors);
	if (EnemyId.IsNone()) OutErrors.Add(FText::FromString(TEXT("EnemyId is required.")));
	if (EnemyClass.IsNull()) OutErrors.Add(FText::FromString(TEXT("EnemyClass is required.")));
	return OutErrors.IsEmpty();
}

bool UMelodiaRewardDefinition::ValidateDefinition(TArray<FText>& OutErrors) const
{
	Super::ValidateDefinition(OutErrors);
	if (Modifiers.IsEmpty()) OutErrors.Add(FText::FromString(TEXT("A reward must change at least one gameplay modifier.")));
	if (StackCap < 1) OutErrors.Add(FText::FromString(TEXT("StackCap must be at least one.")));
	if (Weight <= 0.0f) OutErrors.Add(FText::FromString(TEXT("Weight must be positive.")));
	return OutErrors.IsEmpty();
}

bool UMelodiaRewardPoolDefinition::ValidateDefinition(TArray<FText>& OutErrors) const
{
	Super::ValidateDefinition(OutErrors);
	if (Rewards.Num() < 3) OutErrors.Add(FText::FromString(TEXT("A reward pool requires at least three choices.")));
	for (const TSoftObjectPtr<UMelodiaRewardDefinition>& Reward : Rewards)
	{
		if (Reward.IsNull()) OutErrors.Add(FText::FromString(TEXT("Reward pool contains an empty reward reference.")));
	}
	return OutErrors.IsEmpty();
}

bool UMelodiaRunArchetypeDefinition::ValidateDefinition(TArray<FText>& OutErrors) const
{
	Super::ValidateDefinition(OutErrors);
	if (ActCount < 1 || StagesPerAct < 1) OutErrors.Add(FText::FromString(TEXT("Run requires at least one act and one stage per act.")));
	if (Rooms.IsEmpty()) OutErrors.Add(FText::FromString(TEXT("Run archetype requires rooms.")));
	if (Encounters.IsEmpty()) OutErrors.Add(FText::FromString(TEXT("Run archetype requires encounters.")));
	if (Difficulty.IsNull()) OutErrors.Add(FText::FromString(TEXT("Run archetype requires a difficulty definition.")));
	return OutErrors.IsEmpty();
}
