#include "MelodiaStockContract.h"

#include "HAL/IConsoleManager.h"
#include "UObject/Class.h"
#include "UObject/UObjectGlobals.h"
#include "UObject/UnrealType.h"

namespace
{
	constexpr const TCHAR* BattleUIPath        = TEXT("/Game/TurnBasedJRPGTemplate/Blueprints/UI/BP_BattleUI.BP_BattleUI_C");
	constexpr const TCHAR* BattleControllerPath= TEXT("/Game/TurnBasedJRPGTemplate/Blueprints/Battle/BP_BattleController.BP_BattleController_C");
	constexpr const TCHAR* BattleBasePath      = TEXT("/Game/TurnBasedJRPGTemplate/Blueprints/Battle/BP_BattleBase.BP_BattleBase_C");
	constexpr const TCHAR* UnitBasePath        = TEXT("/Game/TurnBasedJRPGTemplate/Blueprints/Units/BP_UnitBase.BP_UnitBase_C");
	constexpr const TCHAR* PlayerUnitBasePath  = TEXT("/Game/TurnBasedJRPGTemplate/Blueprints/Units/PlayerUnits/BP_PlayerUnitBase.BP_PlayerUnitBase_C");

	// EVERY entry below was read back out of the live graph on 2026-08-09 before
	// being added. That restraint is the point: a manifest entry asserted from a
	// doc, a name table, or a memory of how the template works produces a RED
	// report for a seam that was never broken -- and a gate that cries wolf gets
	// muted, which is strictly worse than having no gate at all.
	//
	// DELIBERATELY NOT LISTED YET -- these are real seams C++ depends on, but
	// their owning class or member kind has NOT been confirmed against the graph.
	// Add each one only after reading it in the editor, never from a doc:
	//
	//   BP_JRPGPlayerController : playerUnits, partyMembers, partySize,
	//                             AddPlayerUnit, RemovePlayerUnit, AddToParty,
	//                             AddEquipmentToInventory, WearEquipmentOnUnit
	//   <tagged encounter actor> : StartBattle, offLevelBattleData
	//   BP_JRPGSaveGame          : melodiaNarrativeRecord, currentMap
	//   BP_MelodiaJRPGGameInstance : slotName, jRPGSaveGame, LoadThisGame
	//   BP_MelodiaBattleUI       : ShowRhythmGrade
	//   BP_BattleSkillBase       : UseSkill
	//
	// The party ones matter most: MelodiaJRPGPartyBootstrapSubsystem reads
	// partyMembers as an array of class references, and that assumption is
	// currently UNVERIFIED. Confirm it, then add it here.
	const FMelodiaStockSeam GStockSeams[] =
	{
		// --- The battle-UI controller reference -------------------------------
		// Four readers, zero writers as of 2026-08-09. The property being PRESENT
		// is what this asserts; that something writes it is a separate problem.
		{ BattleUIPath, TEXT("battleController"), EMelodiaStockSeamKind::ObjectProperty,
		  TEXT("MelodiaUIBridgeSubsystem::EnsureStockBattleUIControllerReference") },
		{ BattleUIPath, TEXT("ShowBattleUI"), EMelodiaStockSeamKind::Function,
		  TEXT("BP_BattleController exec chain; unshadowed 2026-08-08") },

		// --- Battle controller / battle actor ---------------------------------
		{ BattleControllerPath, TEXT("currentTargetUnit"), EMelodiaStockSeamKind::ObjectProperty,
		  TEXT("BP_FocusAttack MoveToTarget; skill targeting") },
		{ BattleBasePath, TEXT("InitBattle"), EMelodiaStockSeamKind::Function,
		  TEXT("battle entry point") },
		{ BattleBasePath, TEXT("OnBattleOver"), EMelodiaStockSeamKind::MulticastDelegate,
		  TEXT("MelodiaExternalJRPGBridgeSubsystem::HandleBattleOver") },
		{ BattleBasePath, TEXT("GetOffLevelBattleData"), EMelodiaStockSeamKind::Function,
		  TEXT("MelodiaExternalJRPGBridgeSubsystem battle handoff") },

		// --- Unit state the co-op skill pair depends on -----------------------
		{ UnitBasePath, TEXT("activeBuffs"), EMelodiaStockSeamKind::MapProperty,
		  TEXT("Resonance apply/consume; COOP_SKILL_RESONANCE_SPEC") },
		{ UnitBasePath, TEXT("currentTarget"), EMelodiaStockSeamKind::ObjectProperty,
		  TEXT("BP_PlayerUnitBase FocusOnTarget / SetTargetIconVisibility") },
		{ UnitBasePath, TEXT("battleController"), EMelodiaStockSeamKind::ObjectProperty,
		  TEXT("BP_UnitBase InitUnit") },

		// --- Skill availability ------------------------------------------------
		// battleSkills maps skill class -> REQUIRED LEVEL, filtered into
		// availableBattleSkills by SetBattleSkills via requiredLevel <= level.
		{ PlayerUnitBasePath, TEXT("battleSkills"), EMelodiaStockSeamKind::MapProperty,
		  TEXT("skill gating; Melusina level-1 fix 2026-08-09") },
		{ PlayerUnitBasePath, TEXT("availableBattleSkills"), EMelodiaStockSeamKind::ArrayProperty,
		  TEXT("BP_BattleUI ShowSkills source") },
		{ PlayerUnitBasePath, TEXT("SetBattleSkills"), EMelodiaStockSeamKind::Function,
		  TEXT("builds availableBattleSkills from battleSkills") },
	};

