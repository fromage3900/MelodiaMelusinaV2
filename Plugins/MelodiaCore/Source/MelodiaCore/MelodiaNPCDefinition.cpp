// NPC Definition DataAsset Implementation

#include "MelodiaNPCDefinition.h"

bool UMelodiaNPCDataAsset::FindNPCById(FName NPCId, FMelodiaNPCDefinition& OutNPC) const
{
	for (const FMelodiaNPCDefinition& NPC : NPCs)
	{
		if (NPC.NPCId == NPCId)
		{
			OutNPC = NPC;
			return true;
		}
	}
	return false;
}

FMelodiaNPCDefinition UMelodiaNPCDataAsset::GetNPCByIndex(int32 Index) const
{
	if (NPCs.IsValidIndex(Index))
	{
		return NPCs[Index];
	}
	return FMelodiaNPCDefinition();
}

TArray<FMelodiaNPCDefinition> UMelodiaNPCDataAsset::GetNPCsByArchetype(FName Archetype) const
{
	TArray<FMelodiaNPCDefinition> Results;
	for (const FMelodiaNPCDefinition& NPC : NPCs)
	{
		if (NPC.Archetype == Archetype)
		{
			Results.Add(NPC);
		}
	}
	return Results;
}

TArray<FMelodiaNPCDefinition> UMelodiaNPCDataAsset::GetNPCsByZone(FName ZoneName) const
{
	TArray<FMelodiaNPCDefinition> Results;
	for (const FMelodiaNPCDefinition& NPC : NPCs)
	{
		if (NPC.SpawnZones.Contains(ZoneName))
		{
			Results.Add(NPC);
		}
	}
	return Results;
}

