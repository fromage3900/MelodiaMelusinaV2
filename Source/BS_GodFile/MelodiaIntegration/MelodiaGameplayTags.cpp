#include "MelodiaGameplayTags.h"
#include "GameplayTagsManager.h"

// ── Water Network Tags ────────────────────────────────────────────────────────

FGameplayTag FMeliaWaterNetworkTag::TagAlpha = FGameplayTag();
FGameplayTag FMeliaWaterNetworkTag::TagBeta = FGameplayTag();
FGameplayTag FMeliaWaterNetworkTag::TagGamma = FGameplayTag();

void FMeliaWaterNetworkTag::RegisterTags()
{
	auto& Manager = UGameplayTagsManager::Get();
	TagAlpha = Manager.AddNativeGameplayTag(TEXT("Melodia.Water.Network.Alpha"), TEXT("Alpha water network"));
	TagBeta = Manager.AddNativeGameplayTag(TEXT("Melodia.Water.Network.Beta"), TEXT("Beta water network"));
	TagGamma = Manager.AddNativeGameplayTag(TEXT("Melodia.Water.Network.Gamma"), TEXT("Gamma water network"));
}

// ── Water Node Tags ──────────────────────────────────────────────────────────

FGameplayTag FMeliaWaterNodeTag::ReservoirMain = FGameplayTag();
FGameplayTag FMeliaWaterNodeTag::ReservoirEast = FGameplayTag();
FGameplayTag FMeliaWaterNodeTag::ReservoirWest = FGameplayTag();
FGameplayTag FMeliaWaterNodeTag::ChannelNorth = FGameplayTag();
FGameplayTag FMeliaWaterNodeTag::ChannelSouth = FGameplayTag();
FGameplayTag FMeliaWaterNodeTag::ChannelCentral = FGameplayTag();
FGameplayTag FMeliaWaterNodeTag::ValveMain = FGameplayTag();
FGameplayTag FMeliaWaterNodeTag::ValveBypass = FGameplayTag();

void FMeliaWaterNodeTag::RegisterTags()
{
	auto& Manager = UGameplayTagsManager::Get();
	ReservoirMain = Manager.AddNativeGameplayTag(TEXT("Melodia.Water.Node.ReservoirMain"), TEXT("Main reservoir"));
	ReservoirEast = Manager.AddNativeGameplayTag(TEXT("Melodia.Water.Node.ReservoirEast"), TEXT("East reservoir"));
	ReservoirWest = Manager.AddNativeGameplayTag(TEXT("Melodia.Water.Node.ReservoirWest"), TEXT("West reservoir"));
	ChannelNorth = Manager.AddNativeGameplayTag(TEXT("Melodia.Water.Node.ChannelNorth"), TEXT("North channel"));
	ChannelSouth = Manager.AddNativeGameplayTag(TEXT("Melodia.Water.Node.ChannelSouth"), TEXT("South channel"));
	ChannelCentral = Manager.AddNativeGameplayTag(TEXT("Melodia.Water.Node.ChannelCentral"), TEXT("Central channel"));
	ValveMain = Manager.AddNativeGameplayTag(TEXT("Melodia.Water.Node.ValveMain"), TEXT("Main valve"));
	ValveBypass = Manager.AddNativeGameplayTag(TEXT("Melodia.Water.Node.ValveBypass"), TEXT("Bypass valve"));
}

// ── Water Route Tags ─────────────────────────────────────────────────────────

FGameplayTag FMeliaWaterRouteTag::MainFlow = FGameplayTag();
FGameplayTag FMeliaWaterRouteTag::Bypass = FGameplayTag();
FGameplayTag FMeliaWaterRouteTag::Overflow = FGameplayTag();
FGameplayTag FMeliaWaterRouteTag::Return = FGameplayTag();

void FMeliaWaterRouteTag::RegisterTags()
{
	auto& Manager = UGameplayTagsManager::Get();
	MainFlow = Manager.AddNativeGameplayTag(TEXT("Melodia.Water.Route.MainFlow"), TEXT("Main flow route"));
	Bypass = Manager.AddNativeGameplayTag(TEXT("Melodia.Water.Route.Bypass"), TEXT("Bypass route"));
	Overflow = Manager.AddNativeGameplayTag(TEXT("Melodia.Water.Route.Overflow"), TEXT("Overflow route"));
	Return = Manager.AddNativeGameplayTag(TEXT("Melodia.Water.Route.Return"), TEXT("Return route"));
}