	bool MemberMatchesKind(const UClass* Class, const TCHAR* MemberName, const EMelodiaStockSeamKind Kind, FString& OutFoundKind, bool& bOutMemberResolved)
	{
		bOutMemberResolved = false;
		OutFoundKind.Reset();

		if (Kind == EMelodiaStockSeamKind::Function)
		{
			if (const UFunction* Function = Class->FindFunctionByName(FName(MemberName)))
			{
				bOutMemberResolved = true;
				OutFoundKind = TEXT("Function");
				return true;
			}
			// A member of this name may still exist as a property -- say so, because
			// "renamed to a variable" is a different repair from "deleted".
			if (const FProperty* AsProperty = FindFProperty<FProperty>(Class, MemberName))
			{
				bOutMemberResolved = true;
				OutFoundKind = AsProperty->GetClass()->GetName();
				return false;
			}
			return false;
		}

		const FProperty* Property = FindFProperty<FProperty>(Class, MemberName);
		if (!Property)
		{
			if (Class->FindFunctionByName(FName(MemberName)))
			{
				bOutMemberResolved = true;
				OutFoundKind = TEXT("Function");
			}
			return false;
		}

		bOutMemberResolved = true;
		OutFoundKind = Property->GetClass()->GetName();

		switch (Kind)
		{
		case EMelodiaStockSeamKind::ObjectProperty:     return CastField<FObjectPropertyBase>(Property) != nullptr;
		case EMelodiaStockSeamKind::StructProperty:     return CastField<FStructProperty>(Property) != nullptr;
		case EMelodiaStockSeamKind::ArrayProperty:      return CastField<FArrayProperty>(Property) != nullptr;
		case EMelodiaStockSeamKind::MapProperty:        return CastField<FMapProperty>(Property) != nullptr;
		case EMelodiaStockSeamKind::MulticastDelegate:  return CastField<FMulticastDelegateProperty>(Property) != nullptr;
		default:                                        return false;
		}
	}
}

