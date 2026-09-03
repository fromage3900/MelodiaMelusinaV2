// Data-driven enemy definitions.

#include "MelodiaEnemyDefinition.h"

bool UMelodiaEnemyDataAsset::FindEnemyById(const FName EnemyId, FMelodiaEnemyDef& OutEnemy) const
{
	for (const FMelodiaEnemyDef& Enemy : Enemies)
	{
		if (Enemy.EnemyId == EnemyId)
		{
			OutEnemy = Enemy;
			return true;
		}
	}
	return false;
}

FMelodiaEnemyDef UMelodiaEnemyDataAsset::GetEnemyByIndex(const int32 Index) const
{
	if (Enemies.IsValidIndex(Index))
	{
		return Enemies[Index];
	}
	return FMelodiaEnemyDef();
}

TArray<FMelodiaEnemyDef> UMelodiaEnemyDataAsset::GetDemoEnemies()
{
	TArray<FMelodiaEnemyDef> DemoEnemies;

	// Crystal Shard ΓÇö easy encounter, Forte element, low HP
	{
		FMelodiaEnemyDef Enemy;
		Enemy.EnemyId = FName(TEXT("CrystalShard"));
		Enemy.DisplayName = FText::FromString(TEXT("Crystal Shard"));
		Enemy.MaxHP = 80.0f;
		Enemy.MaxToughness = 22.0f;
		Enemy.BaseDamage = 7.0f;
		Enemy.Speed = 60;
		Enemy.PrimaryIntentName = FText::FromString(TEXT("Resonance Ping"));
		Enemy.PrimaryIntentDamageMultiplier = 0.9f;
		Enemy.Element = EMelodiaSpellElement::Forte;
		Enemy.MeshScale = 0.8f;
		Enemy.BPMOverride = 120.0f;
		DemoEnemies.Add(Enemy);
	}

	// Stone Golem ΓÇö tanky encounter, Stone element, high HP + high toughness
	{
		FMelodiaEnemyDef Enemy;
		Enemy.EnemyId = FName(TEXT("StoneGolem"));
		Enemy.DisplayName = FText::FromString(TEXT("Stone Golem"));
		Enemy.MaxHP = 155.0f;
		Enemy.MaxToughness = 40.0f;
		Enemy.BaseDamage = 12.0f;
		Enemy.Speed = 50;
		Enemy.PrimaryIntentName = FText::FromString(TEXT("Stone Slam"));
		Enemy.PrimaryIntentDamageMultiplier = 1.1f;
		Enemy.Element = EMelodiaSpellElement::Stone;
		Enemy.MeshScale = 1.5f;
		Enemy.BPMOverride = 100.0f;
		DemoEnemies.Add(Enemy);
	}

	// Void Wraith ΓÇö fast encounter, Umbral element, low HP but high damage
	{
		FMelodiaEnemyDef Enemy;
		Enemy.EnemyId = FName(TEXT("VoidWraith"));
		Enemy.DisplayName = FText::FromString(TEXT("Void Wraith"));
		Enemy.MaxHP = 200.0f;
		Enemy.MaxToughness = 80.0f;
		Enemy.BaseDamage = 22.0f;
		Enemy.Speed = 110;
		Enemy.Element = EMelodiaSpellElement::Umbral;
		Enemy.MeshScale = 1.0f;
		Enemy.BPMOverride = 140.0f;
		DemoEnemies.Add(Enemy);
	}

	// Sakura Phantom ΓÇö Radiant element, themed for the Sakura Dream WP pillar
	{
		FMelodiaEnemyDef Enemy;
		Enemy.EnemyId = FName(TEXT("SakuraPhantom"));
		Enemy.DisplayName = FText::FromString(TEXT("Sakura Phantom"));
		Enemy.MaxHP = 140.0f;
		Enemy.MaxToughness = 28.0f;
		Enemy.BaseDamage = 10.0f;
		Enemy.Speed = 85;
		Enemy.PrimaryIntentName = FText::FromString(TEXT("Petal Volley"));
		Enemy.PrimaryIntentDamageMultiplier = 1.0f;
		Enemy.Element = EMelodiaSpellElement::Radiant;
		Enemy.MeshScale = 1.2f;
		Enemy.BPMOverride = 128.0f;
		DemoEnemies.Add(Enemy);
	}

	// Cosmic Sentinel ΓÇö Arcane element, themed for the Cosmic Orrery WP pillar
	{
		FMelodiaEnemyDef Enemy;
		Enemy.EnemyId = FName(TEXT("CosmicSentinel"));
		Enemy.DisplayName = FText::FromString(TEXT("Cosmic Sentinel"));
		Enemy.MaxHP = 500.0f;
		Enemy.MaxToughness = 200.0f;
		Enemy.BaseDamage = 25.0f;
		Enemy.Speed = 70;
		Enemy.Element = EMelodiaSpellElement::Arcane;
		Enemy.MeshScale = 2.0f;
		Enemy.BPMOverride = 144.0f;
		Enemy.bIsBoss = true; // first-dungeon finale boss
		DemoEnemies.Add(Enemy);
	}

	// Fire Drake
	{
		FMelodiaEnemyDef Enemy;
		Enemy.EnemyId = FName(TEXT("FireDrake"));
		Enemy.DisplayName = FText::FromString(TEXT("Fire Drake"));
		Enemy.MaxHP = 160.0f;
		Enemy.MaxToughness = 70.0f;
		Enemy.BaseDamage = 12.0f;
		Enemy.Speed = 75;
		Enemy.Element = EMelodiaSpellElement::Forte;
		Enemy.MeshScale = 1.1f;
		Enemy.BPMOverride = 150.0f;
		DemoEnemies.Add(Enemy);
	}

	// Shadow Wraith
	{
		FMelodiaEnemyDef Enemy;
		Enemy.EnemyId = FName(TEXT("ShadowWraith"));
		Enemy.DisplayName = FText::FromString(TEXT("Shadow Wraith"));
		Enemy.MaxHP = 100.0f;
		Enemy.MaxToughness = 40.0f;
		Enemy.BaseDamage = 15.0f;
		Enemy.Speed = 95;
		Enemy.Element = EMelodiaSpellElement::Umbral;
		Enemy.MeshScale = 0.9f;
		Enemy.BPMOverride = 90.0f;
		DemoEnemies.Add(Enemy);
	}

	// Arcane Golem
	{
		FMelodiaEnemyDef Enemy;
		Enemy.EnemyId = FName(TEXT("ArcaneGolem"));
		Enemy.DisplayName = FText::FromString(TEXT("Arcane Golem"));
		Enemy.MaxHP = 250.0f;
		Enemy.MaxToughness = 120.0f;
		Enemy.BaseDamage = 10.0f;
		Enemy.Speed = 30;
		Enemy.Element = EMelodiaSpellElement::Arcane;
		Enemy.MeshScale = 1.8f;
		Enemy.BPMOverride = 70.0f;
		DemoEnemies.Add(Enemy);
	}

	// Storm Falcon
	{
		FMelodiaEnemyDef Enemy;
		Enemy.EnemyId = FName(TEXT("StormFalcon"));
		Enemy.DisplayName = FText::FromString(TEXT("Storm Falcon"));
		Enemy.MaxHP = 90.0f;
		Enemy.MaxToughness = 30.0f;
		Enemy.BaseDamage = 8.0f;
		Enemy.Speed = 120;
		Enemy.Element = EMelodiaSpellElement::Gale;
		Enemy.MeshScale = 0.85f;
		Enemy.BPMOverride = 180.0f;
		DemoEnemies.Add(Enemy);
	}

	// Abyssal Kraken
	{
		FMelodiaEnemyDef Enemy;
		Enemy.EnemyId = FName(TEXT("AbyssalKraken"));
		Enemy.DisplayName = FText::FromString(TEXT("Abyssal Kraken"));
		Enemy.MaxHP = 300.0f;
		Enemy.MaxToughness = 150.0f;
		Enemy.BaseDamage = 14.0f;
		Enemy.Speed = 20;
		Enemy.Element = EMelodiaSpellElement::Tide;
		Enemy.MeshScale = 2.5f;
		Enemy.BPMOverride = 60.0f;
		DemoEnemies.Add(Enemy);
	}

	// ΓöÇΓöÇΓöÇ NPC Battle Archetypes (Infinity Nikki-inspired) ΓöÇΓöÇΓöÇ
	// Sakura Dreamer ΓÇö Support/Healer, Radiant element
	{
		FMelodiaEnemyDef Enemy;
		Enemy.EnemyId = FName(TEXT("SakuraDreamer_Battle"));
		Enemy.DisplayName = FText::FromString(TEXT("Sakura Dreamer"));
		Enemy.MaxHP = 200.0f;
		Enemy.MaxToughness = 60.0f;
		Enemy.BaseDamage = 12.0f;
		Enemy.Speed = 75;
		Enemy.Element = EMelodiaSpellElement::Radiant;
		Enemy.MeshScale = 1.1f;
		Enemy.BPMOverride = 128.0f;
		DemoEnemies.Add(Enemy);
	}

	// Cosmic Weaver ΓÇö Controller/Buffer, Arcane element
	{
		FMelodiaEnemyDef Enemy;
		Enemy.EnemyId = FName(TEXT("CosmicWeaver_Battle"));
		Enemy.DisplayName = FText::FromString(TEXT("Cosmic Weaver"));
		Enemy.MaxHP = 350.0f;
		Enemy.MaxToughness = 120.0f;
		Enemy.BaseDamage = 18.0f;
		Enemy.Speed = 65;
		Enemy.Element = EMelodiaSpellElement::Arcane;
		Enemy.MeshScale = 1.2f;
		Enemy.BPMOverride = 144.0f;
		DemoEnemies.Add(Enemy);
	}

	// Mirage Dancer ΓÇö DPS/Evasion, Gale element
	{
		FMelodiaEnemyDef Enemy;
		Enemy.EnemyId = FName(TEXT("MirageDancer_Battle"));
		Enemy.DisplayName = FText::FromString(TEXT("Mirage Dancer"));
		Enemy.MaxHP = 160.0f;
		Enemy.MaxToughness = 40.0f;
		Enemy.BaseDamage = 22.0f;
		Enemy.Speed = 110;
		Enemy.Element = EMelodiaSpellElement::Gale;
		Enemy.MeshScale = 0.95f;
		Enemy.BPMOverride = 180.0f;
		DemoEnemies.Add(Enemy);
	}

	return DemoEnemies;
}