// ── Water Body Tags ──────────────────────────────────────────────────────────

FGameplayTag FMeliaWaterBodyTag::LakeKaleido = FGameplayTag();
FGameplayTag FMeliaWaterBodyTag::RiverNave = FGameplayTag();
FGameplayTag FMeliaWaterBodyTag::FallsMelusina = FGameplayTag();
FGameplayTag FMeliaWaterBodyTag::PoolReflection = FGameplayTag();

void FMeliaWaterBodyTag::RegisterTags()
{
	auto& Manager = UGameplayTagsManager::Get();
	LakeKaleido = Manager.AddNativeGameplayTag(TEXT("Melodia.Water.Body.LakeKaleido"), TEXT("Lake Kaleido"));
	RiverNave = Manager.AddNativeGameplayTag(TEXT("Melodia.Water.Body.RiverNave"), TEXT("River Nave"));
	FallsMelusina = Manager.AddNativeGameplayTag(TEXT("Melodia.Water.Body.FallsMelusina"), TEXT("Falls Melusina"));
	PoolReflection = Manager.AddNativeGameplayTag(TEXT("Melodia.Water.Body.PoolReflection"), TEXT("Reflection Pool"));
}

// ── Water Puzzle Tags ────────────────────────────────────────────────────────

FGameplayTag FMeliaWaterPuzzleTag::Resonance01 = FGameplayTag();
FGameplayTag FMeliaWaterPuzzleTag::Resonance02 = FGameplayTag();
FGameplayTag FMeliaWaterPuzzleTag::Resonance03 = FGameplayTag();
FGameplayTag FMeliaWaterPuzzleTag::FlowControl = FGameplayTag();
FGameplayTag FMeliaWaterPuzzleTag::PressureBalance = FGameplayTag();

void FMeliaWaterPuzzleTag::RegisterTags()
{
	auto& Manager = UGameplayTagsManager::Get();
	Resonance01 = Manager.AddNativeGameplayTag(TEXT("Melodia.Water.Puzzle.Resonance01"), TEXT("Resonance puzzle 01"));
	Resonance02 = Manager.AddNativeGameplayTag(TEXT("Melodia.Water.Puzzle.Resonance02"), TEXT("Resonance puzzle 02"));
	Resonance03 = Manager.AddNativeGameplayTag(TEXT("Melodia.Water.Puzzle.Resonance03"), TEXT("Resonance puzzle 03"));
	FlowControl = Manager.AddNativeGameplayTag(TEXT("Melodia.Water.Puzzle.FlowControl"), TEXT("Flow control puzzle"));
	PressureBalance = Manager.AddNativeGameplayTag(TEXT("Melodia.Water.Puzzle.PressureBalance"), TEXT("Pressure balance puzzle"));
}

// ── Water Platform Tags ──────────────────────────────────────────────────────

FGameplayTag FMeliaWaterPlatformTag::FerryKaleido = FGameplayTag();
FGameplayTag FMeliaWaterPlatformTag::RaftNave = FGameplayTag();
FGameplayTag FMeliaWaterPlatformTag::LiftFalls = FGameplayTag();

void FMeliaWaterPlatformTag::RegisterTags()
{
	auto& Manager = UGameplayTagsManager::Get();
	FerryKaleido = Manager.AddNativeGameplayTag(TEXT("Melodia.Water.Platform.FerryKaleido"), TEXT("Kaleido ferry"));
	RaftNave = Manager.AddNativeGameplayTag(TEXT("Melodia.Water.Platform.RaftNave"), TEXT("Nave raft"));
	LiftFalls = Manager.AddNativeGameplayTag(TEXT("Melodia.Water.Platform.LiftFalls"), TEXT("Falls lift"));
}

// ── Water Channel Tags ───────────────────────────────────────────────────────

FGameplayTag FMeliaWaterChannelTag::Harmonic = FGameplayTag();
FGameplayTag FMeliaWaterChannelTag::Dissonant = FGameplayTag();
FGameplayTag FMeliaWaterChannelTag::Crescendo = FGameplayTag();
FGameplayTag FMeliaWaterChannelTag::Diminuendo = FGameplayTag();