const TCHAR* FMelodiaStockContract::LexToString(const EMelodiaStockSeamKind Kind)
{
	switch (Kind)
	{
	case EMelodiaStockSeamKind::Function:          return TEXT("Function");
	case EMelodiaStockSeamKind::ObjectProperty:    return TEXT("ObjectProperty");
	case EMelodiaStockSeamKind::StructProperty:    return TEXT("StructProperty");
	case EMelodiaStockSeamKind::ArrayProperty:     return TEXT("ArrayProperty");
	case EMelodiaStockSeamKind::MapProperty:       return TEXT("MapProperty");
	case EMelodiaStockSeamKind::MulticastDelegate: return TEXT("MulticastDelegate");
	default:                                       return TEXT("Unknown");
	}
}

FString FMelodiaStockSeamResult::Describe() const
{
	if (!bClassResolved)
	{
		return FString::Printf(TEXT("MELODIA_CONTRACT BROKEN class-not-found '%s' (needed by %s)"), *ClassPath, *UsedBy);
	}
	if (!bMemberResolved)
	{
		return FString::Printf(TEXT("MELODIA_CONTRACT BROKEN member-not-found '%s' on '%s' (needed by %s)"), *MemberName, *ClassPath, *UsedBy);
	}
	if (!bKindMatched)
	{
		return FString::Printf(TEXT("MELODIA_CONTRACT BROKEN kind-mismatch '%s' on '%s' is '%s' (needed by %s)"), *MemberName, *ClassPath, *FoundKind, *UsedBy);
	}
	return FString::Printf(TEXT("MELODIA_CONTRACT ok '%s' on '%s'"), *MemberName, *ClassPath);
}

TArrayView<const FMelodiaStockSeam> FMelodiaStockContract::GetSeams()
{
	return MakeArrayView(GStockSeams, UE_ARRAY_COUNT(GStockSeams));
}

int32 FMelodiaStockContract::Validate(TArray<FMelodiaStockSeamResult>& OutResults)
{
	OutResults.Reset();
	int32 BrokenCount = 0;

	for (const FMelodiaStockSeam& Seam : GetSeams())
	{
		FMelodiaStockSeamResult Result;
		Result.ClassPath = Seam.ClassPath;
		Result.MemberName = Seam.MemberName;
		Result.UsedBy = Seam.UsedBy;

		// LoadClass, not FindObject: the validator must work on a cold process
		// where nothing has pulled these Blueprints in yet.
		if (const UClass* Class = LoadClass<UObject>(nullptr, Seam.ClassPath))
		{
			Result.bClassResolved = true;
			Result.bKindMatched = MemberMatchesKind(Class, Seam.MemberName, Seam.Kind, Result.FoundKind, Result.bMemberResolved);
		}

		if (Result.IsBroken())
		{
			++BrokenCount;
		}
		OutResults.Add(MoveTemp(Result));
	}

	return BrokenCount;
}

int32 FMelodiaStockContract::LogReport()
{
	TArray<FMelodiaStockSeamResult> Results;
	const int32 BrokenCount = Validate(Results);

	for (const FMelodiaStockSeamResult& Result : Results)
	{
		if (Result.IsBroken())
		{
			UE_LOG(LogTemp, Error, TEXT("%s"), *Result.Describe());
		}
		else
		{
			UE_LOG(LogTemp, Verbose, TEXT("%s"), *Result.Describe());
		}
	}

	if (BrokenCount > 0)
	{
		UE_LOG(LogTemp, Error, TEXT("MELODIA_CONTRACT %d of %d stock seams are BROKEN; the integration layer will fail silently at those points."),
			BrokenCount, Results.Num());
	}
	else
	{
		UE_LOG(LogTemp, Log, TEXT("MELODIA_CONTRACT all %d stock seams resolve."), Results.Num());
	}

	return BrokenCount;
}

static FAutoConsoleCommand GMelodiaValidateStockContract(
	TEXT("melodia.Contract.Validate"),
	TEXT("Resolve every stock-Blueprint name the Melodia integration layer depends on and report the broken ones."),
	FConsoleCommandDelegate::CreateLambda([]() { FMelodiaStockContract::LogReport(); }));
