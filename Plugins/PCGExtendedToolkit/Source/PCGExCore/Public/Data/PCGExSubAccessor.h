// Copyright 2026 Timothé Lapetite and contributors
// Released under the MIT license https://opensource.org/license/MIT/

#pragma once

#include "CoreMinimal.h"
#include "Math/PCGExMathAxis.h"
#include "Metadata/PCGMetadataAttributeTraits.h"
#include "Types/PCGExTypeOps.h"

// Forward-declare the PCG metadata attribute descriptor so header consumers don't
// drag the full FPCGMetadataAttribute machinery in. Full definition only required
// by accessors that consult container metadata (FContainerIndex/Count).
struct FPCGMetadataAttributeDesc;

/**
 * Sub-accessor abstraction.
 *
 * Pluggable, chainable sub-selection system. FSubAccessorRegistry owns
 * accessor instances (axis, transform-part, single-field, swizzle,
 * container-index, container-count) and parses ExtraNames into a chain.
 * FCachedSubSelection compiles the chain against a concrete source type
 * for direct fn-pointer invocation on the hot path.
 */

namespace PCGExData
{
	/**
	 * FAccessorParseResult
	 *
	 * Per-step parsed payload. POD, additive layout: each accessor reads
	 * only the fields it owns. New accessors extend this struct with new fields
	 * (container index, swizzle mask, struct-field name, ...) without
	 * breaking ABI.
	 */
	struct PCGEXCORE_API FAccessorParseResult
	{
		// FSingleFieldAccessor writes Field + FieldIndex.
		PCGExTypeOps::ESingleField Field = PCGExTypeOps::ESingleField::X;
		int32 FieldIndex = 0; // 0..3 for X/Y/Z/W; can be -1 for derived (Length/Sum/...)

		// FAxisAccessor writes Axis.
		EPCGExAxis Axis = EPCGExAxis::Forward;

		// FTransformPartAccessor writes Component.
		PCGExTypeOps::ETransformPart Component = PCGExTypeOps::ETransformPart::Position;

		// FSwizzleAccessor writes SwizzleMask + SwizzleLength.
		// Each byte in SwizzleMask is a source-component index (0=X, 1=Y, 2=Z, 3=W).
		// Length is the number of output components (2, 3, or 4 -> Vector2/Vector/Vector4).
		// Bytes beyond [SwizzleLength-1] are unused.
		uint8 SwizzleMask[4] = {0, 0, 0, 0};
		uint8 SwizzleLength = 0;

		// FContainerIndexAccessor writes ContainerIndex at parse time (the
		// integer inside `.N` / `.[N]`). Signed so we can sentinel-reject
		// unsuccessful parses (-1).
		int32 ContainerIndex = -1;

		// Compile-time (NOT parse-time) field. Populated by
		// PostClassifyFinalize for container accessors after the compiler has
		// seen the source attribute Desc: this is sizeof(ONE ELEMENT) of the
		// container, e.g. 24 for TArray<FVector>. The hot path reads it to
		// stride into FScriptArray-backed storage. Zero for non-container
		// accessors (they never touch it).
		int32 ContainerElementSize = 0;

		// Compile-time (NOT parse-time) field. Non-owning pointer to the
		// FProperty describing the container's inner element type (e.g., an
		// FStructProperty for FVector when the source is TArray<FVector>).
		// Populated by PostClassifyFinalize; owned by
		// FCachedSubSelection::OwnedProperties. Used by the container-index
		// write path for FProperty::CopyCompleteValue -- handles
		// non-trivially-copyable elements (FString, nested containers,
		// UStructs with custom copy/destroy). Null for non-container steps
		// and for read-only container steps (ContainerCount).
		const FProperty* ContainerElementProperty = nullptr;

		// Hint type the matched token implies for the source attribute, e.g. "X" -> Vector,
		// "W" -> Vector4, "Roll" -> Quaternion. Used for legacy PossibleSourceType
		// projection. Unknown when the accessor doesn't supply a hint.
		EPCGMetadataTypes SourceTypeHint = EPCGMetadataTypes::Unknown;
	};