void FMeliaWaterChannelTag::RegisterTags()
{
	auto& Manager = UGameplayTagsManager::Get();
	Harmonic = Manager.AddNativeGameplayTag(TEXT("Melodia.Water.Channel.Harmonic"), TEXT("Harmonic resonance channel"));
	Dissonant = Manager.AddNativeGameplayTag(TEXT("Melodia.Water.Channel.Dissonant"), TEXT("Dissonant resonance channel"));
	Crescendo = Manager.AddNativeGameplayTag(TEXT("Melodia.Water.Channel.Crescendo"), TEXT("Crescendo resonance channel"));
	Diminuendo = Manager.AddNativeGameplayTag(TEXT("Melodia.Water.Channel.Diminuendo"), TEXT("Diminuendo resonance channel"));
}

// ── Battle Encounter Tags ────────────────────────────────────────────────────

FGameplayTag FMeliaBattleEncounterTag::KaleidoNaveMelodySlime = FGameplayTag();
FGameplayTag FMeliaBattleEncounterTag::CrystalShard = FGameplayTag();
FGameplayTag FMeliaBattleEncounterTag::CosmicReaver = FGameplayTag();
FGameplayTag FMeliaBattleEncounterTag::ChoralSheep = FGameplayTag();

void FMeliaBattleEncounterTag::RegisterTags()
{
	auto& Manager = UGameplayTagsManager::Get();
	KaleidoNaveMelodySlime = Manager.AddNativeGameplayTag(TEXT("Melodia.Battle.Encounter.KaleidoNaveMelodySlime"), TEXT("Kaleido Nave Melody Slime"));
	CrystalShard = Manager.AddNativeGameplayTag(TEXT("Melodia.Battle.Encounter.CrystalShard"), TEXT("Crystal Shard"));
	CosmicReaver = Manager.AddNativeGameplayTag(TEXT("Melodia.Battle.Encounter.CosmicReaver"), TEXT("Cosmic Reaver"));
	ChoralSheep = Manager.AddNativeGameplayTag(TEXT("Melodia.Battle.Encounter.ChoralSheep"), TEXT("Choral Sheep"));
}

// ── Quest Tags ───────────────────────────────────────────────────────────────

FGameplayTag FMeliaQuestTag::FirstDream = FGameplayTag();
FGameplayTag FMeliaQuestTag::WardrobeEquip = FGameplayTag();
FGameplayTag FMeliaQuestTag::ChoralSheepRecruit = FGameplayTag();
FGameplayTag FMeliaQuestTag::SeaAboveCutscene = FGameplayTag();
FGameplayTag FMeliaQuestTag::Echo01 = FGameplayTag();
FGameplayTag FMeliaQuestTag::Echo02 = FGameplayTag();
FGameplayTag FMeliaQuestTag::Echo03 = FGameplayTag();
FGameplayTag FMeliaQuestTag::SmokeQuest = FGameplayTag();

void FMeliaQuestTag::RegisterTags()
{
	auto& Manager = UGameplayTagsManager::Get();
	FirstDream = Manager.AddNativeGameplayTag(TEXT("Melodia.Quest.FirstDream"), TEXT("First Dream"));
	WardrobeEquip = Manager.AddNativeGameplayTag(TEXT("Melodia.Quest.WardrobeEquip"), TEXT("Wardrobe Equip"));
	ChoralSheepRecruit = Manager.AddNativeGameplayTag(TEXT("Melodia.Quest.ChoralSheepRecruit"), TEXT("Choral Sheep Recruit"));
	SeaAboveCutscene = Manager.AddNativeGameplayTag(TEXT("Melodia.Quest.SeaAboveCutscene"), TEXT("Sea Above Cutscene"));
	Echo01 = Manager.AddNativeGameplayTag(TEXT("Melodia.Quest.Echo01"), TEXT("Echo 01"));
	Echo02 = Manager.AddNativeGameplayTag(TEXT("Melodia.Quest.Echo02"), TEXT("Echo 02"));
	Echo03 = Manager.AddNativeGameplayTag(TEXT("Melodia.Quest.Echo03"), TEXT("Echo 03"));
	SmokeQuest = Manager.AddNativeGameplayTag(TEXT("Melodia.Quest.SmokeQuest"), TEXT("Smoke Quest"));
}

