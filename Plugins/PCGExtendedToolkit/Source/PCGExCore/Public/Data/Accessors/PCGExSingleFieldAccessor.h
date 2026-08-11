// Copyright 2026 Timothé Lapetite and contributors
// Released under the MIT license https://opensource.org/license/MIT/

#pragma once

#include "CoreMinimal.h"
#include "Data/PCGExSubAccessor.h"

namespace PCGExData
{
	/**
	 * FSingleFieldAccessor -- matches X/Y/Z/W and aliases (R/G/B/A,
	 * Roll/Yaw/Pitch, Length/Volume/Sum, ...). Parity wrapper around the
	 * existing FTypeOps<T>::ExtractField / InjectField primitives.
	 *
	 * Always resolves to Double output. Stateless.
	 */
	class PCGEXCORE_API FSingleFieldAccessor final : public ISubAccessor
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
	};
}
