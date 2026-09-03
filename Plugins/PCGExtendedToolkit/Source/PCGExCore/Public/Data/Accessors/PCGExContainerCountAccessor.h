// Copyright 2026 Timothé Lapetite and contributors
// Released under the MIT license https://opensource.org/license/MIT/

#pragma once

#include "CoreMinimal.h"
#include "Data/PCGExSubAccessor.h"

namespace PCGExData
{
	/**
	 * FContainerCountAccessor -- matches `.Num` / `.Count` tokens on
	 * container-typed attribute sources (TArray/TSet). Output is Double
	 * (the number of elements in the outermost container).
	 *
	 * Requires Desc-awareness: ClassifyForInType consults SourceDesc's
	 * ContainerTypes to decide Keep (any container present) vs Drop
	 * (scalar source -- `.Num` on a Vector is nonsensical). Supports
	 * Array, Set, and Map containers: FScriptArray, FScriptSet, and
	 * FScriptMap all store Num() at a compatible binary offset.
	 *
	 * Read-only. Binary-reads the container's Num via FScriptArray layout
	 * (UE guarantees TArray<T> / TSet<T> / TMap<K,V> share the tri-word
	 * Data/Num/Max prefix). The accessor is type-agnostic at hot-path
	 * time: sizeof(T) isn't needed because we only read the Num field.
	 */
	class PCGEXCORE_API FContainerCountAccessor final : public ISubAccessor
	{
	public:
		virtual bool MatchesToken(const FString& UpperToken, FAccessorParseResult& OutParsed) const override;

		virtual bool ResolveOutputType(EPCGMetadataTypes InType,
		                               const FAccessorParseResult& Parsed,
		                               EPCGMetadataTypes& OutType) const override;

		virtual void ApplyGet(EPCGMetadataTypes InType,
		                      const void* Source,
		                      EPCGMetadataTypes OutType,
		                      void* OutValue,
		                      const FAccessorParseResult& Parsed) const override;

		virtual FString GetDisplayName() const override;

		virtual FStepGetFn GetStepGetFn(EPCGMetadataTypes InType) const override;
		// Read-only; GetStepSetFn inherits default nullptr.

		virtual ECompileAction ClassifyForInType(EPCGMetadataTypes InType,
		                                         const FAccessorParseResult& Parsed,
		                                         const FPCGMetadataAttributeDesc* SourceDesc = nullptr) const override;

		// No PostClassifyFinalize override: Count doesn't need ElementSize.
	};
}
