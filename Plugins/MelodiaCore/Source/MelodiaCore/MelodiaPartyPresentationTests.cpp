// Regression cover for the party presentation swap.
//
// Symptom this pins down: in battle Melusina appeared as the stock
// SK_Mannequin, i.e. naked. The cause was not an art problem - the dressed unit
// (BP_MelusinaSwordsman_Presentation, carrying SK_Melusina_V2_Body/Shirt/Skirt/
// Boots) was fully authored and referenced. UMelodiaJRPGPartyBootstrapSubsystem
// is supposed to remove the stock BP_SwordsmanPlayerUnit and field the
// presentation unit instead, but it gated that swap on a single hardcoded
// controller class name (BP_MelodiaJRPGController_Config_C) while
// BP_MelodiaJRPGGameMode - the GlobalDefaultGameMode - spawns the sibling
// BP_MelodiaJRPGPlayerController. The gate declined on every map and returned
// false without logging, so the mannequin stayed in the party.
//
// The test asserts the OUTCOME on the live stock controller, not the
// implementation, so any future re-gating mistake fails here too. It runs in PIE
// because the swap is seeded from PostLoadMap on a game world.
//
// It lives in MelodiaCore because this is where the PIE automation harness
// already is; the assertion is entirely on stock-template controller state, so
// it does not need the game module.

#if WITH_DEV_AUTOMATION_TESTS && WITH_EDITOR

#include "Tests/AutomationEditorCommon.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "GameFramework/PlayerController.h"
#include "Misc/AutomationTest.h"
#include "UObject/UnrealType.h"

namespace
{
	constexpr TCHAR PresentationUnitPath[] = TEXT("/Game/Experiments/MelodiaJRPG/BP_MelusinaSwordsman_Presentation.BP_MelusinaSwordsman_Presentation_C");
	constexpr TCHAR StockSwordsmanPath[] = TEXT("/Game/TurnBasedJRPGTemplate/Blueprints/Units/PlayerUnits/BP_SwordsmanPlayerUnit.BP_SwordsmanPlayerUnit_C");

	UWorld* FindPIEWorld()
	{
		if (!GEngine)
		{
			return nullptr;
		}
		for (const FWorldContext& Context : GEngine->GetWorldContexts())
		{
			if (Context.WorldType == EWorldType::PIE)
			{
				return Context.World();
			}
		}
		return nullptr;
	}

	/** Read the stock controller's fielded roster; presence, not ownership. */
	bool PartyContains(const APlayerController* Controller, UClass* UnitClass)
	{
		if (!Controller || !UnitClass)
		{
			return false;
		}
		const FArrayProperty* PartyMembers = FindFProperty<FArrayProperty>(Controller->GetClass(), TEXT("partyMembers"));
		if (!PartyMembers)
		{
			return false;
		}
		const FClassProperty* Element = CastField<FClassProperty>(PartyMembers->Inner);
		if (!Element)
		{
			return false;
		}
		void* ArrayMemory = const_cast<void*>(PartyMembers->ContainerPtrToValuePtr<void>(Controller));
		FScriptArrayHelper Helper(PartyMembers, ArrayMemory);
		for (int32 Index = 0; Index < Helper.Num(); ++Index)
		{
			if (Cast<UClass>(Element->GetObjectPropertyValue(Helper.GetRawPtr(Index))) == UnitClass)
			{
				return true;
			}
		}
		return false;
	}

	class FMelodiaPartyPresentationCommand final : public IAutomationLatentCommand
	{
	public:
		explicit FMelodiaPartyPresentationCommand(FAutomationTestBase* InTest)
			: Test(InTest)
			, StartedAt(FPlatformTime::Seconds())
		{
		}

		virtual bool Update() override
		{
			UWorld* World = FindPIEWorld();
			if (!World)
			{
				return false;
			}

			APlayerController* Controller = World->GetFirstPlayerController();
			if (!Controller)
			{
				return false;
			}

			UClass* PresentationUnit = LoadClass<UObject>(nullptr, PresentationUnitPath);
			UClass* StockSwordsman = LoadClass<UObject>(nullptr, StockSwordsmanPath);
			if (!Test->TestNotNull(TEXT("The dressed Melusina presentation unit exists"), PresentationUnit)
				|| !Test->TestNotNull(TEXT("The stock Swordsman unit exists"), StockSwordsman))
			{
				return true;
			}

			// The swap is seeded from PostLoadMap via a next-tick timer, so give
			// it a moment before declaring the roster wrong.
			if (!PartyContains(Controller, PresentationUnit)
				&& FPlatformTime::Seconds() - StartedAt < 10.0)
			{
				return false;
			}

			Test->TestTrue(TEXT("Melusina fields her dressed presentation unit in battle"),
				PartyContains(Controller, PresentationUnit));
			Test->TestFalse(TEXT("The stock mannequin Swordsman is not fielded alongside her"),
				PartyContains(Controller, StockSwordsman));
			return true;
		}

	private:
		FAutomationTestBase* Test = nullptr;
		double StartedAt = 0.0;
	};
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMelodiaPartyPresentationTest,
	"Melodia.Integration.Functional.PartyPresentationUnit",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMelodiaPartyPresentationTest::RunTest(const FString& Parameters)
{
	ADD_LATENT_AUTOMATION_COMMAND(FEditorLoadMap(TEXT("/Game/ZenForestTest")));
	ADD_LATENT_AUTOMATION_COMMAND(FStartPIECommand(false));
	ADD_LATENT_AUTOMATION_COMMAND(FMelodiaPartyPresentationCommand(this));
	ADD_LATENT_AUTOMATION_COMMAND(FEndPlayMapCommand());
	return true;
}

#endif
