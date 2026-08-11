// Copyright 2026 Timothé Lapetite and contributors
// Released under the MIT license https://opensource.org/license/MIT/

#pragma once

#include "CoreMinimal.h"
#include "PCGExAssetGrammar.generated.h"

struct FPCGExAssetStagingData;
class UPCGExAssetCollection;
struct FPCGExAssetCollectionEntry;
struct FPCGSubdivisionSubmodule;

// ============================================================================
// LEGACY ENUMS (schema v0)
// Retained ONLY so existing serialized data deserializes correctly for migration.
// New code MUST NOT reference these. Removed in a future major version.
// ============================================================================

UENUM()
enum class EPCGExGrammarScaleMode : uint8
{
	Fixed = 0 UMETA(DisplayName = "Fixed"),
	Flex  = 1 UMETA(DisplayName = "Flexible"),
};

UENUM()
enum class EPCGExGrammarSizeReference : uint8
{
	X       = 0 UMETA(DisplayName = "X"),
	Y       = 1 UMETA(DisplayName = "Y"),
	Z       = 2 UMETA(DisplayName = "Z"),
	Min     = 3 UMETA(DisplayName = "Smallest"),
	Max     = 4 UMETA(DisplayName = "Largest"),
	Average = 5 UMETA(DisplayName = "Average"),
	Fixed   = 6 UMETA(DisplayName = "Fixed"),
};

UENUM()
enum class EPCGExCollectionGrammarSize : uint8
{
	Fixed   = 0 UMETA(DisplayName = "Fixed"),
	Min     = 1 UMETA(DisplayName = "Smallest"),
	Max     = 2 UMETA(DisplayName = "Largest"),
	Average = 3 UMETA(DisplayName = "Average"),
};

// ============================================================================
// CURRENT ENUMS (schema v1)
// ============================================================================

/**
 * Bitmask of subdivision axes a grammar module participates in. None = not a valid module.
 * UseEnumValuesAsMaskValuesInEditor tells the editor's BitmaskEnum widget that values are
 * mask bits directly (1, 2, 4) rather than bit indices -- without it, the checkboxes are
 * off-by-one and toggling "X" sets the Y bit.
 */
UENUM(BlueprintType, meta=(Bitflags, UseEnumValuesAsMaskValuesInEditor="true"))
enum class EPCGExGrammarAxes : uint8
{
	None = 0 UMETA(Hidden),
	X    = 1 << 0 UMETA(DisplayName = "X", ActionIcon = "X"),
	Y    = 1 << 1 UMETA(DisplayName = "Y", ActionIcon = "Y"),
	Z    = 1 << 2 UMETA(DisplayName = "Z", ActionIcon = "Z"),
};

ENUM_CLASS_FLAGS(EPCGExGrammarAxes)

namespace PCGExGrammarAxes
{
	/** Iteration order for axis-indexed loops. */
	static constexpr EPCGExGrammarAxes Bits[3] = {EPCGExGrammarAxes::X, EPCGExGrammarAxes::Y, EPCGExGrammarAxes::Z};

	/** Hardcoded attribute-name suffixes. */
	static constexpr const TCHAR* Suffixes[3] = {TEXT("_X"), TEXT("_Y"), TEXT("_Z")};

	/** Bare per-axis letters for UI labels. */
	static constexpr const TCHAR* Letters[3] = {TEXT("X"), TEXT("Y"), TEXT("Z")};

	/** Number of set bits in an axis mask. Constrained to the 3 valid axis bits. */
	FORCEINLINE int32 CountAxes(const uint8 Mask)
	{
		return ((Mask & static_cast<uint8>(EPCGExGrammarAxes::X)) ? 1 : 0)
			+ ((Mask & static_cast<uint8>(EPCGExGrammarAxes::Y)) ? 1 : 0)
			+ ((Mask & static_cast<uint8>(EPCGExGrammarAxes::Z)) ? 1 : 0);
	}