// ── Flag Tags ────────────────────────────────────────────────────────────────

FGameplayTag FMeliaFlagTag::BattleWon = FGameplayTag();
FGameplayTag FMeliaFlagTag::SmokeComplete = FGameplayTag();
FGameplayTag FMeliaFlagTag::FirstDreamCompleted = FGameplayTag();
FGameplayTag FMeliaFlagTag::FirstDreamAttempted = FGameplayTag();
FGameplayTag FMeliaFlagTag::FirstDreamFled = FGameplayTag();
FGameplayTag FMeliaFlagTag::P0PlaythroughCompleted = FGameplayTag();
FGameplayTag FMeliaFlagTag::P0PlaythroughAttempted = FGameplayTag();
FGameplayTag FMeliaFlagTag::P0PlaythroughFled = FGameplayTag();
FGameplayTag FMeliaFlagTag::WardrobeOutfitEquipped = FGameplayTag();
FGameplayTag FMeliaFlagTag::WardrobeEquipCompleted = FGameplayTag();
FGameplayTag FMeliaFlagTag::MelusinaSorrowSeamRestored = FGameplayTag();
FGameplayTag FMeliaFlagTag::ChoralSheepRecruited = FGameplayTag();
FGameplayTag FMeliaFlagTag::ChoralSheepCompleted = FGameplayTag();
FGameplayTag FMeliaFlagTag::SeaAboveWitnessed = FGameplayTag();
FGameplayTag FMeliaFlagTag::SeaAboveMembranePulseActive = FGameplayTag();
FGameplayTag FMeliaFlagTag::SeaAboveCompleted = FGameplayTag();

void FMeliaFlagTag::RegisterTags()
{
	auto& Manager = UGameplayTagsManager::Get();
	BattleWon = Manager.AddNativeGameplayTag(TEXT("Melodia.Flag.BattleWon"), TEXT("Battle won"));
	SmokeComplete = Manager.AddNativeGameplayTag(TEXT("Melodia.Flag.SmokeComplete"), TEXT("Smoke complete"));
	FirstDreamCompleted = Manager.AddNativeGameplayTag(TEXT("Melodia.Flag.FirstDream.Completed"), TEXT("First Dream completed"));
	FirstDreamAttempted = Manager.AddNativeGameplayTag(TEXT("Melodia.Flag.FirstDream.Attempted"), TEXT("First Dream attempted"));
	FirstDreamFled = Manager.AddNativeGameplayTag(TEXT("Melodia.Flag.FirstDream.Fled"), TEXT("First Dream fled"));
	P0PlaythroughCompleted = Manager.AddNativeGameplayTag(TEXT("Melodia.Flag.P0Playthrough.Completed"), TEXT("P0 playthrough completed"));
	P0PlaythroughAttempted = Manager.AddNativeGameplayTag(TEXT("Melodia.Flag.P0Playthrough.Attempted"), TEXT("P0 playthrough attempted"));
	P0PlaythroughFled = Manager.AddNativeGameplayTag(TEXT("Melodia.Flag.P0Playthrough.Fled"), TEXT("P0 playthrough fled"));
	WardrobeOutfitEquipped = Manager.AddNativeGameplayTag(TEXT("Melodia.Flag.Wardrobe.OutfitEquipped"), TEXT("Outfit equipped"));
	WardrobeEquipCompleted = Manager.AddNativeGameplayTag(TEXT("Melodia.Flag.Wardrobe.EquipCompleted"), TEXT("Wardrobe equip completed"));
	MelusinaSorrowSeamRestored = Manager.AddNativeGameplayTag(TEXT("Melodia.Flag.Melusina.SorrowSeamRestored"), TEXT("Sorrow Seam restored"));
	ChoralSheepRecruited = Manager.AddNativeGameplayTag(TEXT("Melodia.Flag.ChoralSheep.Recruited"), TEXT("Choral Sheep recruited"));
	ChoralSheepCompleted = Manager.AddNativeGameplayTag(TEXT("Melodia.Flag.ChoralSheep.Completed"), TEXT("Choral Sheep completed"));
	SeaAboveWitnessed = Manager.AddNativeGameplayTag(TEXT("Melodia.Flag.SeaAbove.Witnessed"), TEXT("Sea Above witnessed"));
	SeaAboveMembranePulseActive = Manager.AddNativeGameplayTag(TEXT("Melodia.Flag.SeaAbove.MembranePulseActive"), TEXT("Sea Above membrane pulse active"));
	SeaAboveCompleted = Manager.AddNativeGameplayTag(TEXT("Melodia.Flag.SeaAbove.Completed"), TEXT("Sea Above completed"));
}

