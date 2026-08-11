// Copyright 2026 Timothé Lapetite and contributors
// Released under the MIT license https://opensource.org/license/MIT/

#pragma once

#include "CoreMinimal.h"
#include "Data/PCGExSubAccessor.h"

namespace PCGExData
{
	/**
	 * FContainerIndexAccessor -- matches numeric tokens (`0`, `42`) and
	 * bracket-wrapped numeric tokens (`[0]`, `[42]`) on container-typed
	 * attribute sources (TArray). The output is the element type (which
	 * for PCG metadata is reported as-is in EPCGMetadataTypes -- container
	 * attributes carry their container-ness out-of-band via Desc, so
	 * `RealType` for TArray<FVector> is already Vector).
	 *
	 * Requires Desc-awareness: ClassifyForInType consults SourceDesc's
	 * ContainerTypes to decide Keep (Array container present) vs Drop
	 * (scalar source -- `.0` on a Vector is nonsensical). PostClassifyFinalize
	 * stashes the inner element size into Parsed.ContainerElementSize so
	 * the hot path can stride into FScriptArray storage without carrying
	 * the Desc forward.
	 *
	 * Write path uses FProperty::CopyCompleteValue when
	 * Parsed.ContainerElementProperty is available (handles non-trivially-
	 * copyable elements like FString, nested containers, UStructs), falling
	 * back to memcpy for trivially-copyable types or when no property was
	 * created.
	 *
	 * Type-agnostic at hot-path time: a single StepGetFn memcpys
	 * Parsed.ContainerElementSize bytes from the array's storage into the
	 * caller-provided output buffer. Out-of-range indices zero the output.
	 */
	class PCGEXCORE_API FContainerIndexAccessor final : public ISubAccessor
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

		virtual void ApplySet(EPCGMetadataTypes InType,
		                      void* TargetInOut,
		                      EPCGMetadataTypes SourceType,
		                      const void* Source,
		                      const FAccessorParseResult& Parsed) const override;

		virtual FString GetDisplayName() const override;

		virtual FStepGetFn GetStepGetFn(EPCGMetadataTypes InType) const override;
		virtual FStepSetFn GetStepSetFn(EPCGMetadataTypes InType) const override;

		virtual ECompileAction ClassifyForInType(EPCGMetadataTypes InType,
		                                         const FAccessorParseResult& Parsed,
		                                         const FPCGMetadataAttributeDesc* SourceDesc = nullptr) const override;

		virtual void PostClassifyFinalize(EPCGMetadataTypes InType,
		                                  FAccessorParseResult& InOutParsed,
		                                  const FPCGMetadataAttributeDesc* SourceDesc) const override;
	};
}