	/** Builds the per-axis attribute name. When bSuppressSuffix is true, returns Base unchanged
	 *  (single-axis legacy shape); otherwise appends the matching _X/_Y/_Z suffix. */
	FORCEINLINE FName MakeAxisAttributeName(const FName& Base, const int32 AxisIndex, const bool bSuppressSuffix)
	{
		if (bSuppressSuffix)
		{
			return Base;
		}
		return FName(*FString::Printf(TEXT("%s%s"), *Base.ToString(), Suffixes[AxisIndex]));
	}
}

/** Per-axis size source. Min_X/Y/Z, Max_X/Y/Z, Avg_X/Y/Z are subcollection-only and encode a child
 *  source axis independent of the slot axis (Min_Z in SizingX = aggregate child Z for the X output). */
UENUM(BlueprintType)
enum class EPCGExGrammarAxisSize : uint8
{
	Bounds = 0 UMETA(DisplayName = "Bounds", Tooltip = "Use the entry's bounds extent on this axis.", ActionIcon = "From_Center"),
	Fixed  = 1 UMETA(DisplayName = "Fixed", Tooltip = "Use FixedSize as the literal size on this axis.", ActionIcon = "Constant"),
	Min_X  = 2 UMETA(DisplayName = "Smallest (X)", Tooltip = "Subcollection only: smallest child X grammar size.", ActionIcon = "Fit_Min"),
	Min_Y  = 3 UMETA(DisplayName = "Smallest (Y)", Tooltip = "Subcollection only: smallest child Y grammar size.", ActionIcon = "Fit_Min"),
	Min_Z  = 4 UMETA(DisplayName = "Smallest (Z)", Tooltip = "Subcollection only: smallest child Z grammar size.", ActionIcon = "Fit_Min"),
	Max_X  = 5 UMETA(DisplayName = "Largest (X)", Tooltip = "Subcollection only: largest child X grammar size.", ActionIcon = "Fit_Max"),
	Max_Y  = 6 UMETA(DisplayName = "Largest (Y)", Tooltip = "Subcollection only: largest child Y grammar size.", ActionIcon = "Fit_Max"),
	Max_Z  = 7 UMETA(DisplayName = "Largest (Z)", Tooltip = "Subcollection only: largest child Z grammar size.", ActionIcon = "Fit_Max"),
	Avg_X  = 8 UMETA(DisplayName = "Average (X)", Tooltip = "Subcollection only: average of child X grammar sizes.", ActionIcon = "Fit_Average"),
	Avg_Y  = 9 UMETA(DisplayName = "Average (Y)", Tooltip = "Subcollection only: average of child Y grammar sizes.", ActionIcon = "Fit_Average"),
	Avg_Z  = 10 UMETA(DisplayName = "Average (Z)", Tooltip = "Subcollection only: average of child Z grammar sizes.", ActionIcon = "Fit_Average"),
};

namespace PCGExGrammarAxes
{
	enum class EAggregator : uint8
	{
		None,
		Min,
		Max,
		Average
	};

	namespace Detail
	{
		struct FAggregationDecode
		{
			EAggregator Agg;
			EPCGExGrammarAxes Axis;
		};

		static constexpr FAggregationDecode AggregationTable[11] = {
			/* Bounds */ {EAggregator::None, EPCGExGrammarAxes::None},
			             /* Fixed  */ {EAggregator::None, EPCGExGrammarAxes::None},
			             /* Min_X  */ {EAggregator::Min, EPCGExGrammarAxes::X},
			             /* Min_Y  */ {EAggregator::Min, EPCGExGrammarAxes::Y},
			             /* Min_Z  */ {EAggregator::Min, EPCGExGrammarAxes::Z},
			             /* Max_X  */ {EAggregator::Max, EPCGExGrammarAxes::X},
			             /* Max_Y  */ {EAggregator::Max, EPCGExGrammarAxes::Y},
			             /* Max_Z  */ {EAggregator::Max, EPCGExGrammarAxes::Z},
			             /* Avg_X  */ {EAggregator::Average, EPCGExGrammarAxes::X},
			             /* Avg_Y  */ {EAggregator::Average, EPCGExGrammarAxes::Y},
			             /* Avg_Z  */ {EAggregator::Average, EPCGExGrammarAxes::Z},
		};
	}

