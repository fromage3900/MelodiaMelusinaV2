#include "MelodiaJRPGPartyBootstrapSubsystem.h"

#include "Components/InputComponent.h"
#include "Engine/Engine.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerController.h"
#include "MelodiaPartySubsystem.h"
#include "MelodiaOpeningFlowSubsystem.h"
#include "MelodiaNarrativeSubsystem.h"
#include "InputCoreTypes.h"
#include "MelodiousFlightCharacter.h"
#include "MelodiaSmokeCharacter.h"
#include "GameFramework/PlayerInput.h"
#include "UObject/StructOnScope.h"
#include "UObject/UnrealType.h"

#if !UE_BUILD_SHIPPING
/** [Melodia DEBUG] Full Sir recruitment through the stock party (the same path the
 *  authored rescue beats drive) plus the exploration-flight unlock, so a PIE session
 *  can exercise the switch without having played the rescue beats. Never in shipping. */
static FAutoConsoleCommandWithWorld GMelodiaDebugRecruitSirFlight(
	TEXT("Melodia.Party.RecruitSirFlight"),
	TEXT("Runs the stock-party Sir recruitment and unlocks exploration flight for this session."),
	FConsoleCommandWithWorldDelegate::CreateLambda([](UWorld* World)
	{
		UGameInstance* GameInstance = World ? World->GetGameInstance() : nullptr;
		UMelodiaJRPGPartyBootstrapSubsystem* Bootstrap = GameInstance ? GameInstance->GetSubsystem<UMelodiaJRPGPartyBootstrapSubsystem>() : nullptr;
		if (!Bootstrap)
		{
			UE_LOG(LogTemp, Warning, TEXT("[Melodia DEBUG] RecruitSirFlight: no game-instance bootstrap here (%s)."),
				World ? TEXT("world has no game instance") : TEXT("no focused world"));
			return;
		}
		if (Bootstrap->RecruitSirMelodiousThroughStockParty())
		{
			UE_LOG(LogTemp, Warning, TEXT("[Melodia DEBUG] RecruitSirFlight: stock party accepted Sir; Ctrl now switches."));
		}
		else if (GameInstance->GetSubsystem<UMelodiaPartySubsystem>()
			&& GameInstance->GetSubsystem<UMelodiaPartySubsystem>()->IsSirMelodiousExplorationUnlocked())
		{
			UE_LOG(LogTemp, Warning, TEXT("[Melodia DEBUG] RecruitSirFlight: unlock already open; Ctrl now switches."));
		}
		else
		{
			UE_LOG(LogTemp, Error, TEXT("[Melodia DEBUG] RecruitSirFlight: the stock party contract refused; see the recruitment log above."));
		}
	}));
#endif

namespace
{
	constexpr TCHAR PresentationUnitClassPath[] = TEXT("/Game/Experiments/MelodiaJRPG/BP_MelusinaSwordsman_Presentation.BP_MelusinaSwordsman_Presentation_C");
	constexpr TCHAR StockSwordsmanUnitClassPath[] = TEXT("/Game/TurnBasedJRPGTemplate/Blueprints/Units/PlayerUnits/BP_SwordsmanPlayerUnit.BP_SwordsmanPlayerUnit_C");
	constexpr TCHAR SirMelodiousUnitClassPath[] = TEXT("/Game/MelodiaIntegration/Party/BP_SirMelodiousPlayerUnit.BP_SirMelodiousPlayerUnit_C");

	bool HasPlayerUnit(const APlayerController* Controller, const UClass* UnitClass)
	{
		if (!Controller || !UnitClass)
		{
			return false;
		}

		const FMapProperty* PlayerUnitsProperty = FindFProperty<FMapProperty>(Controller->GetClass(), TEXT("playerUnits"));
		const FClassProperty* KeyProperty = PlayerUnitsProperty ? CastField<FClassProperty>(PlayerUnitsProperty->KeyProp) : nullptr;
		if (!PlayerUnitsProperty || !KeyProperty)
		{
			return false;
		}

		void* MapMemory = const_cast<void*>(PlayerUnitsProperty->ContainerPtrToValuePtr<void>(Controller));
		FScriptMapHelper MapHelper(PlayerUnitsProperty, MapMemory);
		for (int32 Index = 0; Index < MapHelper.GetMaxIndex(); ++Index)
		{
			if (!MapHelper.IsValidIndex(Index))
			{
				continue;
			}

			if (Cast<UClass>(KeyProperty->GetObjectPropertyValue(MapHelper.GetKeyPtr(Index))) == UnitClass)
			{
				return true;
			}
		}
		return false;
	}