	// Forward decls.
	class ISubAccessor;
	using FStepGetFn = void (*)(const void* Parent, void* ChildOut, const FAccessorParseResult& Parsed);
	using FStepSetFn = void (*)(void* ParentInOut, const void* NewChild, const FAccessorParseResult& Parsed);

	/**
	 * FSubSelectionStep
	 *
	 * One step in a parsed chain: the accessor that matched, its parsed
	 * payload, and the input/output types for this step in the pipeline.
	 *
	 * After CompileChainForSource, InType/OutType are resolved and
	 * StepGetFn/StepSetFn carry direct fn pointers so the hot path can
	 * invoke each step without vtable dispatch on the accessor.
	 */
	struct PCGEXCORE_API FSubSelectionStep
	{
		const ISubAccessor* Accessor = nullptr;
		FAccessorParseResult Parsed;
		EPCGMetadataTypes InType = EPCGMetadataTypes::Unknown;
		EPCGMetadataTypes OutType = EPCGMetadataTypes::Unknown;

		// Populated by CompileChainForSource. Hot path calls these directly.
		FStepGetFn StepGetFn = nullptr;
		FStepSetFn StepSetFn = nullptr;
	};

	/**
	 * FSubSelectionChain
	 *
	 * Ordered sequence of accessor steps that derives a sub-selected value
	 * from a source. An empty chain is the identity. Most chains are 1-2
	 * steps (Position.X, Rotation.Forward); the inline allocator avoids
	 * heap traffic for the common case.
	 */
	struct PCGEXCORE_API FSubSelectionChain
	{
		TArray<FSubSelectionStep, TInlineAllocator<2>> Steps;
		EPCGMetadataTypes FinalType = EPCGMetadataTypes::Unknown;
		EPCGMetadataTypes SourceTypeHint = EPCGMetadataTypes::Unknown;
		bool bIsValid = false;

		FORCEINLINE bool IsEmpty() const
		{
			return Steps.Num() == 0;
		}

		void Reset();
	};

	/**
	 * Compiled-chain hot-path fn-pointer signatures.
	 *
	 * FStepGetFn reads Parent (at this step's InType) and writes the
	 * extracted Child (at this step's OutType) to ChildOut.
	 *
	 * FStepSetFn takes a ParentInOut (at this step's InType) and a NewChild
	 * (at this step's OutType) and modifies Parent so that applying the
	 * extract again would produce NewChild. Read-only accessors (Axis)
	 * return nullptr from GetStepSetFn.
	 */
	using FStepGetFn = void (*)(const void* Parent, void* ChildOut, const FAccessorParseResult& Parsed);
	using FStepSetFn = void (*)(void* ParentInOut, const void* NewChild, const FAccessorParseResult& Parsed);

	/**
	 * ISubAccessor
	 *
	 * A pluggable accessor that knows how to match tokens, resolve the
	 * resulting type for a given source, and extract/inject values.
	 *
	 * Stateless by convention. Owned for-process by FSubAccessorRegistry.
	 *
	 * Implementations (FSingleFieldAccessor, FAxisAccessor,
	 * FTransformPartAccessor, FSwizzleAccessor, FContainerIndex/Count)
	 * provide typed fn-pointer getters (GetStepGetFn / GetStepSetFn)
	 * so FCachedSubSelection can cache per-step direct function calls
	 * without vtable dispatch.
	 */
	class PCGEXCORE_API ISubAccessor
	{
	public:
		virtual ~ISubAccessor() = default;

		/**
		 * Token matching. The registry calls this once per token in
		 * ExtraNames. The accessor decides whether the token is one of
		 * "its" tokens and, if so, populates OutParsed with whatever
		 * per-step state it needs.
		 *
		 * @param UpperToken The token uppercased (callers normalize once).
		 * @param OutParsed  Populated on a successful match.
		 * @return true if this accessor matches.
		 */
		virtual bool MatchesToken(const FString& UpperToken, FAccessorParseResult& OutParsed) const = 0;