	FORCEINLINE void DecodeAggregation(EPCGExGrammarAxisSize Size, EAggregator& OutAgg, EPCGExGrammarAxes& OutSourceAxis)
	{
		const Detail::FAggregationDecode& E = Detail::AggregationTable[static_cast<uint8>(Size)];
		OutAgg = E.Agg;
		OutSourceAxis = E.Axis;
	}

	FORCEINLINE bool IsAggregation(EPCGExGrammarAxisSize Size)
	{
		return Size != EPCGExGrammarAxisSize::Bounds && Size != EPCGExGrammarAxisSize::Fixed;
	}
}

/** Memoization key for recursive grammar size resolution. Keyed by (Entry, Axis) because
 *  cross-axis aggregation recursion mixes axes within one top-level pass. */
struct FPCGExGrammarSizeCacheKey
{
	const FPCGExAssetCollectionEntry* Entry = nullptr;
	EPCGExGrammarAxes Axis = EPCGExGrammarAxes::None;

	FORCEINLINE bool operator==(const FPCGExGrammarSizeCacheKey& Other) const
	{
		return Entry == Other.Entry && Axis == Other.Axis;
	}
};

FORCEINLINE uint32 GetTypeHash(const FPCGExGrammarSizeCacheKey& Key)
{
	return HashCombine(GetTypeHash(Key.Entry), GetTypeHash(static_cast<uint8>(Key.Axis)));
}

using FPCGExGrammarSizeCache = TMap<FPCGExGrammarSizeCacheKey, double>;

/** Arithmetic op applied on top of the resolved per-axis size. */
UENUM(BlueprintType)
enum class EPCGExGrammarSizeOp : uint8
{
	None     = 0 UMETA(DisplayName = "=", Tooltip = "Use the resolved size as-is."),
	Offset   = 1 UMETA(DisplayName = "+", Tooltip = "Add FixedSize to the resolved size."),
	Multiply = 2 UMETA(DisplayName = "×", Tooltip = "Multiply the resolved size by FixedSize."),
};

UENUM(BlueprintType)
enum class EPCGExGrammarSubCollectionMode : uint8
{
	Inherit  = 0 UMETA(DisplayName = "Inherit", Tooltip = "Use the subcollection's own SubCollectionGrammar."),
	Override = 1 UMETA(DisplayName = "Override", Tooltip = "Override with this entry's AssetGrammar."),
	Flatten  = 2 UMETA(DisplayName = "Flatten", Tooltip = "Hoist the collection entries as if they were part of this collection."),
};

// ============================================================================
// CURRENT TYPES (schema v1)
// ============================================================================

/**
 * Per-axis sizing configuration. Shared across leaf and subcollection contexts;
 * customization gates which EPCGExGrammarAxisSize values are available based on
 * the surrounding entry's bIsSubCollection.
 */
USTRUCT(BlueprintType, DisplayName="[PCGEx] Grammar Axis Details")
struct PCGEXCOLLECTIONS_API FPCGExGrammarAxisDetails
{
	GENERATED_BODY()

	FPCGExGrammarAxisDetails() = default;

	/** Where the size for this axis comes from. */
	UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = Settings)
	EPCGExGrammarAxisSize Size = EPCGExGrammarAxisSize::Bounds;

	/** Optional op applied on top of the resolved size. Ignored when Size == Fixed. */
	UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = Settings)
	EPCGExGrammarSizeOp SizeOp = EPCGExGrammarSizeOp::None;

	/** Literal size when Size==Fixed, offset when SizeOp==Offset, multiplier when SizeOp==Multiply. */
	UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = Settings)
	double FixedSize = 100;

	/** Whether the resolved module is scalable along this axis. */
	UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = Settings)
	bool bScalable = false;

	/** Apply SizeOp + FixedSize on top of an already-resolved scalar (Bounds extent or aggregated value). */
	double ApplyOp(double InResolved) const;
};

