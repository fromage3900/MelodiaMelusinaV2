#if WITH_DEV_AUTOMATION_TESTS

#include "Misc/AutomationTest.h"
#include "../MelodiaInputContextSubsystem.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMelodiaCursorPrecedenceTest,
	"Melodia.Cursor.StatePrecedence", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMelodiaCursorPrecedenceTest::RunTest(const FString&)
{
	const FMelodiaCursorVisualState Forbidden = UMelodiaInputContextSubsystem::ResolveCursorVisualState(
		EMelodiaInputContext::Battle, EMelodiaCursorRole::SlashedCircle, true, EMelodiaCursorDevice::MouseAndKeyboard, false);
	TestEqual(TEXT("Forbidden overrides pressed"), Forbidden.EffectiveRole, EMelodiaCursorRole::SlashedCircle);

	const FMelodiaCursorVisualState Pressed = UMelodiaInputContextSubsystem::ResolveCursorVisualState(
		EMelodiaInputContext::Dialogue, EMelodiaCursorRole::Hand, true, EMelodiaCursorDevice::MouseAndKeyboard, false);
	TestEqual(TEXT("Pressed overrides hover"), Pressed.EffectiveRole, EMelodiaCursorRole::Crosshairs);
	TestEqual(TEXT("Dialogue supplies theme"), Pressed.ContextTheme, EMelodiaInputContext::Dialogue);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMelodiaCursorAdaptiveVisibilityTest,
	"Melodia.Cursor.AdaptiveVisibility", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMelodiaCursorAdaptiveVisibilityTest::RunTest(const FString&)
{
	TestFalse(TEXT("Cinematic hides cursor"), UMelodiaInputContextSubsystem::ResolveCursorVisualState(
		EMelodiaInputContext::Cinematic, EMelodiaCursorRole::Default, false, EMelodiaCursorDevice::MouseAndKeyboard, false).bVisible);
	TestFalse(TEXT("Gamepad hides cursor"), UMelodiaInputContextSubsystem::ResolveCursorVisualState(
		EMelodiaInputContext::Menu, EMelodiaCursorRole::Default, false, EMelodiaCursorDevice::Gamepad, false).bVisible);
	TestFalse(TEXT("Touch-only hides cursor"), UMelodiaInputContextSubsystem::ResolveCursorVisualState(
		EMelodiaInputContext::Exploration, EMelodiaCursorRole::Default, false, EMelodiaCursorDevice::MouseAndKeyboard, true).bVisible);
	TestTrue(TEXT("Mouse restores outside cinematics"), UMelodiaInputContextSubsystem::ResolveCursorVisualState(
		EMelodiaInputContext::Rhythm, EMelodiaCursorRole::Default, false, EMelodiaCursorDevice::MouseAndKeyboard, false).bVisible);
	return true;
}

#endif
