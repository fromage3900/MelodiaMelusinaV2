#pragma once

#include "CoreMinimal.h"
#include "Containers/ArrayView.h"

/**
 * The stock-Blueprint name contract, in one place.
 *
 * WHY THIS FILE EXISTS
 *
 * The integration layer reaches into stock TurnBasedJRPG Blueprints by NAME --
 * FindFunction(TEXT("AddPlayerUnit")), FindFProperty<>(..., TEXT("playerUnits")),
 * and roughly thirty more across nine files. Every one of those is a silent
 * failure surface: rename or delete the member on the Blueprint side and the C++
 * still compiles, still runs, and quietly does nothing.
 *
 * That is not hypothetical. On 2026-08-08 all three of the day's defects had this
 * exact shape:
 *
 *   * BP_BattleUI::battleController had four readers and zero writers, so the
 *     widget's controller reference was permanently null and target selection
 *     could never work.
 *   * Sir Melodious was added to the playerUnits roster but never to
 *     partyMembers, and the recruitment path logged success anyway because it
 *     returned true the moment ProcessEvent came back.
 *   * The presentation rhythm component had no clock source, warned once at
 *     BeginPlay, and was silent forever after.
 *
 * All three compiled clean, matched their graph fingerprints, and passed closure
 * checks. No gate in the project could see any of them, because every gate
 * asserts that a call site EXISTS -- not that the thing it names is still there.
 *
 * This manifest closes that gap. Validation is a pure lookup: load the class,
 * find the member, confirm its kind. It needs no PIE, no world, and no editor,
 * so it can run as an automation test and at boot behind a cvar.
 *
 * SCOPE: this proves the seams RESOLVE. It does not prove they BEHAVE. A green
 * report means "the names C++ depends on are still present with the expected
 * shape" -- nothing more.
 */

enum class EMelodiaStockSeamKind : uint8
{
	Function,
	ObjectProperty,
	StructProperty,
	ArrayProperty,
	MapProperty,
	MulticastDelegate,
};

/** One name C++ depends on, and who depends on it. */
struct FMelodiaStockSeam
{
	const TCHAR* ClassPath;
	const TCHAR* MemberName;
	EMelodiaStockSeamKind Kind;
	const TCHAR* UsedBy;
};

struct FMelodiaStockSeamResult
{
	FString ClassPath;
	FString MemberName;
	FString UsedBy;
	FString FoundKind;

	bool bClassResolved = false;
	bool bMemberResolved = false;
	bool bKindMatched = false;

	bool IsBroken() const { return !bClassResolved || !bMemberResolved || !bKindMatched; }

	/** Single-line, greppable, and states what was expected AND what was found. */
	FString Describe() const;
};

class BS_GODFILE_API FMelodiaStockContract
{
public:
	/** The manifest. Every entry below was confirmed present in the live graph. */
	static TArrayView<const FMelodiaStockSeam> GetSeams();

	/** Resolves every seam. Returns the number that are broken. */
	static int32 Validate(TArray<FMelodiaStockSeamResult>& OutResults);

	/** Validates and logs one line per broken seam, plus a summary. */
	static int32 LogReport();

	static const TCHAR* LexToString(EMelodiaStockSeamKind Kind);
};
