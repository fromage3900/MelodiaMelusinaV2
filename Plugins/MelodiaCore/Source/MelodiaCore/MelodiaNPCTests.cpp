#if WITH_DEV_AUTOMATION_TESTS
#include "MelodiaNPCData.h"
#include "Misc/AutomationTest.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMelodiaNPCDefinitionContractTest, "Melodia.NPC.DefinitionContract", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMelodiaNPCDefinitionContractTest::RunTest(const FString& Parameters)
{
	FMelodiaNPCDef Empty;
	TestFalse(TEXT("Unset definition is rejected"), Empty.IsValid());

	FMelodiaNPCDef Valid;
	Valid.NPCId = TEXT("NPC_TestGuide");
	Valid.DisplayName = FText::FromString(TEXT("Test Guide"));
	Valid.Role = EMelodiaNPCRole::Quest;
	Valid.StaticMesh = TSoftObjectPtr<UStaticMesh>(FSoftObjectPath(TEXT("/Game/Test/SM_NPCPlaceholder.SM_NPCPlaceholder")));
	Valid.DialogueKeys = { TEXT("SirEntry_003") };
	TestTrue(TEXT("Minimal definition is accepted without loading soft assets"), Valid.IsValid());

	UMelodiaNPCDefinitionAsset* Asset = NewObject<UMelodiaNPCDefinitionAsset>();
	Asset->Definition = Valid;
	TestEqual(TEXT("Stable primary type"), Asset->GetPrimaryAssetId().PrimaryAssetType, FPrimaryAssetType(TEXT("MelodiaNPC")));
	TestEqual(TEXT("Stable primary name derives from NPCId"), Asset->GetPrimaryAssetId().PrimaryAssetName, Valid.NPCId);
	return true;
}
#endif