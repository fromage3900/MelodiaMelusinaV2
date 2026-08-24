#if WITH_DEV_AUTOMATION_TESTS

#include "MelodiaCompanionComponent.h"
#include "MelodiaCompanionData.h"
#include "MelodiaResonanceGardenData.h"
#include "Misc/AutomationTest.h"

namespace
{
	FMelodiaCompanionDefinition MakeValidChoralSheepDefinition()
	{
		FMelodiaCompanionDefinition Definition;
		Definition.CompanionId = FName(TEXT("ChoralSheep"));
		Definition.NPCDefinition.NPCId = Definition.CompanionId;
		Definition.NPCDefinition.DisplayName = Definition.DisplayName;
		Definition.NPCDefinition.Role = EMelodiaNPCRole::Companion;
		Definition.NPCDefinition.BehaviorTag = FName(TEXT("NonCombatExplorationCompanion"));
		Definition.NPCDefinition.SkeletalMesh = TSoftObjectPtr<USkeletalMesh>(FSoftObjectPath(TEXT("/Game/Melodia/Companions/ChoralSheep/SK_ChoralSheep")));
		Definition.MusicalMotif = FName(TEXT("choral_wool"));
		Definition.SupportedInteractions = {
			EMelodiaCompanionInteractionKind::Graze,
			EMelodiaCompanionInteractionKind::Harmonize,
			EMelodiaCompanionInteractionKind::Guide
		};
		Definition.HabitatTags = { FName(TEXT("SakuraGrove")), FName(TEXT("ResonanceGarden")) };
		return Definition;
	}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMelodiaResonanceGardenStyleGenomeTest, "Melodia.ResonanceGarden.StyleGenome", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMelodiaResonanceGardenStyleGenomeTest::RunTest(const FString& Parameters)
{
	FMelodiaStyleGenome Genome;
	FText Error;

	TestTrue(TEXT("Default Resonance Garden genome validates"), Genome.IsValid(&Error));
	TestTrue(TEXT("Default genome has a stable identity"), Genome.GenomeId == FName(TEXT("ResonanceGarden")));
	TestTrue(TEXT("Default genome uses the current universal material family"), Genome.MaterialFamily == FName(TEXT("M_Master_Toon_Universal")));
	TestTrue(TEXT("Validation error remains empty for valid data"), Error.IsEmpty());

	Genome.Sheen = 1.5f;
	TestFalse(TEXT("Out-of-range sheen is rejected"), Genome.IsValid(&Error));
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMelodiaResonanceGardenFurLodTest, "Melodia.ResonanceGarden.FurLOD", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMelodiaResonanceGardenFurLodTest::RunTest(const FString& Parameters)
{
	const FMelodiaFurProfile Profile;

	TestTrue(TEXT("Fur defaults validate"), Profile.IsValid());
	TestEqual(TEXT("Hero distance selects Native Groom"), UMelodiaFurLibrary::SelectBackendForDistance(Profile, 0.0f), EMelodiaFurBackendKind::NativeGroom);
	TestEqual(TEXT("Hero upper boundary remains Native Groom"), UMelodiaFurLibrary::SelectBackendForDistance(Profile, 399.9f), EMelodiaFurBackendKind::NativeGroom);
	TestEqual(TEXT("Mid distance selects Shell/Card"), UMelodiaFurLibrary::SelectBackendForDistance(Profile, 400.0f), EMelodiaFurBackendKind::ShellCard);
	TestEqual(TEXT("Far distance selects Impostor"), UMelodiaFurLibrary::SelectBackendForDistance(Profile, 1200.0f), EMelodiaFurBackendKind::Impostor);
	TestEqual(TEXT("Negative distance clamps to hero"), UMelodiaFurLibrary::SelectBackendForDistance(Profile, -10.0f), EMelodiaFurBackendKind::NativeGroom);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMelodiaChoralSheepDefinitionTest, "Melodia.ResonanceGarden.ChoralSheepDefinition", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMelodiaChoralSheepDefinitionTest::RunTest(const FString& Parameters)
{
	FMelodiaCompanionDefinition Definition = MakeValidChoralSheepDefinition();
	FText Error;

	TestTrue(TEXT("Choral Sheep definition validates"), Definition.IsValid(&Error));
	TestTrue(TEXT("Choral Sheep keeps an identity mesh path"), Definition.NPCDefinition.SkeletalMesh.ToSoftObjectPath() == FSoftObjectPath(TEXT("/Game/Melodia/Companions/ChoralSheep/SK_ChoralSheep")));
	TestTrue(TEXT("Choral Sheep uses an identity presentation transform by default"), Definition.MeshRelativeTransform.Equals(FTransform::Identity));
	TestTrue(TEXT("Choral Sheep remains noncombat"), Definition.bNonCombat);
	TestTrue(TEXT("Choral Sheep supports grazing"), Definition.SupportedInteractions.Contains(EMelodiaCompanionInteractionKind::Graze));
	TestTrue(TEXT("Choral Sheep supports harmonize"), Definition.SupportedInteractions.Contains(EMelodiaCompanionInteractionKind::Harmonize));
	TestTrue(TEXT("Choral Sheep supports guidance"), Definition.SupportedInteractions.Contains(EMelodiaCompanionInteractionKind::Guide));

	Definition.WardrobeProfile.PreferredCosmeticIds.Add(FName(TEXT("Cos_ChoralSheep_Wool")));
	Error = FText::GetEmpty();
	TestTrue(TEXT("Optional companion wardrobe profile validates when authored"), Definition.IsValid(&Error));
	TestTrue(TEXT("Optional wardrobe profile keeps the companion identity"), Definition.WardrobeProfile.ProfileId == FName(TEXT("ChoralSheep")));

	Definition.WardrobeProfile.bAllowPrototypeGrant = true;
	Error = FText::GetEmpty();
	TestFalse(TEXT("Companion wardrobe prototype grants fail closed without a receipt"), Definition.IsValid(&Error));

	Definition.NPCDefinition.Role = EMelodiaNPCRole::Ambient;
	TestFalse(TEXT("Non-companion NPC role is rejected"), Definition.IsValid(&Error));

	Definition = MakeValidChoralSheepDefinition();
	Definition.NPCDefinition.SkeletalMesh.Reset();
	Definition.NPCDefinition.StaticMesh = TSoftObjectPtr<UStaticMesh>(FSoftObjectPath(TEXT("/Game/Melodia/Companions/ChoralSheep/SM_ChoralSheepPlaceholder")));
	Error = FText::GetEmpty();
	TestFalse(TEXT("Static-only companion presentation is rejected"), Definition.IsValid(&Error));
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMelodiaCompanionComponentStateTest, "Melodia.ResonanceGarden.CompanionState", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMelodiaCompanionComponentStateTest::RunTest(const FString& Parameters)
{
	UMelodiaCompanionDefinitionAsset* Asset = NewObject<UMelodiaCompanionDefinitionAsset>();
	Asset->Definition = MakeValidChoralSheepDefinition();

	UMelodiaCompanionComponent* Component = NewObject<UMelodiaCompanionComponent>();
	TestTrue(TEXT("Component accepts valid Choral Sheep definition"), Component->SetCompanionDefinition(Asset));
	TestTrue(TEXT("Component exposes grazing interaction"), Component->SupportsInteraction(EMelodiaCompanionInteractionKind::Graze));
	TestTrue(TEXT("Component exposes harmonize interaction"), Component->SupportsInteraction(EMelodiaCompanionInteractionKind::Harmonize));
	TestFalse(TEXT("Follow requires an explicit target"), Component->RequestState(EMelodiaCompanionBehaviorState::Follow));
	TestTrue(TEXT("Idle state is deterministic without a target"), Component->RequestState(EMelodiaCompanionBehaviorState::Idle));
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMelodiaCompanionPrimaryAssetIdsTest, "Melodia.ResonanceGarden.PrimaryAssetIds", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMelodiaCompanionPrimaryAssetIdsTest::RunTest(const FString& Parameters)
{
	UMelodiaStyleGenomeAsset* StyleAsset = NewObject<UMelodiaStyleGenomeAsset>();
	StyleAsset->Genome.GenomeId = FName(TEXT("ResonanceGarden"));
	TestEqual(TEXT("Style genome primary asset type is stable"), StyleAsset->GetPrimaryAssetId().PrimaryAssetType, FPrimaryAssetType(TEXT("MelodiaStyleGenome")));
	TestEqual(TEXT("Style genome primary asset name is stable"), StyleAsset->GetPrimaryAssetId().PrimaryAssetName, FName(TEXT("ResonanceGarden")));

	UMelodiaCompanionDefinitionAsset* CompanionAsset = NewObject<UMelodiaCompanionDefinitionAsset>();
	CompanionAsset->Definition = MakeValidChoralSheepDefinition();
	TestEqual(TEXT("Companion primary asset type is stable"), CompanionAsset->GetPrimaryAssetId().PrimaryAssetType, FPrimaryAssetType(TEXT("MelodiaCompanion")));
	TestEqual(TEXT("Companion primary asset name is stable"), CompanionAsset->GetPrimaryAssetId().PrimaryAssetName, FName(TEXT("ChoralSheep")));
	return true;
}

#endif