// ── Travel Tags ──────────────────────────────────────────────────────────────

FGameplayTag FMeliaTravelTag::KaleidoNave = FGameplayTag();
FGameplayTag FMeliaTravelTag::MelusinaMorning = FGameplayTag();
FGameplayTag FMeliaTravelTag::SeaAbovePrototype = FGameplayTag();

void FMeliaTravelTag::RegisterTags()
{
	auto& Manager = UGameplayTagsManager::Get();
	KaleidoNave = Manager.AddNativeGameplayTag(TEXT("Melodia.Travel.KaleidoNave"), TEXT("Kaleido Nave"));
	MelusinaMorning = Manager.AddNativeGameplayTag(TEXT("Melodia.Travel.MelusinaMorning"), TEXT("Melusina Morning"));
	SeaAbovePrototype = Manager.AddNativeGameplayTag(TEXT("Melodia.Travel.SeaAbovePrototype"), TEXT("Sea Above Prototype"));
}

// ── Reward Tags ──────────────────────────────────────────────────────────────

FGameplayTag FMeliaRewardTag::DawnVeil = FGameplayTag();
FGameplayTag FMeliaRewardTag::DreamweaveShawl = FGameplayTag();
FGameplayTag FMeliaRewardTag::SolsticeDrum = FGameplayTag();
FGameplayTag FMeliaRewardTag::StarCharm = FGameplayTag();
FGameplayTag FMeliaRewardTag::TuningFork = FGameplayTag();
FGameplayTag FMeliaRewardTag::SmokeReward = FGameplayTag();
FGameplayTag FMeliaRewardTag::FirstResonanceEcho = FGameplayTag();
FGameplayTag FMeliaRewardTag::WardrobeFirstOutfit = FGameplayTag();
FGameplayTag FMeliaRewardTag::CompanionChoralSheep = FGameplayTag();
FGameplayTag FMeliaRewardTag::SeaAboveMemory = FGameplayTag();

void FMeliaRewardTag::RegisterTags()
{
	auto& Manager = UGameplayTagsManager::Get();
	DawnVeil = Manager.AddNativeGameplayTag(TEXT("Melodia.Reward.DawnVeil"), TEXT("Dawn Veil"));
	DreamweaveShawl = Manager.AddNativeGameplayTag(TEXT("Melodia.Reward.DreamweaveShawl"), TEXT("Dreamweave Shawl"));
	SolsticeDrum = Manager.AddNativeGameplayTag(TEXT("Melodia.Reward.SolsticeDrum"), TEXT("Solstice Drum"));
	StarCharm = Manager.AddNativeGameplayTag(TEXT("Melodia.Reward.StarCharm"), TEXT("Star Charm"));
	TuningFork = Manager.AddNativeGameplayTag(TEXT("Melodia.Reward.TuningFork"), TEXT("Tuning Fork"));
	SmokeReward = Manager.AddNativeGameplayTag(TEXT("Melodia.Reward.SmokeReward"), TEXT("Smoke Reward"));
	FirstResonanceEcho = Manager.AddNativeGameplayTag(TEXT("Melodia.Reward.FirstResonanceEcho"), TEXT("First Resonance Echo"));
	WardrobeFirstOutfit = Manager.AddNativeGameplayTag(TEXT("Melodia.Reward.WardrobeFirstOutfit"), TEXT("Wardrobe First Outfit"));
	CompanionChoralSheep = Manager.AddNativeGameplayTag(TEXT("Melodia.Reward.CompanionChoralSheep"), TEXT("Companion Choral Sheep"));
	SeaAboveMemory = Manager.AddNativeGameplayTag(TEXT("Melodia.Reward.SeaAboveMemory"), TEXT("Sea Above Memory"));
}

// ── Stat Tags ────────────────────────────────────────────────────────────────

FGameplayTag FMeliaStatTag::Harmony = FGameplayTag();
FGameplayTag FMeliaStatTag::Elegance = FGameplayTag();
FGameplayTag FMeliaStatTag::Resonance = FGameplayTag();

