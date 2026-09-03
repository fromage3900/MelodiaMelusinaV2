#if WITH_DEV_AUTOMATION_TESTS

#include "MelodiaCompanionWardrobeBridge.h"
#include "MelodiaWardrobeComponent.h"
#include "Components/SceneComponent.h"
#include "Misc/AutomationTest.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FMelodiaCompanionWardrobeProfileValidationTest,
	"Melodia.Wardrobe.Companion.ProfileValidation",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMelodiaCompanionWardrobeProfileValidationTest::RunTest(const FString& Parameters)
{
	FMelodiaCompanionWardrobeProfile Profile;
	FText Error;

	TestFalse(TEXT("Empty profile fails closed"), Profile.IsValid(&Error));
	TestFalse(TEXT("Empty profile reports a validation error"), Error.IsEmpty());

	Profile.PreferredCosmeticIds.Add(FName(TEXT("Cos_ChoralSheep_Wool")));
	Error = FText::GetEmpty();
	TestTrue(TEXT("Owned-only profile validates"), Profile.IsValid(&Error));
	TestTrue(TEXT("Owned-only profile has no validation error"), Error.IsEmpty());

	Profile.bAllowPrototypeGrant = true;
	Error = FText::GetEmpty();
	TestFalse(TEXT("Prototype grant requires explicit grant fields"), Profile.IsValid(&Error));

	Profile.PrototypeGrantCosmeticId = FName(TEXT("Cos_ChoralSheep_Wool"));
	Profile.PrototypeGrantId = FName(TEXT("ChoralSheep_Prototype_01"));
	Error = FText::GetEmpty();
	TestTrue(TEXT("Explicit prototype grant profile validates"), Profile.IsValid(&Error));
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
	FMelodiaCompanionWardrobeBridgeFailClosedTest,
	"Melodia.Wardrobe.Companion.BridgeFailsClosed",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMelodiaCompanionWardrobeBridgeFailClosedTest::RunTest(const FString& Parameters)
{
	UMelodiaCompanionWardrobeBridge* Bridge = NewObject<UMelodiaCompanionWardrobeBridge>();
	FMelodiaCompanionWardrobeProfile Profile;
	Profile.PreferredCosmeticIds.Add(FName(TEXT("Cos_ChoralSheep_Wool")));

	TestFalse(
		TEXT("Bridge does not accept an arbitrary provider"),
		Bridge->SetWardrobeProvider(NewObject<USceneComponent>()));
	TestEqual(
		TEXT("Request without a wardrobe provider is rejected"),
		Bridge->RequestPresentationWithProfile(Profile),
		EMelodiaCompanionWardrobeRequestResult::RejectedNoWardrobeProvider);
	return true;
}

#endif