TArray<FMelodiaNPCDefinition> UMelodiaNPCDataAsset::GetDemoNPCs()
{
	TArray<FMelodiaNPCDefinition> DemoNPCs;

	// Sakura Dreamers (4)
	{
		FMelodiaNPCDefinition NPC;
		NPC.NPCId = FName(TEXT("SD_01_SakuraMaiden"));
		NPC.DisplayName = FText::FromString(TEXT("Sakura Maiden"));
		NPC.Archetype = FName(TEXT("SakuraDreamer"));
		NPC.Description = FText::FromString(TEXT("Gentle healer who tends the cherry blossoms. Sells petal tea and healing salves."));
		NPC.BaseSkeletalMesh = FSoftObjectPath(TEXT("/Game/NPCs/Imported/SakuraDreamer/SD_01_SakuraMaiden/SK_SD_01_SakuraMaiden"));
		NPC.AnimationBlueprint = FSoftObjectPath(TEXT("/Game/NPCs/Blueprints/ABP_NPC_SakuraDreamer.ABP_NPC_SakuraDreamer_C"));
		NPC.OutfitVariant = FName(TEXT("default"));
		NPC.IdleSet = FName(TEXT("IDLE_GentleSway"));
		NPC.WalkStyle = FName(TEXT("WALK_LightStep"));
		NPC.RunStyle = FName(TEXT("RUN_GracefulGlide"));
		NPC.InteractionGestures = { FName(TEXT("wave_gentle")), FName(TEXT("gesture_explain")), FName(TEXT("offer_item")), FName(TEXT("pose_photo")), FName(TEXT("blessing")) };
		NPC.FacialExpressions = { FName(TEXT("gentle_smile")), FName(TEXT("soft_laugh")), FName(TEXT("thoughtful")), FName(TEXT("dreamy")), FName(TEXT("serene")), FName(TEXT("curious")) };
		NPC.BehaviorType = ENPCBehaviorType::Stationary;
		NPC.InteractionConfig.InteractionType = FName(TEXT("Shop"));
		NPC.InteractionConfig.ShopType = FName(TEXT("healing_items"));
		NPC.InteractionConfig.ShopInventory = { FName(TEXT("PetalTea")), FName(TEXT("SakuraSalve")), FName(TEXT("DreamDust")) };
		NPC.BattleEnemyId = FName(TEXT("SakuraDreamer_Battle"));
		NPC.SpawnZones = { FName(TEXT("SakuraGrove")), FName(TEXT("HealingShrine")), FName(TEXT("PetalPlaza")), FName(TEXT("DreamGarden")) };
		NPC.SpawnLevelPath = TEXT("/Game/Levels/L_PCGTest_Forest");
		NPC.AffinityRewards = {
			{1, FName(TEXT("PetalHairRibbon_ColorVariant")), FText::FromString(TEXT("Unlock pink hair ribbon dye")), FName(TEXT("OutfitVariant"))},
			{3, FName(TEXT("KimonoSleeve_PatternUnlock")), FText::FromString(TEXT("Unlock sakura pattern on kimono")), FName(TEXT("OutfitVariant"))},
			{5, FName(TEXT("HakamaSkirt_GradientDye")), FText::FromString(TEXT("Unlock gradient hakama dye")), FName(TEXT("OutfitVariant"))},
			{10, FName(TEXT("Exclusive_Pose_PetalDance")), FText::FromString(TEXT("Unlock Petal Dance photo pose")), FName(TEXT("Pose"))}
		};
		DemoNPCs.Add(NPC);
	}

	{
		FMelodiaNPCDefinition NPC;
		NPC.NPCId = FName(TEXT("SD_02_PetalPriestess"));
		NPC.DisplayName = FText::FromString(TEXT("Petal Priestess"));
		NPC.Archetype = FName(TEXT("SakuraDreamer"));
		NPC.Description = FText::FromString(TEXT("Shrine maiden who guides lost travelers. Offers blessings and pathfinding quests."));
		NPC.BaseSkeletalMesh = FSoftObjectPath(TEXT("/Game/NPCs/Imported/SakuraDreamer/SD_02_PetalPriestess/SK_SD_02_PetalPriestess"));
		NPC.AnimationBlueprint = FSoftObjectPath(TEXT("/Game/NPCs/Blueprints/ABP_NPC_SakuraDreamer.ABP_NPC_SakuraDreamer_C"));
		NPC.OutfitVariant = FName(TEXT("priestess"));
		NPC.IdleSet = FName(TEXT("IDLE_GentleSway"));
		NPC.WalkStyle = FName(TEXT("WALK_LightStep"));
		NPC.RunStyle = FName(TEXT("RUN_GracefulGlide"));
		NPC.InteractionGestures = { FName(TEXT("prayer")), FName(TEXT("gentle_smile")), FName(TEXT("blessing")), FName(TEXT("serene")) };
		NPC.FacialExpressions = { FName(TEXT("prayer")), FName(TEXT("gentle_smile")), FName(TEXT("blessing")), FName(TEXT("serene")) };
		NPC.BehaviorType = ENPCBehaviorType::Patrol;
		NPC.PatrolPath = FName(TEXT("ShrinePatrolPath"));
		NPC.InteractionConfig.InteractionType = FName(TEXT("Dialogue"));
		NPC.InteractionConfig.DialogueTree = FName(TEXT("PetalPriestess_Intro"));
		NPC.InteractionConfig.bQuestGiver = true;
		NPC.BattleEnemyId = FName(TEXT("SakuraDreamer_Battle"));
		NPC.SpawnZones = { FName(TEXT("HealingShrine")) };
		NPC.SpawnLevelPath = TEXT("/Game/Levels/L_PCGTest_Forest");
		DemoNPCs.Add(NPC);
	}

	{
		FMelodiaNPCDefinition NPC;
		NPC.NPCId = FName(TEXT("SD_03_BlossomGuide"));
		NPC.DisplayName = FText::FromString(TEXT("Blossom Guide"));
		NPC.Archetype = FName(TEXT("SakuraDreamer"));
		NPC.Description = FText::FromString(TEXT("Wandering guide who knows all hidden paths. Shares tips for photo spots and secret groves."));
		NPC.BaseSkeletalMesh = FSoftObjectPath(TEXT("/Game/NPCs/Imported/SakuraDreamer/SD_03_BlossomGuide/SK_SD_03_BlossomGuide"));
		NPC.AnimationBlueprint = FSoftObjectPath(TEXT("/Game/NPCs/Blueprints/ABP_NPC_SakuraDreamer.ABP_NPC_SakuraDreamer_C"));
		NPC.OutfitVariant = FName(TEXT("guide"));
		NPC.IdleSet = FName(TEXT("IDLE_GentleSway"));
		NPC.WalkStyle = FName(TEXT("WALK_LightStep"));
		NPC.RunStyle = FName(TEXT("RUN_GracefulGlide"));
		NPC.InteractionGestures = { FName(TEXT("guiding_smile")), FName(TEXT("curious")), FName(TEXT("gentle_laugh")), FName(TEXT("welcoming")) };
		NPC.FacialExpressions = { FName(TEXT("guiding_smile")), FName(TEXT("curious")), FName(TEXT("gentle_laugh")), FName(TEXT("welcoming")) };
		NPC.BehaviorType = ENPCBehaviorType::Wander;
		NPC.WanderRadius = 800.0f;
		NPC.InteractionConfig.InteractionType = FName(TEXT("Dialogue"));
		NPC.InteractionConfig.DialogueTree = FName(TEXT("BlossomGuide_Paths"));
		NPC.InteractionConfig.Tips = { FName(TEXT("hidden_grove")), FName(TEXT("photo_spot")) };
		NPC.BattleEnemyId = FName(TEXT("SakuraDreamer_Battle"));
		NPC.SpawnZones = { FName(TEXT("PetalPlaza")) };
		NPC.SpawnLevelPath = TEXT("/Game/Levels/L_PCGTest_Forest");
		DemoNPCs.Add(NPC);
	}

	{
		FMelodiaNPCDefinition NPC;
		NPC.NPCId = FName(TEXT("SD_04_FlowerMerchant"));
		NPC.DisplayName = FText::FromString(TEXT("Flower Merchant"));
		NPC.Archetype = FName(TEXT("SakuraDreamer"));
		NPC.Description = FText::FromString(TEXT("Cheerful vendor selling cosmetic dyes, ribbons, and flower crowns for photo mode."));
		NPC.BaseSkeletalMesh = FSoftObjectPath(TEXT("/Game/NPCs/Imported/SakuraDreamer/SD_04_FlowerMerchant/SK_SD_04_FlowerMerchant"));
		NPC.AnimationBlueprint = FSoftObjectPath(TEXT("/Game/NPCs/Blueprints/ABP_NPC_SakuraDreamer.ABP_NPC_SakuraDreamer_C"));
		NPC.OutfitVariant = FName(TEXT("merchant"));
		NPC.IdleSet = FName(TEXT("IDLE_GentleSway"));
		NPC.WalkStyle = FName(TEXT("WALK_LightStep"));
		NPC.RunStyle = FName(TEXT("RUN_GracefulGlide"));
		NPC.InteractionGestures = { FName(TEXT("merchant_smile")), FName(TEXT("proud")), FName(TEXT("thoughtful")), FName(TEXT("laughing")) };
		NPC.FacialExpressions = { FName(TEXT("merchant_smile")), FName(TEXT("proud")), FName(TEXT("thoughtful")), FName(TEXT("laughing")) };
		NPC.BehaviorType = ENPCBehaviorType::Stationary;
		NPC.InteractionConfig.InteractionType = FName(TEXT("Shop"));
		NPC.InteractionConfig.ShopType = FName(TEXT("cosmetics"));
		NPC.InteractionConfig.ShopInventory = { FName(TEXT("PetalDye_Pink")), FName(TEXT("Ribbon_White")), FName(TEXT("FlowerCrown")) };
		NPC.BattleEnemyId = FName(TEXT("SakuraDreamer_Battle"));
		NPC.SpawnZones = { FName(TEXT("DreamGarden")) };
		NPC.SpawnLevelPath = TEXT("/Game/Levels/L_PCGTest_Forest");
		DemoNPCs.Add(NPC);
	}

	{
		FMelodiaNPCDefinition NPC;
		NPC.NPCId = FName(TEXT("SD_05_EternalGardener"));
		NPC.DisplayName = FText::FromString(TEXT("Eternal Gardener"));
		NPC.Archetype = FName(TEXT("SakuraDreamer"));
		NPC.Description = FText::FromString(TEXT("Ancient keeper of the grove. Boss-tier battle encounter with unique rewards."));
		NPC.BaseSkeletalMesh = FSoftObjectPath(TEXT("/Game/NPCs/Imported/SakuraDreamer/SD_05_EternalGardener/SK_SD_05_EternalGardener"));
		NPC.AnimationBlueprint = FSoftObjectPath(TEXT("/Game/NPCs/Blueprints/ABP_NPC_SakuraDreamer.ABP_NPC_SakuraDreamer_C"));
		NPC.OutfitVariant = FName(TEXT("elder"));
		NPC.IdleSet = FName(TEXT("IDLE_GentleSway"));
		NPC.WalkStyle = FName(TEXT("WALK_LightStep"));
		NPC.RunStyle = FName(TEXT("RUN_GracefulGlide"));
		NPC.InteractionGestures = { FName(TEXT("nurturing")), FName(TEXT("gentle_wisdom")), FName(TEXT("blooming_smile")), FName(TEXT("peaceful")) };
		NPC.FacialExpressions = { FName(TEXT("nurturing")), FName(TEXT("gentle_wisdom")), FName(TEXT("blooming_smile")), FName(TEXT("peaceful")) };
		NPC.BehaviorType = ENPCBehaviorType::Event;
		NPC.InteractionConfig.InteractionType = FName(TEXT("Battle"));
		NPC.InteractionConfig.BattleEnemyId = FName(TEXT("SakuraDreamer_Battle"));
		NPC.InteractionConfig.Difficulty = FName(TEXT("Boss"));
		NPC.InteractionConfig.BattleRewards = { FName(TEXT("EternalPetal")), FName(TEXT("GroveKey")), FName(TEXT("GardenerTitle")) };
		NPC.BattleEnemyId = FName(TEXT("SakuraDreamer_Battle"));
		NPC.BattleDifficulty = FName(TEXT("Boss"));
		NPC.SpawnZones = { FName(TEXT("SakuraGrove")) };
		NPC.SpawnLevelPath = TEXT("/Game/Levels/L_PCGTest_Forest");
		NPC.SpawnWeight = 0.1f;
		DemoNPCs.Add(NPC);
	}

	// Cosmic Weavers (3)
	{
		FMelodiaNPCDefinition NPC;
		NPC.NPCId = FName(TEXT("CW_01_StarWeaver"));
		NPC.DisplayName = FText::FromString(TEXT("Star Weaver"));
		NPC.Archetype = FName(TEXT("CosmicWeaver"));
		NPC.Description = FText::FromString(TEXT("Celestial artisan weaving fate from starlight. Battle encounter rewards constellation maps."));
		NPC.BaseSkeletalMesh = FSoftObjectPath(TEXT("/Game/NPCs/Imported/CosmicWeaver/CW_01_StarWeaver/SK_CW_01_StarWeaver"));
		NPC.AnimationBlueprint = FSoftObjectPath(TEXT("/Game/NPCs/Blueprints/ABP_NPC_CosmicWeaver.ABP_NPC_CosmicWeaver_C"));
		NPC.OutfitVariant = FName(TEXT("default"));
		NPC.IdleSet = FName(TEXT("IDLE_MysticalFloat"));
		NPC.WalkStyle = FName(TEXT("WALK_PurposefulStride"));
		NPC.RunStyle = FName(TEXT("RUN_StarlightTrail"));
		NPC.InteractionGestures = { FName(TEXT("gesture_reading")), FName(TEXT("crystal_gaze")), FName(TEXT("weaving_motion")), FName(TEXT("star_point")), FName(TEXT("knowing_nod")) };
		NPC.FacialExpressions = { FName(TEXT("mystical")), FName(TEXT("knowing_smile")), FName(TEXT("contemplative")), FName(TEXT("stargazing")), FName(TEXT("focused")), FName(TEXT("gentle")) };
		NPC.BehaviorType = ENPCBehaviorType::Stationary;
		NPC.InteractionConfig.InteractionType = FName(TEXT("Battle"));
		NPC.InteractionConfig.BattleEnemyId = FName(TEXT("CosmicWeaver_Battle"));
		NPC.InteractionConfig.Difficulty = FName(TEXT("Normal"));
		NPC.InteractionConfig.BattleRewards = { FName(TEXT("StarlightThread")), FName(TEXT("ConstellationMap")) };
		NPC.BattleEnemyId = FName(TEXT("CosmicWeaver_Battle"));
		NPC.SpawnZones = { FName(TEXT("StarObservatory")) };
		NPC.SpawnLevelPath = TEXT("/Game/Levels/L_PCGTest_Forest");
		DemoNPCs.Add(NPC);
	}

	{
		FMelodiaNPCDefinition NPC;
		NPC.NPCId = FName(TEXT("CW_02_VoidSeamstress"));
		NPC.DisplayName = FText::FromString(TEXT("Void Seamstress"));
		NPC.Archetype = FName(TEXT("CosmicWeaver"));
		NPC.Description = FText::FromString(TEXT("Time-sensitive NPC who moves between observatory, garden, and tower. Night-only dialogue."));
		NPC.BaseSkeletalMesh = FSoftObjectPath(TEXT("/Game/NPCs/Imported/CosmicWeaver/CW_02_VoidSeamstress/SK_CW_02_VoidSeamstress"));
		NPC.AnimationBlueprint = FSoftObjectPath(TEXT("/Game/NPCs/Blueprints/ABP_NPC_CosmicWeaver.ABP_NPC_CosmicWeaver_C"));
		NPC.OutfitVariant = FName(TEXT("seamstress"));
		NPC.IdleSet = FName(TEXT("IDLE_MysticalFloat"));
		NPC.WalkStyle = FName(TEXT("WALK_PurposefulStride"));
		NPC.RunStyle = FName(TEXT("RUN_StarlightTrail"));
		NPC.InteractionGestures = { FName(TEXT("focused")), FName(TEXT("subtle_smile")), FName(TEXT("weaving")), FName(TEXT("distant")) };
		NPC.FacialExpressions = { FName(TEXT("focused")), FName(TEXT("subtle_smile")), FName(TEXT("weaving")), FName(TEXT("distant")) };
		NPC.BehaviorType = ENPCBehaviorType::Schedule;
		NPC.Schedule = {
			{ TEXT("06:00"), FVector(-2500, 3000, 150), FRotator::ZeroRotator, FName(TEXT("IDLE_MysticalFloat")) },
			{ TEXT("18:00"), FVector(-1800, 2200, 100), FRotator::ZeroRotator, FName(TEXT("IDLE_MysticalFloat")) },
			{ TEXT("22:00"), FVector(-3000, 3500, 250), FRotator::ZeroRotator, FName(TEXT("IDLE_MysticalFloat")) }
		};
		NPC.InteractionConfig.InteractionType = FName(TEXT("Dialogue"));
		NPC.InteractionConfig.DialogueTree = FName(TEXT("VoidSeamstress_Night"));
		NPC.InteractionConfig.bTimeSensitive = true;
		NPC.BattleEnemyId = FName(TEXT("CosmicWeaver_Battle"));
		NPC.SpawnZones = { FName(TEXT("CosmicLibrary")) };
		NPC.SpawnLevelPath = TEXT("/Game/Levels/L_PCGTest_Forest");
		DemoNPCs.Add(NPC);
	}

	{
		FMelodiaNPCDefinition NPC;
		NPC.NPCId = FName(TEXT("CW_03_AstralScribe"));
		NPC.DisplayName = FText::FromString(TEXT("Astral Scribe"));
		NPC.Archetype = FName(TEXT("CosmicWeaver"));
		NPC.Description = FText::FromString(TEXT("Keeper of the Starfall Chronicles. Quest giver for multi-step stellar questline."));
		NPC.BaseSkeletalMesh = FSoftObjectPath(TEXT("/Game/NPCs/Imported/CosmicWeaver/CW_03_AstralScribe/SK_CW_03_AstralScribe"));
		NPC.AnimationBlueprint = FSoftObjectPath(TEXT("/Game/NPCs/Blueprints/ABP_NPC_CosmicWeaver.ABP_NPC_CosmicWeaver_C"));
		NPC.OutfitVariant = FName(TEXT("scribe"));
		NPC.IdleSet = FName(TEXT("IDLE_MysticalFloat"));
		NPC.WalkStyle = FName(TEXT("WALK_PurposefulStride"));
		NPC.RunStyle = FName(TEXT("RUN_StarlightTrail"));
		NPC.InteractionGestures = { FName(TEXT("writing")), FName(TEXT("looking_up")), FName(TEXT("gentle_smile")), FName(TEXT("concentrating")) };
		NPC.FacialExpressions = { FName(TEXT("writing")), FName(TEXT("looking_up")), FName(TEXT("gentle_smile")), FName(TEXT("concentrating")) };
		NPC.BehaviorType = ENPCBehaviorType::Stationary;
		NPC.InteractionConfig.InteractionType = FName(TEXT("Quest"));
		NPC.InteractionConfig.QuestChain = FName(TEXT("StarfallChronicles"));
		NPC.InteractionConfig.QuestStep = 1;
		NPC.BattleEnemyId = FName(TEXT("CosmicWeaver_Battle"));
		NPC.SpawnZones = { FName(TEXT("AstralNexus")) };
		NPC.SpawnLevelPath = TEXT("/Game/Levels/L_PCGTest_Forest");
		DemoNPCs.Add(NPC);
	}

	// Mirage Dancers (3)
	{
		FMelodiaNPCDefinition NPC;
		NPC.NPCId = FName(TEXT("MD_01_TwilightDancer"));
		NPC.DisplayName = FText::FromString(TEXT("Twilight Dancer"));
		NPC.Archetype = FName(TEXT("MirageDancer"));
		NPC.Description = FText::FromString(TEXT("Graceful dancer who performs at dusk. Photo mode pose partner with ribbon trails."));
		NPC.BaseSkeletalMesh = FSoftObjectPath(TEXT("/Game/NPCs/Imported/MirageDancer/MD_01_TwilightDancer/SK_MD_01_TwilightDancer"));
		NPC.AnimationBlueprint = FSoftObjectPath(TEXT("/Game/NPCs/Blueprints/ABP_NPC_MirageDancer.ABP_NPC_MirageDancer_C"));
		NPC.OutfitVariant = FName(TEXT("dancer"));
		NPC.IdleSet = FName(TEXT("IDLE_BreezyShift"));
		NPC.WalkStyle = FName(TEXT("WALK_DanceStep"));
		NPC.RunStyle = FName(TEXT("RUN_WindRider"));
		NPC.InteractionGestures = { FName(TEXT("spin_flourish")), FName(TEXT("ribbon_wave")), FName(TEXT("confident_grin")), FName(TEXT("wind_swept_hair")), FName(TEXT("photo_pose_dynamic")) };
		NPC.FacialExpressions = { FName(TEXT("joyful")), FName(TEXT("determined")), FName(TEXT("wind_swept")), FName(TEXT("playful")), FName(TEXT("confident")), FName(TEXT("breezy_laugh")) };
		NPC.BehaviorType = ENPCBehaviorType::Wander;
		NPC.WanderRadius = 1200.0f;
		NPC.InteractionConfig.InteractionType = FName(TEXT("Photo"));
		NPC.InteractionConfig.PhotoPoseSet = FName(TEXT("TwilightDance"));
		NPC.InteractionConfig.PhotoReward = FName(TEXT("TwilightRibbon"));
		NPC.BattleEnemyId = FName(TEXT("MirageDancer_Battle"));
		NPC.SpawnZones = { FName(TEXT("TwilightDunes")) };
		NPC.SpawnLevelPath = TEXT("/Game/Levels/L_PCGTest_Forest");
		DemoNPCs.Add(NPC);
	}

	{
		FMelodiaNPCDefinition NPC;
		NPC.NPCId = FName(TEXT("MD_02_WindWalker"));
		NPC.DisplayName = FText::FromString(TEXT("Wind Walker"));
		NPC.Archetype = FName(TEXT("MirageDancer"));
		NPC.Description = FText::FromString(TEXT("Swift messenger patrolling the wind paths. Hard difficulty battle for Zephyr Step reward."));
		NPC.BaseSkeletalMesh = FSoftObjectPath(TEXT("/Game/NPCs/Imported/MirageDancer/MD_02_WindWalker/SK_MD_02_WindWalker"));
		NPC.AnimationBlueprint = FSoftObjectPath(TEXT("/Game/NPCs/Blueprints/ABP_NPC_MirageDancer.ABP_NPC_MirageDancer_C"));
		NPC.OutfitVariant = FName(TEXT("walker"));
		NPC.IdleSet = FName(TEXT("IDLE_BreezyShift"));
		NPC.WalkStyle = FName(TEXT("WALK_DanceStep"));
		NPC.RunStyle = FName(TEXT("RUN_WindRider"));
		NPC.InteractionGestures = { FName(TEXT("walking")), FName(TEXT("determined")), FName(TEXT("breezy")), FName(TEXT("confident")) };
		NPC.FacialExpressions = { FName(TEXT("walking")), FName(TEXT("determined")), FName(TEXT("breezy")), FName(TEXT("confident")) };
		NPC.BehaviorType = ENPCBehaviorType::Patrol;
		NPC.PatrolPath = FName(TEXT("WindPath_Clearing"));
		NPC.InteractionConfig.InteractionType = FName(TEXT("Battle"));
		NPC.InteractionConfig.BattleEnemyId = FName(TEXT("MirageDancer_Battle"));
		NPC.InteractionConfig.Difficulty = FName(TEXT("Hard"));
		NPC.InteractionConfig.BattleRewards = { FName(TEXT("WindBell")), FName(TEXT("ZephyrStep")) };
		NPC.BattleEnemyId = FName(TEXT("MirageDancer_Battle"));
		NPC.BattleDifficulty = FName(TEXT("Hard"));
		NPC.SpawnZones = { FName(TEXT("WindTemple")) };
		NPC.SpawnLevelPath = TEXT("/Game/Levels/L_PCGTest_Forest");
		DemoNPCs.Add(NPC);
	}

	{
		FMelodiaNPCDefinition NPC;
		NPC.NPCId = FName(TEXT("MD_03_ZephyrChampion"));
		NPC.DisplayName = FText::FromString(TEXT("Zephyr Champion"));
		NPC.Archetype = FName(TEXT("MirageDancer"));
		NPC.Description = FText::FromString(TEXT("Master of the winds. Boss encounter requiring 2 Mirage Dancer defeats. Ultimate dancer title reward."));
		NPC.BaseSkeletalMesh = FSoftObjectPath(TEXT("/Game/NPCs/Imported/MirageDancer/MD_03_ZephyrChampion/SK_MD_03_ZephyrChampion"));
		NPC.AnimationBlueprint = FSoftObjectPath(TEXT("/Game/NPCs/Blueprints/ABP_NPC_MirageDancer.ABP_NPC_MirageDancer_C"));
		NPC.OutfitVariant = FName(TEXT("champion"));
		NPC.IdleSet = FName(TEXT("IDLE_BreezyShift"));
		NPC.WalkStyle = FName(TEXT("WALK_DanceStep"));
		NPC.RunStyle = FName(TEXT("RUN_WindRider"));
		NPC.InteractionGestures = { FName(TEXT("champion_pose")), FName(TEXT("wind_mastery")), FName(TEXT("confident_grin")), FName(TEXT("battle_ready")) };
		NPC.FacialExpressions = { FName(TEXT("champion_pose")), FName(TEXT("wind_mastery")), FName(TEXT("confident_grin")), FName(TEXT("battle_ready")) };
		NPC.BehaviorType = ENPCBehaviorType::Event;
		NPC.InteractionConfig.InteractionType = FName(TEXT("Battle"));
		NPC.InteractionConfig.BattleEnemyId = FName(TEXT("MirageDancer_Battle"));
		NPC.InteractionConfig.Difficulty = FName(TEXT("Boss"));
		NPC.InteractionConfig.BattleRewards = { FName(TEXT("ChampionScarf")), FName(TEXT("ZephyrTitle")), FName(TEXT("MasterDancerPose")) };
		NPC.InteractionConfig.UnlockRequirement = FName(TEXT("defeat_2_mirage_dancers"));
		NPC.BattleEnemyId = FName(TEXT("MirageDancer_Battle"));
		NPC.BattleDifficulty = FName(TEXT("Boss"));
		NPC.SpawnZones = { FName(TEXT("ZephyrPeak")) };
		NPC.SpawnLevelPath = TEXT("/Game/Levels/L_PCGTest_Forest");
		NPC.SpawnWeight = 0.1f;
		DemoNPCs.Add(NPC);
	}

	return DemoNPCs;
}