void FMeliaStatTag::RegisterTags()
{
	auto& Manager = UGameplayTagsManager::Get();
	Harmony = Manager.AddNativeGameplayTag(TEXT("Melodia.Stat.Harmony"), TEXT("Harmony"));
	Elegance = Manager.AddNativeGameplayTag(TEXT("Melodia.Stat.Elegance"), TEXT("Elegance"));
	Resonance = Manager.AddNativeGameplayTag(TEXT("Melodia.Stat.Resonance"), TEXT("Resonance"));
}

// ── Bond Tags ────────────────────────────────────────────────────────────────

FGameplayTag FMeliaBondTag::SirMelodious = FGameplayTag();
FGameplayTag FMeliaBondTag::TheOrrery = FGameplayTag();

void FMeliaBondTag::RegisterTags()
{
	auto& Manager = UGameplayTagsManager::Get();
	SirMelodious = Manager.AddNativeGameplayTag(TEXT("Melodia.Bond.SirMelodious"), TEXT("Sir Melodious"));
	TheOrrery = Manager.AddNativeGameplayTag(TEXT("Melodia.Bond.TheOrrery"), TEXT("The Orrery"));
}

// ── Intent Tags ──────────────────────────────────────────────────────────────

FGameplayTag FMeliaIntentTag::FirstDreamComplete = FGameplayTag();
FGameplayTag FMeliaIntentTag::WardrobeEquipComplete = FGameplayTag();
FGameplayTag FMeliaIntentTag::ChoralSheepComplete = FGameplayTag();
FGameplayTag FMeliaIntentTag::SeaAboveComplete = FGameplayTag();
FGameplayTag FMeliaIntentTag::Resonance01Complete = FGameplayTag();
FGameplayTag FMeliaIntentTag::Resonance02Complete = FGameplayTag();
FGameplayTag FMeliaIntentTag::Resonance03Complete = FGameplayTag();
FGameplayTag FMeliaIntentTag::AnchorFirstDream = FGameplayTag();
FGameplayTag FMeliaIntentTag::AnchorWardrobe = FGameplayTag();

void FMeliaIntentTag::RegisterTags()
{
	auto& Manager = UGameplayTagsManager::Get();
	FirstDreamComplete = Manager.AddNativeGameplayTag(TEXT("Melodia.Intent.FirstDream.Complete"), TEXT("First Dream completion intent"));
	WardrobeEquipComplete = Manager.AddNativeGameplayTag(TEXT("Melodia.Intent.WardrobeEquip.Complete"), TEXT("Wardrobe equip completion intent"));
	ChoralSheepComplete = Manager.AddNativeGameplayTag(TEXT("Melodia.Intent.ChoralSheep.Complete"), TEXT("Choral Sheep completion intent"));
	SeaAboveComplete = Manager.AddNativeGameplayTag(TEXT("Melodia.Intent.SeaAbove.Complete"), TEXT("Sea Above completion intent"));
	Resonance01Complete = Manager.AddNativeGameplayTag(TEXT("Melodia.Intent.Resonance01.Complete"), TEXT("Resonance 01 completion intent"));
	Resonance02Complete = Manager.AddNativeGameplayTag(TEXT("Melodia.Intent.Resonance02.Complete"), TEXT("Resonance 02 completion intent"));
	Resonance03Complete = Manager.AddNativeGameplayTag(TEXT("Melodia.Intent.Resonance03.Complete"), TEXT("Resonance 03 completion intent"));
	AnchorFirstDream = Manager.AddNativeGameplayTag(TEXT("Melodia.Intent.Anchor.FirstDream"), TEXT("First Dream state anchor intent"));
	AnchorWardrobe = Manager.AddNativeGameplayTag(TEXT("Melodia.Intent.Anchor.Wardrobe"), TEXT("Wardrobe state anchor intent"));
}

// ── State Anchor Tags ────────────────────────────────────────────────────────

FGameplayTag FMeliaStateAnchorTag::FirstDream = FGameplayTag();
FGameplayTag FMeliaStateAnchorTag::Wardrobe = FGameplayTag();
FGameplayTag FMeliaStateAnchorTag::ChoralSheep = FGameplayTag();
FGameplayTag FMeliaStateAnchorTag::SeaAbove = FGameplayTag();