	/**
	 * Roster presence is not party membership. The stock template keeps the units
	 * you own in `playerUnits` and the units you field in `partyMembers`, and
	 * only the latter is what BP_BattleBase::SpawnPlayerUnits iterates. Probing
	 * distinguishes "not fielded" from "we could not read the contract", because
	 * reporting the second as the first is what let recruitment claim success
	 * while Sir never reached the battle.
	 */
	enum class EStockPartyMembership : uint8
	{
		Present,
		Absent,
		ContractUnreadable,
	};

	EStockPartyMembership ProbePartyMembership(const APlayerController* Controller, const UClass* UnitClass)
	{
		if (!Controller || !UnitClass)
		{
			return EStockPartyMembership::ContractUnreadable;
		}

		const FArrayProperty* PartyMembersProperty = FindFProperty<FArrayProperty>(Controller->GetClass(), TEXT("partyMembers"));
		if (!PartyMembersProperty)
		{
			UE_LOG(LogTemp, Error, TEXT("Melodia party probe found no 'partyMembers' array on '%s'."),
				*Controller->GetClass()->GetName());
			return EStockPartyMembership::ContractUnreadable;
		}

		const FClassProperty* ElementProperty = CastField<FClassProperty>(PartyMembersProperty->Inner);
		if (!ElementProperty)
		{
			// Do not guess at a struct layout. Name what was actually found so the
			// next session can widen this deliberately instead of by trial.
			UE_LOG(LogTemp, Error, TEXT("Melodia party probe expected 'partyMembers' to hold class references but found '%s'; membership cannot be confirmed."),
				*PartyMembersProperty->Inner->GetClass()->GetName());
			return EStockPartyMembership::ContractUnreadable;
		}

		void* ArrayMemory = const_cast<void*>(PartyMembersProperty->ContainerPtrToValuePtr<void>(Controller));
		FScriptArrayHelper ArrayHelper(PartyMembersProperty, ArrayMemory);
		for (int32 Index = 0; Index < ArrayHelper.Num(); ++Index)
		{
			if (Cast<UClass>(ElementProperty->GetObjectPropertyValue(ArrayHelper.GetRawPtr(Index))) == UnitClass)
			{
				return EStockPartyMembership::Present;
			}
		}
		return EStockPartyMembership::Absent;
	}

	bool FindPartyMemberIndex(const APlayerController* Controller, const UClass* UnitClass, int32& OutIndex)
	{
		OutIndex = INDEX_NONE;
		if (!Controller || !UnitClass)
		{
			return false;
		}

		const FArrayProperty* PartyMembersProperty = FindFProperty<FArrayProperty>(Controller->GetClass(), TEXT("partyMembers"));
		const FClassProperty* ElementProperty = PartyMembersProperty
			? CastField<FClassProperty>(PartyMembersProperty->Inner)
			: nullptr;
		if (!PartyMembersProperty || !ElementProperty)
		{
			return false;
		}

		void* ArrayMemory = const_cast<void*>(PartyMembersProperty->ContainerPtrToValuePtr<void>(Controller));
		FScriptArrayHelper ArrayHelper(PartyMembersProperty, ArrayMemory);
		for (int32 Index = 0; Index < ArrayHelper.Num(); ++Index)
		{
			if (Cast<UClass>(ElementProperty->GetObjectPropertyValue(ArrayHelper.GetRawPtr(Index))) == UnitClass)
			{
				OutIndex = Index;
				break;
			}
		}
		return true;
	}

	bool ReadPartyMemberAtIndex(const APlayerController* Controller, const int32 Index, UClass*& OutUnitClass)
	{
		OutUnitClass = nullptr;
		if (!Controller || Index < 0)
		{
			return false;
		}

		const FArrayProperty* PartyMembersProperty = FindFProperty<FArrayProperty>(Controller->GetClass(), TEXT("partyMembers"));
		const FClassProperty* ElementProperty = PartyMembersProperty
			? CastField<FClassProperty>(PartyMembersProperty->Inner)
			: nullptr;
		if (!PartyMembersProperty || !ElementProperty)
		{
			return false;
		}

		void* ArrayMemory = const_cast<void*>(PartyMembersProperty->ContainerPtrToValuePtr<void>(Controller));
		FScriptArrayHelper ArrayHelper(PartyMembersProperty, ArrayMemory);
		if (Index >= ArrayHelper.Num())
		{
			return false;
		}

		OutUnitClass = Cast<UClass>(ElementProperty->GetObjectPropertyValue(ArrayHelper.GetRawPtr(Index)));
		return true;
	}