/**
 * Unified grammar configuration. Lives at the entry level (as AssetGrammar) and at the
 * collection level (as GlobalAssetGrammar / SubCollectionGrammar). Customization shows
 * different EPCGExGrammarAxisSize options depending on whether the surrounding entry
 * is bIsSubCollection.
 *
 * Axes is a bitmask: 0 means "not a valid module" (output skipped). When evaluated for
 * a disabled axis, GetSize returns 0 and FixLeaf/FixSubCollection return false.
 */
USTRUCT(BlueprintType, DisplayName="[PCGEx] Grammar Details")
struct PCGEXCOLLECTIONS_API FPCGExAssetGrammarDetails
{
	GENERATED_BODY()

	FPCGExAssetGrammarDetails() = default;

	FPCGExAssetGrammarDetails(const FName InSymbol)
		: Symbol(InSymbol)
	{
	}

	/** Symbol for the grammar. Shared across all enabled axes. */
	UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = Settings)
	FName Symbol = NAME_None;

	/** For easier debugging, using Point color in conjunction with PCG Debug Color Material. Shared across axes. */
	UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = Settings)
	FLinearColor DebugColor = FLinearColor::White;

	/**
	 * Subdivision axes this module participates in. None = not a valid module (skipped during export).
	 * Defaults to X for new entries, matching the most common single-axis use case. PostLoad migration
	 * overrides this explicitly for legacy entries (empty Symbol -> None; legacy Size axis -> matching bit).
	 */
	UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = Settings, meta=(Bitmask, BitmaskEnum="/Script/PCGExCollections.EPCGExGrammarAxes"))
	uint8 Axes = static_cast<uint8>(EPCGExGrammarAxes::X);

	UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = Settings)
	FPCGExGrammarAxisDetails SizingX;

	UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = Settings)
	FPCGExGrammarAxisDetails SizingY;

	UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = Settings)
	FPCGExGrammarAxisDetails SizingZ;

#pragma region DEPRECATED
	// LEGACY (schema v0). Kept ONLY so prior serialized data deserializes for migration.
	// UPCGExAssetCollection::PostLoad reads these when GrammarSchemaVersion < 1 and writes
	// the canonical fields above. Do not read directly outside migration code.

	UPROPERTY(meta=(DeprecatedProperty, ScriptNoExport))
	EPCGExGrammarScaleMode ScaleMode_DEPRECATED = EPCGExGrammarScaleMode::Fixed;

	UPROPERTY(meta=(DeprecatedProperty, ScriptNoExport))
	EPCGExGrammarSizeReference Size_DEPRECATED = EPCGExGrammarSizeReference::X;

	UPROPERTY(meta=(DeprecatedProperty, ScriptNoExport))
	EPCGExGrammarSizeOp SizeOp_DEPRECATED = EPCGExGrammarSizeOp::None;

	UPROPERTY(meta=(DeprecatedProperty, ScriptNoExport))
	double FixedSize_DEPRECATED = 100;