		/**
		 * Compute the output type when this accessor's step is applied to
		 * a source of InType with the given parsed payload. Returns false
		 * if the accessor cannot apply to this source (e.g. axis on FString).
		 */
		virtual bool ResolveOutputType(EPCGMetadataTypes InType,
		                               const FAccessorParseResult& Parsed,
		                               EPCGMetadataTypes& OutType) const = 0;

		/**
		 * Hot path: extract the sub-selected value from Source (typed as
		 * InType) into OutValue (typed as OutType). Caller guarantees
		 * OutValue is large enough for OutType.
		 */
		virtual void ApplyGet(EPCGMetadataTypes InType,
		                      const void* Source,
		                      EPCGMetadataTypes OutType,
		                      void* OutValue,
		                      const FAccessorParseResult& Parsed) const = 0;

		/**
		 * Optional inject path. Default no-op for read-only accessors.
		 * Implementations that own a writable slot (field, component) may
		 * override.
		 */
		virtual void ApplySet(EPCGMetadataTypes InType,
		                      void* TargetInOut,
		                      EPCGMetadataTypes SourceType,
		                      const void* Source,
		                      const FAccessorParseResult& Parsed) const
		{
			(void)InType;
			(void)TargetInOut;
			(void)SourceType;
			(void)Source;
			(void)Parsed;
		}

		/**
		 * Diagnostic name. Used for chain-structure tests and error logs.
		 * Should be a short stable identifier, not a localized string.
		 */
		virtual FString GetDisplayName() const = 0;

		//
		// Compiled-chain hot path
		//

		/**
		 * Return a direct fn pointer for the extract direction at this
		 * step's InType. Called once per step during FCachedSubSelection
		 * Initialize; the returned pointer is cached in the compiled step
		 * and called without vtable dispatch at hot-path time.
		 *
		 * Returns nullptr if this accessor cannot operate on InType (the
		 * chain compiler drops such steps before they reach the hot path).
		 */
		virtual FStepGetFn GetStepGetFn(EPCGMetadataTypes InType) const = 0;

		/**
		 * Inject counterpart to GetStepGetFn. Returns nullptr for read-only
		 * accessors (Axis) and for types where inject is not meaningful.
		 */
		virtual FStepSetFn GetStepSetFn(EPCGMetadataTypes InType) const
		{
			(void)InType;
			return nullptr;
		}

		/**
		 * Chain compilation classifier for the parser-time chain vs the
		 * compile-time chain. Three outcomes:
		 *   - Keep: the step applies to SourceType as-is.
		 *   - Drop: the step is nonsensical for SourceType; the compiler
		 *     removes it (chain flows on to the next step at SourceType).
		 *   - PromoteToTransformPart_{Position,Rotation}: user shortcut --
		 *     auto-insert a TransformPart step before this one. Used when
		 *     SourceType is Transform and the user asked for axis/field
		 *     without explicitly picking a component first.
		 */
		enum class ECompileAction : uint8
		{
			Keep,
			Drop,
			PromoteWithPosition,
			PromoteWithRotation,
		};

		virtual ECompileAction ClassifyForInType(EPCGMetadataTypes InType,
		                                         const FAccessorParseResult& Parsed,
		                                         const FPCGMetadataAttributeDesc* SourceDesc = nullptr) const = 0;

		/**
		 * Compile-time finalization hook. Called by the chain compiler AFTER
		 * ClassifyForInType returns Keep and AFTER InType/OutType/StepGetFn
		 * are populated. Accessors that need to stash compile-derived state
		 * (e.g. container element size from the source Desc) override this
		 * to mutate Parsed in-place.
		 *
		 * Defaults to no-op. Only FContainerIndexAccessor and
		 * FContainerCountAccessor currently override.
		 */
		virtual void PostClassifyFinalize(EPCGMetadataTypes InType,
		                                  FAccessorParseResult& InOutParsed,
		                                  const FPCGMetadataAttributeDesc* SourceDesc) const
		{
			(void)InType;
			(void)InOutParsed;
			(void)SourceDesc;
		}
	};