	bool SwapPartyMembersThroughStockController(APlayerController* Controller, UClass* UnitClassA, UClass* UnitClassB)
	{
		if (!Controller || !UnitClassA || !UnitClassB || UnitClassA == UnitClassB)
		{
			return false;
		}

		UFunction* SwapPartyMembers = Controller->FindFunction(TEXT("SwapPartyMembers"));
		if (!SwapPartyMembers)
		{
			UE_LOG(LogTemp, Error, TEXT("Melodia party ordering found no stock 'SwapPartyMembers' function on '%s'."),
				*Controller->GetClass()->GetName());
			return false;
		}

		FClassProperty* UnitAParameter = nullptr;
		FClassProperty* UnitBParameter = nullptr;
		for (TFieldIterator<FProperty> It(SwapPartyMembers); It; ++It)
		{
			if (!It->HasAnyPropertyFlags(CPF_Parm) || It->HasAnyPropertyFlags(CPF_ReturnParm))
			{
				continue;
			}

			FClassProperty* ClassParameter = CastField<FClassProperty>(*It);
			if (!ClassParameter)
			{
				continue;
			}
			if (It->GetFName() == FName(TEXT("playerUnit1")))
			{
				UnitAParameter = ClassParameter;
			}
			else if (It->GetFName() == FName(TEXT("playerUnit2")))
			{
				UnitBParameter = ClassParameter;
			}
		}

		if (!UnitAParameter || !UnitBParameter)
		{
			UE_LOG(LogTemp, Error, TEXT("Melodia party ordering found an incompatible stock 'SwapPartyMembers' signature."));
			return false;
		}

		FStructOnScope Parameters(SwapPartyMembers);
		UnitAParameter->SetPropertyValue_InContainer(Parameters.GetStructMemory(), UnitClassA);
		UnitBParameter->SetPropertyValue_InContainer(Parameters.GetStructMemory(), UnitClassB);
		Controller->ProcessEvent(SwapPartyMembers, Parameters.GetStructMemory());
		return true;
	}

	/**
	 * Is this one of the Melodia integration's stock JRPG controllers?
	 *
	 * The presentation swap is only safe on a Melodia controller, because it
	 * rewrites the stock party roster. Matching one hardcoded class name was
	 * wrong twice over: BP_MelodiaJRPGController_Config and
	 * BP_MelodiaJRPGPlayerController are siblings under the template's
	 * BP_JRPGPlayerController, and BP_MelodiaJRPGGameMode - the project's
	 * GlobalDefaultGameMode - spawns the latter. So the check declined the live
	 * controller on every map, returned false without a word, and left the
	 * stock Swordsman in the party. Because that unit's mesh is the template's
	 * SK_Mannequin, Melusina fought bare while the fully authored
	 * BP_MelusinaSwordsman_Presentation (SK_Melusina_V2_Body/Shirt/Skirt/Boots)
	 * sat unused. Owning package is the stable identity here and survives a
	 * rename of either Blueprint.
	 */
	bool IsMelodiaIntegrationController(const APlayerController* Controller)
	{
		return Controller
			&& Controller->GetClass()->GetOutermost()->GetName().StartsWith(
				TEXT("/Game/MelodiaIntegration/"), ESearchCase::IgnoreCase);
	}

	bool AddToPartyThroughStockController(APlayerController* Controller, UClass* UnitClass)
	{
		if (!Controller || !UnitClass)
		{
			return false;
		}

		UFunction* AddToParty = Controller->FindFunction(TEXT("AddToParty"));
		if (!AddToParty)
		{
			UE_LOG(LogTemp, Error, TEXT("Melodia party fielding found no 'AddToParty' on '%s'."),
				*Controller->GetClass()->GetName());
			return false;
		}

		FClassProperty* UnitClassParameter = nullptr;
		for (TFieldIterator<FProperty> It(AddToParty); It; ++It)
		{
			if (It->HasAnyPropertyFlags(CPF_Parm) && !It->HasAnyPropertyFlags(CPF_ReturnParm))
			{
				UnitClassParameter = CastField<FClassProperty>(*It);
				break;
			}
		}
		if (!UnitClassParameter)
		{
			UE_LOG(LogTemp, Error, TEXT("Melodia party fielding found an incompatible 'AddToParty' signature; refusing to guess its parameters."));
			return false;
		}

		FStructOnScope Parameters(AddToParty);
		UnitClassParameter->SetPropertyValue_InContainer(Parameters.GetStructMemory(), UnitClass);
		Controller->ProcessEvent(AddToParty, Parameters.GetStructMemory());
		return true;
	}