void FMeliaStateAnchorTag::RegisterTags()
{
	auto& Manager = UGameplayTagsManager::Get();
	FirstDream = Manager.AddNativeGameplayTag(TEXT("Melodia.StateAnchor.FirstDream"), TEXT("First Dream state anchor"));
	Wardrobe = Manager.AddNativeGameplayTag(TEXT("Melodia.StateAnchor.Wardrobe"), TEXT("Wardrobe state anchor"));
	ChoralSheep = Manager.AddNativeGameplayTag(TEXT("Melodia.StateAnchor.ChoralSheep"), TEXT("Choral Sheep state anchor"));
	SeaAbove = Manager.AddNativeGameplayTag(TEXT("Melodia.StateAnchor.SeaAbove"), TEXT("Sea Above state anchor"));
}

// ── Checkpoint Tags ──────────────────────────────────────────────────────────

FGameplayTag FMeliaCheckpointTag::AfterBattle = FGameplayTag();
FGameplayTag FMeliaCheckpointTag::AfterDialogue = FGameplayTag();
FGameplayTag FMeliaCheckpointTag::AfterTravel = FGameplayTag();
FGameplayTag FMeliaCheckpointTag::AfterWardrobe = FGameplayTag();

void FMeliaCheckpointTag::RegisterTags()
{
	auto& Manager = UGameplayTagsManager::Get();
	AfterBattle = Manager.AddNativeGameplayTag(TEXT("Melodia.Checkpoint.AfterBattle"), TEXT("After battle checkpoint"));
	AfterDialogue = Manager.AddNativeGameplayTag(TEXT("Melodia.Checkpoint.AfterDialogue"), TEXT("After dialogue checkpoint"));
	AfterTravel = Manager.AddNativeGameplayTag(TEXT("Melodia.Checkpoint.AfterTravel"), TEXT("After travel checkpoint"));
	AfterWardrobe = Manager.AddNativeGameplayTag(TEXT("Melodia.Checkpoint.AfterWardrobe"), TEXT("After wardrobe checkpoint"));
}

// ── Spawn Tags ───────────────────────────────────────────────────────────────

FGameplayTag FMeliaSpawnTag::Default = FGameplayTag();
FGameplayTag FMeliaSpawnTag::AfterBattle = FGameplayTag();
FGameplayTag FMeliaSpawnTag::AfterTravel = FGameplayTag();
FGameplayTag FMeliaSpawnTag::Checkpoint = FGameplayTag();

void FMeliaSpawnTag::RegisterTags()
{
	auto& Manager = UGameplayTagsManager::Get();
	Default = Manager.AddNativeGameplayTag(TEXT("Melodia.Spawn.Default"), TEXT("Default spawn"));
	AfterBattle = Manager.AddNativeGameplayTag(TEXT("Melodia.Spawn.AfterBattle"), TEXT("After battle spawn"));
	AfterTravel = Manager.AddNativeGameplayTag(TEXT("Melodia.Spawn.AfterTravel"), TEXT("After travel spawn"));
	Checkpoint = Manager.AddNativeGameplayTag(TEXT("Melodia.Spawn.Checkpoint"), TEXT("Checkpoint spawn"));
}

// ── Master Registration ──────────────────────────────────────────────────────

void RegisterMelodiaGameplayTags()
{
	FMeliaWaterNetworkTag::RegisterTags();
	FMeliaWaterNodeTag::RegisterTags();
	FMeliaWaterRouteTag::RegisterTags();
	FMeliaWaterBodyTag::RegisterTags();
	FMeliaWaterPuzzleTag::RegisterTags();
	FMeliaWaterPlatformTag::RegisterTags();
	FMeliaWaterChannelTag::RegisterTags();
	FMeliaBattleEncounterTag::RegisterTags();
	FMeliaQuestTag::RegisterTags();
	FMeliaFlagTag::RegisterTags();
	FMeliaTravelTag::RegisterTags();
	FMeliaRewardTag::RegisterTags();
	FMeliaStatTag::RegisterTags();
	FMeliaBondTag::RegisterTags();
	FMeliaIntentTag::RegisterTags();
	FMeliaStateAnchorTag::RegisterTags();
	FMeliaCheckpointTag::RegisterTags();
	FMeliaSpawnTag::RegisterTags();
}