	/**
	 * FSubAccessorRegistry
	 *
	 * Process-lifetime owner of accessor instances + entry point for
	 * parsing ExtraNames into a chain.
	 *
	 * Registration order is priority order: when multiple accessors could
	 * match a token, the earlier-registered one wins. Registration order is
	 * Axis -> TransformPart -> SingleField -> Swizzle -> ContainerCount -> ContainerIndex.
	 */
	class PCGEXCORE_API FSubAccessorRegistry
	{
	public:
		/** Idempotent. Builds the accessor list on first call. */
		static void Initialize();

		/** Registration-order view of all known accessors. */
		static TConstArrayView<const ISubAccessor*> GetAll();

		/** Typed accessor getters. Stable for the process lifetime after Initialize(). */
		static const ISubAccessor* GetAxisAccessor();
		static const ISubAccessor* GetTransformPartAccessor();
		static const ISubAccessor* GetSingleFieldAccessor();
		static const ISubAccessor* GetContainerIndexAccessor();
		static const ISubAccessor* GetContainerCountAccessor();

		/**
		 * Parse a list of extra-name tokens into a chain. True left-to-right
		 * walk; each token tries every accessor in registration order, first
		 * match wins. Chain order mirrors token order.
		 *
		 * @param ExtraNames     Tokens from FPCGAttributePropertyInputSelector::GetExtraNames().
		 * @param SourceTypeHint Optional hint about the source attribute's type.
		 * @param OutChain       Populated on a successful parse; reset on failure.
		 * @return true if any step was produced.
		 */
		static bool ParseChain(const TArray<FString>& ExtraNames,
		                       EPCGMetadataTypes SourceTypeHint,
		                       FSubSelectionChain& OutChain);

	private:
		static TArray<TUniquePtr<ISubAccessor>> OwnedAccessors;
		static TArray<const ISubAccessor*> OrderedView;
		static bool bInitialized;
	};

	/**
	 * Number of distinct field positions a source type exposes.
	 * Used by callers that split an attribute into per-field sub-pieces
	 * (attribute remapper, noise generator, proxy-data helper).
	 *
	 *   Vector2            -> 2
	 *   Vector / Rotator   -> 3
	 *   Vector4 / Quat     -> 4
	 *   Transform          -> 9  (3 pos + 3 rot + 3 scale)
	 *   everything else    -> 1
	 */
	PCGEXCORE_API int32 GetNumFieldsForType(EPCGMetadataTypes Type);

	/**
	 * Compile a parsed chain for a concrete source type.
	 *
	 * Walks the chain left-to-right. For each step, classifies against the
	 * current value type (starting from SourceType; each kept step updates
	 * the current type to its OutType):
	 *   - Keep:   step is compatible; appended to the compiled chain as-is.
	 *   - Drop:   step is nonsensical for the current type; removed.
	 *   - Promote: insert an implicit TransformPart step before this one,
	 *              then retry (e.g., `.Forward` on a Transform source gets
	 *              promoted to `.Rotation.Forward`; `.X` on a Transform
	 *              source gets promoted to `.Position.X`).
	 *
	 * Also fills in each step's InType, OutType, StepGetFn, StepSetFn so
	 * the compiled chain is ready for direct invocation without further
	 * accessor lookups.
	 *
	 * SourceDesc: when non-null, container-aware accessors
	 * (FContainerIndexAccessor / FContainerCountAccessor) consult it to
	 * decide whether the source is a compatible container. The Desc is
	 * only meaningful for the chain's first (unwrapping) step; after a
	 * container step consumes the outer ContainerTypes entry, subsequent
	 * steps see a null SourceDesc because the value has been unwrapped to
	 * its element type. Scalar sources pass SourceDesc=nullptr.
	 */
	PCGEXCORE_API void CompileChainForSource(FSubSelectionChain& InOutChain,
	                                         EPCGMetadataTypes SourceType,
	                                         const FPCGMetadataAttributeDesc* SourceDesc = nullptr);
}