	bool RemovePlayerUnitThroughStockController(APlayerController* Controller, UClass* UnitClass)
	{
		if (!Controller || !UnitClass)
		{
			return false;
		}

		UFunction* RemovePlayerUnit = Controller->FindFunction(TEXT("RemovePlayerUnit"));
		if (!RemovePlayerUnit)
		{
			return false;
		}

		FClassProperty* UnitClassParameter = nullptr;
		for (TFieldIterator<FProperty> It(RemovePlayerUnit); It; ++It)
		{
			if (It->HasAnyPropertyFlags(CPF_Parm) && !It->HasAnyPropertyFlags(CPF_ReturnParm))
			{
				UnitClassParameter = CastField<FClassProperty>(*It);
				break;
			}
		}
		if (!UnitClassParameter)
		{
			return false;
		}

		FStructOnScope Parameters(RemovePlayerUnit);
		UnitClassParameter->SetPropertyValue_InContainer(Parameters.GetStructMemory(), UnitClass);
		Controller->ProcessEvent(RemovePlayerUnit, Parameters.GetStructMemory());
		return true;
	}

	bool AddPlayerUnitThroughStockController(APlayerController* Controller, UClass* UnitClass)
	{
		if (!Controller || !UnitClass)
		{
			return false;
		}

		UFunction* AddPlayerUnit = Controller->FindFunction(TEXT("AddPlayerUnit"));
		if (!AddPlayerUnit)
		{
			return false;
		}

		FClassProperty* UnitClassParameter = nullptr;
		FIntProperty* ExperienceParameter = nullptr;
		for (TFieldIterator<FProperty> It(AddPlayerUnit); It; ++It)
		{
			if (!It->HasAnyPropertyFlags(CPF_Parm) || It->HasAnyPropertyFlags(CPF_ReturnParm))
			{
				continue;
			}
			UnitClassParameter = UnitClassParameter ? UnitClassParameter : CastField<FClassProperty>(*It);
			ExperienceParameter = ExperienceParameter ? ExperienceParameter : CastField<FIntProperty>(*It);
		}
		if (!UnitClassParameter || !ExperienceParameter)
		{
			return false;
		}

		FStructOnScope Parameters(AddPlayerUnit);
		UnitClassParameter->SetPropertyValue_InContainer(Parameters.GetStructMemory(), UnitClass);
		ExperienceParameter->SetPropertyValue_InContainer(Parameters.GetStructMemory(), 0);
		Controller->ProcessEvent(AddPlayerUnit, Parameters.GetStructMemory());
		return true;
	}
}

void UMelodiaJRPGPartyBootstrapSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);
	PostLoadMapHandle = FCoreUObjectDelegates::PostLoadMapWithWorld.AddUObject(this, &ThisClass::HandlePostLoadMap);
	WorldInitializedActorsHandle = FWorldDelegates::OnWorldInitializedActors.AddUObject(this, &ThisClass::HandleWorldInitializedActors);
	if (UGameInstance* GameInstance = GetGameInstance())
	{
		if (UMelodiaOpeningFlowSubsystem* OpeningFlow = GameInstance->GetSubsystem<UMelodiaOpeningFlowSubsystem>())
		{
			OpeningFlow->OnPhaseChanged.AddDynamic(this, &ThisClass::HandleOpeningPhaseChanged);
		}

		// Lane A4: MorningIntro's completion flag stands in for the dungeon run the
		// slice does not have. See HandleNarrativeFlagChanged.
		if (UMelodiaNarrativeSubsystem* Narrative = GameInstance->GetSubsystem<UMelodiaNarrativeSubsystem>())
		{
			Narrative->OnFlagChanged.AddDynamic(this, &ThisClass::HandleNarrativeFlagChanged);
		}
	}
}

