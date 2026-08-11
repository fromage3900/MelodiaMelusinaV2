// Copyright Brennan Shepherd 2026 - Melodia Roguelike Dungeon Bridge
// Bridges ProceduralDungeon plugin with MelodiaCore battle system and GMM roguelike rules.
// Implementation file for URoguelikeRoomCustomData.

#include "RoguelikeRoomCustomData.h"
#include "Engine/World.h"

TArray<FString> URoguelikeRoomCustomData::GetEnemyPoolAsString() const
{
	TArray<FString> Result;
	for (const FName& EnemyId : EnemyPool)
	{
		Result.Add(EnemyId.ToString());
	}
	return Result;
}

bool URoguelikeRoomCustomData::IsValidForFloor(int32 FloorNumber) const
{
	return FloorNumber >= FloorTierMin && FloorNumber <= FloorTierMax;
}

FString URoguelikeRoomCustomData::GetLightingPresetName() const
{
	switch (LightingPreset)
	{
	case ENikkiLightingPreset::Nikki:
		return TEXT("Lights_Nikki");
	case ENikkiLightingPreset::Jewelry:
		return TEXT("Lights_Jewelry");
	case ENikkiLightingPreset::Silhouette:
		return TEXT("Lights_Silhouette");
	default:
		return TEXT("");
	}
}
