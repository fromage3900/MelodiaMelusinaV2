// Copyright 2026 Timothé Lapetite and contributors
// Released under the MIT license https://opensource.org/license/MIT/

#pragma once

#include "CoreMinimal.h"
#include "Data/PCGExSubAccessor.h"

namespace PCGExData
{
	/**
	 * FSwizzleAccessor -- matches 2/3/4-char swizzle tokens like `.xy`,
	 * `.xyz`, `.wzyx`, `.zxy`, etc. Each character must be one of
	 * {x, y, z, w} (case-insensitive).
	 *
	 * Output type is driven by the swizzle length:
	 *   2 chars -> Vector2
	 *   3 chars -> Vector
	 *   4 chars -> Vector4
	 *
	 * Reading a component the source type doesn't have (e.g., `.w` on
	 * FVector2D) yields 0 for that output component -- treats shorter
	 * vectors as padded with zeros on the right.
	 *
	 * Stateless. Read-only (no inject path -- swizzle order would be
	 * ambiguous to reverse). ClassifyForInType auto-promotes Transform
	 * sources via Position, drops string sources, and keeps everything
	 * else.
	 */
	class PCGEXCORE_API FSwizzleAccessor final : public ISubAccessor
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
	};
}