void UMelodiaJRPGPartyBootstrapSubsystem::HandleNarrativeFlagChanged(const FName FlagId, const bool bValue)
{
	static const FName SmokeCompleteFlag(TEXT("melodia_smoke_complete"));
	if (FlagId != SmokeCompleteFlag || !bValue)
	{
		return;
	}

	UGameInstance* GameInstance = GetGameInstance();
	UMelodiaOpeningFlowSubsystem* OpeningFlow = GameInstance ? GameInstance->GetSubsystem<UMelodiaOpeningFlowSubsystem>() : nullptr;
	if (!OpeningFlow)
	{
		UE_LOG(LogTemp, Error, TEXT("MELODIA_A4 '%s' set but no opening-flow subsystem; Sir cannot be rescued."),
			*FlagId.ToString());
		return;
	}

	if (OpeningFlow->Phase == EMelodiaOpeningPhase::SirRescued
		|| OpeningFlow->Phase == EMelodiaOpeningPhase::ReturnedHome)
	{
		// Already past the transition -- recruitment has run (or will on the next
		// seed). Nothing to do, and NotifySirRescued would refuse anyway.
		return;
	}

	if (!OpeningFlow->NotifySirRescued())
	{
		// Do not fabricate the missing phases. Report exactly what blocked it so the
		// authored beat that should have advanced the flow can be found, instead of
		// leaving a rescue that quietly never happened.
		UE_LOG(LogTemp, Error, TEXT("MELODIA_A4 '%s' set, but NotifySirRescued() was refused at phase %d; it requires FirstDungeonUnlocked. Sir stays unrecruited and Ctrl-switching stays locked."),
			*FlagId.ToString(), static_cast<int32>(OpeningFlow->Phase));
		return;
	}

	UE_LOG(LogTemp, Log, TEXT("MELODIA_A4 '%s' advanced the opening flow to SirRescued; recruitment follows via OnPhaseChanged."),
		*FlagId.ToString());
}

void UMelodiaJRPGPartyBootstrapSubsystem::Deinitialize()
{
	if (PostLoadMapHandle.IsValid())
	{
		FCoreUObjectDelegates::PostLoadMapWithWorld.Remove(PostLoadMapHandle);
		PostLoadMapHandle.Reset();
	}
	if (WorldInitializedActorsHandle.IsValid())
	{
		FWorldDelegates::OnWorldInitializedActors.Remove(WorldInitializedActorsHandle);
		WorldInitializedActorsHandle.Reset();
	}
	if (UGameInstance* GameInstance = GetGameInstance())
	{
		if (UMelodiaOpeningFlowSubsystem* OpeningFlow = GameInstance->GetSubsystem<UMelodiaOpeningFlowSubsystem>())
		{
			OpeningFlow->OnPhaseChanged.RemoveDynamic(this, &ThisClass::HandleOpeningPhaseChanged);
		}

		if (UMelodiaNarrativeSubsystem* Narrative = GameInstance->GetSubsystem<UMelodiaNarrativeSubsystem>())
		{
			Narrative->OnFlagChanged.RemoveDynamic(this, &ThisClass::HandleNarrativeFlagChanged);
		}
	}
	Super::Deinitialize();
}

void UMelodiaJRPGPartyBootstrapSubsystem::HandlePostLoadMap(UWorld* LoadedWorld)
{
	QueueSeedForWorld(LoadedWorld);
}

void UMelodiaJRPGPartyBootstrapSubsystem::HandleWorldInitializedActors(const FActorsInitializedParams& Params)
{
	QueueSeedForWorld(Params.World);
}

void UMelodiaJRPGPartyBootstrapSubsystem::QueueSeedForWorld(UWorld* World)
{
	if (!World || !World->IsGameWorld() || World->GetGameInstance() != GetGameInstance())
	{
		return;
	}

	// PostLoadMap covers standalone travel; the global actors-initialized event
	// catches PIE world duplication. Its next-tick timer runs after world BeginPlay.
	// Keep one queued/successful seed per runtime world.
	if (SeededWorld.Get() == World || SeedQueuedWorld.Get() == World)
	{
		return;
	}
	bSeededForCurrentWorld = false;
	SeedQueuedWorld = World;
	World->GetTimerManager().SetTimerForNextTick(this, &ThisClass::SeedOnNextTick);
}

void UMelodiaJRPGPartyBootstrapSubsystem::SeedOnNextTick()
{
	UGameInstance* GameInstance = GetGameInstance();
	UWorld* World = GameInstance ? GameInstance->GetWorld() : nullptr;
	if (!World || SeedQueuedWorld.Get() != World)
	{
		return;
	}
	SeedQueuedWorld.Reset();
	if (TrySeedPresentationUnit())
	{
		SeededWorld = World;
	}
	TryRecruitSirMelodious();
	EnsurePartySwitchBinding();
}