#pragma endregion

	// Runtime API

	FORCEINLINE bool IsValidModule() const
	{
		return Axes != 0;
	}

	FORCEINLINE bool HasAxis(EPCGExGrammarAxes Axis) const
	{
		return (Axes & static_cast<uint8>(Axis)) != 0;
	}

	const FPCGExGrammarAxisDetails& GetAxisDetails(EPCGExGrammarAxes Axis) const;
	FPCGExGrammarAxisDetails& GetAxisDetailsMutable(EPCGExGrammarAxes Axis);

	/**
	 * Leaf-context size. Caller provides the entry's own bounds.
	 * Returns 0 when the axis isn't enabled, or when the axis sizing mode is Min/Max/Average
	 * (only valid for subcollections -- invalid combination, caller should have used FixSubCollection).
	 */
	double GetLeafSize(const FBox& InBounds, EPCGExGrammarAxes Axis = EPCGExGrammarAxes::X) const;

	/** Subcollection-context size. SizeCache deduplicates per-(entry,axis) queries across the recursion. */
	double GetSubCollectionSize(
		const UPCGExAssetCollection* SubCollection,
		EPCGExGrammarAxes Axis = EPCGExGrammarAxes::X,
		FPCGExGrammarSizeCache* SizeCache = nullptr) const;

	/**
	 * Leaf-context Fix. Returns true and populates OutSubmodule (Symbol, DebugColor, Size, bScalable)
	 * when the axis is enabled. Returns false otherwise; OutSubmodule untouched.
	 */
	bool FixLeaf(const FBox& InBounds, EPCGExGrammarAxes Axis, FPCGSubdivisionSubmodule& OutSubmodule) const;

	/** Subcollection-context Fix. Same contract as FixLeaf, using GetSubCollectionSize. */
	bool FixSubCollection(
		const UPCGExAssetCollection* SubCollection,
		EPCGExGrammarAxes Axis,
		FPCGSubdivisionSubmodule& OutSubmodule,
		FPCGExGrammarSizeCache* SizeCache = nullptr) const;


#if WITH_EDITOR

	// Migration (schema v0 -> v1)

	/**
	 * Migrate the internal *_DEPRECATED fields into the new per-axis fields. Should be called
	 * exactly once per struct during PostLoad gated by GrammarSchemaVersion. Mapping:
	 *  - Symbol == NAME_None                 -> Axes = None (module disabled, info)
	 *  - Size_DEPRECATED in {X, Y, Z}        -> Axes = matching bit, SizingN.Size = Bounds
	 *  - Size_DEPRECATED == Fixed            -> Axes = X, SizingX.Size = Fixed
	 *  - Size_DEPRECATED in {Min, Max, Avg}  -> Axes = X, SizingX.Size = Bounds (warning)
	 * The old SizeOp / FixedSize copy into the targeted axis; old ScaleMode == Flex -> bScalable.
	 * @return true when a Min/Max/Average legacy mode was downgraded (caller may log).
	 */
	bool MigrateFromV0Internal();

	/** Overwrite this struct with the values of a legacy collection grammar (used for migrating
	 *  entry CollectionGrammar_DEPRECATED into AssetGrammar when Override, and collection-level
	 *  CollectionGrammar_DEPRECATED into SubCollectionGrammar). */
	void MigrateFromLegacyCollectionGrammar(const struct FPCGExCollectionGrammarDetails& Legacy);

	/**
	 * Snap each axis's Size mode to one valid for the given context (leaf vs subcollection).
	 * Bounds is leaf-only; Min/Max/Average are subcollection-only; Fixed is universal and the
	 * fallback target. Invoked from PostEditChangeProperty to recover from context flips
	 * (toggling bIsSubCollection, switching SubGrammarMode to/from Override) without leaving
	 * the struct in an unevaluable state.
	 * @return true if any axis was modified.
	 */
	bool ValidateContext(bool bIsSubCollection);

#endif

};


// ============================================================================
// LEGACY TYPES (schema v0)
// ============================================================================

/**
 * LEGACY (schema v0). Retained ONLY so prior CollectionGrammar serialized data deserializes
 * for migration in UPCGExAssetCollection::PostLoad. New code must use FPCGExAssetGrammarDetails.
 * Removed in a future major version.
 */
USTRUCT()
struct PCGEXCOLLECTIONS_API FPCGExCollectionGrammarDetails
{
	GENERATED_BODY()

	FPCGExCollectionGrammarDetails() = default;

	UPROPERTY()
	FName Symbol = NAME_None;

	UPROPERTY()
	EPCGExGrammarScaleMode ScaleMode = EPCGExGrammarScaleMode::Fixed;

	UPROPERTY()
	EPCGExCollectionGrammarSize SizeMode = EPCGExCollectionGrammarSize::Min;

	UPROPERTY()
	double Size = 100;

	UPROPERTY()
	FLinearColor DebugColor = FLinearColor::White;
};
