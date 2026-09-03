#if WITH_DEV_AUTOMATION_TESTS

#include "ProceduralModelingToolkitBasicModifiers.h"
#include "ProceduralModelingToolkitModifierStack.h"
#include "ProceduralModelingToolkitPresetLibrary.h"

#include "Misc/AutomationTest.h"
#include "Misc/Paths.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FProceduralModelingToolkitPresetRoundTripTest,
	"ProceduralModelingToolkit.Presets.RoundTrip",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter
)

bool FProceduralModelingToolkitPresetRoundTripTest::RunTest(const FString& Parameters)
{
	UProceduralModelingToolkitModifierStack* Stack = NewObject<UProceduralModelingToolkitModifierStack>(GetTransientPackageAsObject(), NAME_None, RF_Transient);
	UProceduralModelingToolkitModifier* Modifier = Stack->AddModifier(UProceduralModelingToolkitTranslateModifier::StaticClass());
	TestNotNull(TEXT("Translate modifier added to preset test stack"), Modifier);
	Modifier->SetEnabled(false);

	const FString PresetName = TEXT("AutomationPresetRoundTrip.json");
	const FString DuplicateName = TEXT("AutomationPresetRoundTrip_Copy.json");

	FString SavedPath;
	FString Message;
	TestTrue(TEXT("Preset saved"), UProceduralModelingToolkitPresetLibrary::SavePreset(Stack, PresetName, SavedPath, Message));
	TestTrue(TEXT("Preset path has JSON extension"), FPaths::GetExtension(SavedPath).Equals(TEXT("json"), ESearchCase::IgnoreCase));

	UProceduralModelingToolkitModifierStack* LoadedStack = UProceduralModelingToolkitPresetLibrary::LoadPreset(SavedPath, GetTransientPackageAsObject(), Message);
	TestNotNull(TEXT("Preset loaded"), LoadedStack);
	TestEqual(TEXT("Loaded modifier count matches"), LoadedStack ? LoadedStack->Modifiers.Num() : 0, 1);
	TestFalse(TEXT("Loaded modifier enabled state preserved"), LoadedStack && LoadedStack->Modifiers[0] ? LoadedStack->Modifiers[0]->IsEnabled() : true);

	FString DuplicatePath;
	TestTrue(TEXT("Preset duplicated"), UProceduralModelingToolkitPresetLibrary::DuplicatePreset(SavedPath, DuplicateName, DuplicatePath, Message));
	TestTrue(TEXT("Duplicate deleted"), UProceduralModelingToolkitPresetLibrary::DeletePreset(DuplicatePath, Message));
	TestTrue(TEXT("Original deleted"), UProceduralModelingToolkitPresetLibrary::DeletePreset(SavedPath, Message));

	return true;
}

#endif