void UMelodiaJRPGPartyBootstrapSubsystem::HandleOpeningPhaseChanged(const EMelodiaOpeningPhase NewPhase, const EMelodiaOpeningPhase PreviousPhase)
{
	if (NewPhase == EMelodiaOpeningPhase::SirRescued && PreviousPhase != EMelodiaOpeningPhase::SirRescued)
	{
		TryRecruitSirMelodious();
	}
}

void UMelodiaJRPGPartyBootstrapSubsystem::TryRecruitSirMelodious()
{
	if (UGameInstance* GameInstance = GetGameInstance())
	{
		if (UMelodiaOpeningFlowSubsystem* OpeningFlow = GameInstance->GetSubsystem<UMelodiaOpeningFlowSubsystem>())
		{
			if (OpeningFlow->Phase == EMelodiaOpeningPhase::SirRescued || OpeningFlow->Phase == EMelodiaOpeningPhase::ReturnedHome)
			{
				RecruitSirMelodiousThroughStockParty();
			}
		}
	}
}

bool UMelodiaJRPGPartyBootstrapSubsystem::RecruitSirMelodiousThroughStockParty()
{
	UGameInstance* GameInstance = GetGameInstance();
	UWorld* World = GameInstance ? GameInstance->GetWorld() : nullptr;
	APlayerController* Controller = World ? World->GetFirstPlayerController() : nullptr;
	UClass* SirUnitClass = LoadClass<UObject>(nullptr, SirMelodiousUnitClassPath);
	if (!Controller || !SirUnitClass)
	{
		UE_LOG(LogTemp, Warning, TEXT("Melodia Sir recruitment is waiting for the authored BP_SirMelodiousPlayerUnit asset and an active stock controller."));
		return false;
	}

	if (!HasPlayerUnit(Controller, SirUnitClass) && !AddPlayerUnitThroughStockController(Controller, SirUnitClass))
	{
		UE_LOG(LogTemp, Error, TEXT("Melodia Sir recruitment rejected by the stock AddPlayerUnit contract."));
		return false;
	}

	// AddPlayerUnit only grants ownership. Field him as well, then confirm it by
	// reading the array back -- ProcessEvent returning is not evidence of effect.
	if (ProbePartyMembership(Controller, SirUnitClass) == EStockPartyMembership::Absent)
	{
		AddToPartyThroughStockController(Controller, SirUnitClass);
	}

	const EStockPartyMembership Membership = ProbePartyMembership(Controller, SirUnitClass);
	if (Membership != EStockPartyMembership::Present)
	{
		UE_LOG(LogTemp, Error, TEXT("Melodia Sir was granted to the roster but is not in partyMembers (%s); he will not appear in battle. Exploration flight stays locked."),
			Membership == EStockPartyMembership::Absent ? TEXT("absent") : TEXT("contract unreadable"));
		return false;
	}

	if (UMelodiaPartySubsystem* ExplorationParty = GameInstance->GetSubsystem<UMelodiaPartySubsystem>())
	{
		ExplorationParty->SetSirMelodiousExplorationUnlocked(true);
	}
	UE_LOG(LogTemp, Log, TEXT("Melodia Sir recruitment accepted by stock party; exploration flight handoff unlocked."));
	return true;
}

bool UMelodiaJRPGPartyBootstrapSubsystem::TrySeedPresentationUnit()
{
	if (bSeededForCurrentWorld)
	{
		return true;
	}

	UGameInstance* GameInstance = GetGameInstance();
	UWorld* World = GameInstance ? GameInstance->GetWorld() : nullptr;
	if (!World || !World->IsGameWorld())
	{
		return false;
	}

	APlayerController* Controller = World->GetFirstPlayerController();
	if (!IsMelodiaIntegrationController(Controller))
	{
		// Never decline in silence again: a bare "return false" here is what let
		// the stock mannequin reach the battle with nobody noticing.
		UE_LOG(LogTemp, Warning,
			TEXT("Melodia JRPG party bootstrap left the stock party untouched: controller '%s' is not a Melodia integration controller, so the presentation unit was not seeded."),
			Controller ? *Controller->GetClass()->GetName() : TEXT("<none>"));
		return false;
	}

	UFunction* AddPlayerUnit = Controller->FindFunction(TEXT("AddPlayerUnit"));
	UClass* PresentationUnitClass = LoadClass<UObject>(nullptr, PresentationUnitClassPath);
	UClass* StockSwordsmanUnitClass = LoadClass<UObject>(nullptr, StockSwordsmanUnitClassPath);
	if (!AddPlayerUnit || !PresentationUnitClass || !StockSwordsmanUnitClass)
	{
		UE_LOG(LogTemp, Error, TEXT("Melodia JRPG party bootstrap could not resolve the stock party contract or required unit classes."));
		return false;
	}

	// Saved worlds and repeated map callbacks can already contain Melusina.
	// Never append a second presentation actor in that case.
	if (HasPlayerUnit(Controller, PresentationUnitClass))
	{
		bSeededForCurrentWorld = true;
		UE_LOG(LogTemp, Log, TEXT("Melodia JRPG party bootstrap found an existing Melusina presentation unit; no duplicate seed."));
		return true;
	}

	int32 OriginalStarterIndex = INDEX_NONE;
	if (!FindPartyMemberIndex(Controller, StockSwordsmanUnitClass, OriginalStarterIndex))
	{
		UE_LOG(LogTemp, Error, TEXT("Melodia JRPG party bootstrap could not read the stock party order before replacing the starter."));
		return false;
	}

	// The first slice replaces the template's starter Swordsman, rather than
	// adding a second fighter at the same battle anchor. Use the controller's
	// stock removal API so party bookkeeping remains its responsibility.
	if (HasPlayerUnit(Controller, StockSwordsmanUnitClass) && !RemovePlayerUnitThroughStockController(Controller, StockSwordsmanUnitClass))
	{
		UE_LOG(LogTemp, Error, TEXT("Melodia JRPG party bootstrap could not remove the stock Swordsman through the controller contract."));
		return false;
	}

	FClassProperty* UnitClassParameter = nullptr;
	FIntProperty* ExperienceParameter = nullptr;
	for (TFieldIterator<FProperty> It(AddPlayerUnit); It; ++It)
	{
		if (!It->HasAnyPropertyFlags(CPF_Parm) || It->HasAnyPropertyFlags(CPF_ReturnParm))
		{
			continue;
		}
		UnitClassParameter = UnitClassParameter ? UnitClassParameter : CastField<FClassProperty>(*It);
		ExperienceParameter = ExperienceParameter ? ExperienceParameter : CastField<FIntProperty>(*It);
	}
	if (!UnitClassParameter || !ExperienceParameter)
	{
		UE_LOG(LogTemp, Error, TEXT("Melodia JRPG party bootstrap found an incompatible AddPlayerUnit signature."));
		return false;
	}

	FStructOnScope Parameters(AddPlayerUnit);
	UnitClassParameter->SetPropertyValue_InContainer(Parameters.GetStructMemory(), PresentationUnitClass);
	ExperienceParameter->SetPropertyValue_InContainer(Parameters.GetStructMemory(), 0);
	Controller->ProcessEvent(AddPlayerUnit, Parameters.GetStructMemory());

	if (ProbePartyMembership(Controller, PresentationUnitClass) != EStockPartyMembership::Present)
	{
		UE_LOG(LogTemp, Error, TEXT("Melodia JRPG party bootstrap could not confirm Melusina in partyMembers after AddPlayerUnit; seed remains incomplete."));
		return false;
	}

	if (OriginalStarterIndex != INDEX_NONE)
	{
		UClass* CurrentStarterSlotClass = nullptr;
		if (!ReadPartyMemberAtIndex(Controller, OriginalStarterIndex, CurrentStarterSlotClass)
			|| !IsValid(CurrentStarterSlotClass))
		{
			UE_LOG(LogTemp, Error, TEXT("Melodia JRPG party bootstrap could not resolve the original starter slot after adding Melusina; seed remains incomplete."));
			return false;
		}

		if (CurrentStarterSlotClass != PresentationUnitClass)
		{
			if (!SwapPartyMembersThroughStockController(Controller, PresentationUnitClass, CurrentStarterSlotClass))
			{
				return false;
			}

			UClass* VerifiedStarterSlotClass = nullptr;
			if (!ReadPartyMemberAtIndex(Controller, OriginalStarterIndex, VerifiedStarterSlotClass)
				|| VerifiedStarterSlotClass != PresentationUnitClass)
			{
				UE_LOG(LogTemp, Error, TEXT("Melodia JRPG party bootstrap could not verify Melusina in the original starter slot after the stock swap; seed remains incomplete."));
				return false;
			}
		}
	}

	bSeededForCurrentWorld = true;
	UE_LOG(LogTemp, Log, TEXT("Melodia JRPG party bootstrap replaced the starter unit with Melusina through stock party contracts."));
	return true;
}

void UMelodiaJRPGPartyBootstrapSubsystem::EnsurePartySwitchBinding()
{
	UGameInstance* GameInstance = GetGameInstance();
	UWorld* World = GameInstance ? GameInstance->GetWorld() : nullptr;
	APlayerController* PC = World ? World->GetFirstPlayerController() : nullptr;
	if (!World || !World->IsGameWorld() || !PC)
	{
		return;
	}
	if (PartySwitchBoundController.Get() == PC)
	{
		return;
	}

	// Register the action mapping once (idempotent by name + key): duplicates
	// would fire the action twice per press and double-hop the switch.
	if (PC->PlayerInput)
	{
		bool bMappingExists = false;
		for (const FInputActionKeyMapping& Mapping : PC->PlayerInput->ActionKeyMappings)
		{
			if (Mapping.ActionName == FName("MelodiaPartySwitch") && Mapping.Key == EKeys::LeftControl)
			{
				bMappingExists = true;
				break;
			}
		}
		if (!bMappingExists)
		{
			PC->PlayerInput->AddActionMapping(FInputActionKeyMapping(FName("MelodiaPartySwitch"), EKeys::LeftControl));
		}
	}
	else
	{
		UE_LOG(LogTemp, Warning, TEXT("Melodia party switch mapping not registered: controller has no PlayerInput."));
	}

	// Every possess swing names itself in the log. If something later wipes a
	// binding or yanks possession during the intro, the sequence is visible by
	// name instead of being reconstructed from silence.
	PC->OnNewPawn.AddUObject(this, &UMelodiaJRPGPartyBootstrapSubsystem::OnControllerPawnChanged);

	// Bind on the controller's InputComponent, never the pawn's. A pawn
	// InputComponent's bindings do not survive a possess swing; the
	// controller's component is pushed for every frame of play and holds.
	if (UInputComponent* PCInput = PC->InputComponent)
	{
		PCInput->BindAction(FName("MelodiaPartySwitch"), IE_Pressed, this, &UMelodiaJRPGPartyBootstrapSubsystem::HandlePartySwitchKey);
		PartySwitchBoundController = PC;
		UE_LOG(LogTemp, Log, TEXT("Melodia party switch bound: LeftControl -> SwitchToNext on controller %s (possess-safe)."), *PC->GetName());
	}
	else
	{
		// No controller InputComponent yet (before first possession). The
		// possess event above re-runs this function, which binds then.
		UE_LOG(LogTemp, Log, TEXT("Melodia party switch deferring bind: controller %s has no InputComponent yet."), *PC->GetName());
	}
}

void UMelodiaJRPGPartyBootstrapSubsystem::OnControllerPawnChanged(APawn* NewPawn)
{
	UE_LOG(LogTemp, Log, TEXT("Melodia possess swing: controller %s now holds %s."),
		*GetNameSafe(this), NewPawn ? *NewPawn->GetName() : TEXT("nothing"));
	EnsurePartySwitchBinding();
}

void UMelodiaJRPGPartyBootstrapSubsystem::HandlePartySwitchKey()
{
	UGameInstance* GameInstance = GetGameInstance();
	UWorld* World = GameInstance ? GameInstance->GetWorld() : nullptr;
	APlayerController* PC = World ? World->GetFirstPlayerController() : nullptr;
	UMelodiaPartySubsystem* Party = GameInstance ? GameInstance->GetSubsystem<UMelodiaPartySubsystem>() : nullptr;
	if (!PC || !Party)
	{
		return;
	}
	UE_LOG(LogTemp, Log, TEXT("Melodia party switch key received: active_index=%d sir_unlocked=%d."),
		Party->ActiveIndex, Party->IsSirMelodiousExplorationUnlocked() ? 1 : 0);
	// While the flight pawn (index 1) is possessed, its own binding owns Ctrl;
	// skipping here prevents a double SwitchToNext (a silent hop-and-hop-back).
	if (Party->ActiveIndex != 0)
	{
		return;
	}
	Party->SwitchToNext(PC);
}
