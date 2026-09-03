// Copyright 2026 Timothé Lapetite and contributors
// Released under the MIT license https://opensource.org/license/MIT/

#pragma once

#include "CoreMinimal.h"
#include "Core/PCGExProxyDataBlending.h"
#include "Core/PCGExUnionData.h"
#include "Data/PCGExData.h"
#include "UObject/Object.h"

class UPCGExBlendOpFactory;
class FPCGExBlendOperation;

namespace PCGExBlending
{
	class FBlendOpsManager;
	class FBlendOpsSchema;
	struct FPropertiesBlender;
}

namespace PCGExBlending
{
	class PCGEXBLENDING_API FUnionOpsManager final : public IUnionBlender
	{
	public:
		FUnionOpsManager(const TArray<TObjectPtr<const UPCGExBlendOpFactory>>* InBlendingFactories, const PCGExMath::IDistances* InDistances);
		virtual ~FUnionOpsManager() override;

		/** When a pre-resolved schema is provided, per-source blenders skip factory config resolution
		 * (and its concurrent metadata enumeration) -- see PCGExBlending::FBlendOpsSchema. */
		bool Init(FPCGExContext* InContext, const TSharedPtr<PCGExData::FFacade>& TargetData, const TArray<TSharedRef<PCGExData::FFacade>>& InSources, const TSharedPtr<const FBlendOpsSchema>& InSchema = nullptr);
		bool Init(FPCGExContext* InContext, const TSharedPtr<PCGExData::FFacade>& TargetData, const TArray<TSharedRef<PCGExData::FFacade>>& InSources, const TSharedPtr<PCGExData::FUnionMetadata>& InUnionMetadata, const TSharedPtr<const FBlendOpsSchema>& InSchema = nullptr);

		virtual void InitTrackers(TArray<PCGEx::FOpStats>& Trackers) const override;
		virtual int32 ComputeWeights(const int32 WriteIndex, const TSharedPtr<PCGExData::IUnionData>& InUnionData, TArray<PCGExData::FWeightedPoint>& OutWeightedPoints) const override;
		virtual void Blend(const int32 WriteIndex, const TArray<PCGExData::FWeightedPoint>& InWeightedPoints, TArray<PCGEx::FOpStats>& Trackers) const override;
		virtual void MergeSingle(const int32 WriteIndex, const TSharedPtr<PCGExData::IUnionData>& InUnionData, TArray<PCGExData::FWeightedPoint>& OutWeightedPoints, TArray<PCGEx::FOpStats>& Trackers) const override;
		virtual void MergeSingle(const int32 UnionIndex, TArray<PCGExData::FWeightedPoint>& OutWeightedPoints, TArray<PCGEx::FOpStats>& Trackers) const override;

		void Cleanup(FPCGExContext* InContext);

	protected:
		const TArray<TObjectPtr<const UPCGExBlendOpFactory>>* BlendingFactories = nullptr;

		const PCGExMath::IDistances* Distances = nullptr;

		TArray<TSharedPtr<FBlendOpsManager>> Blenders;
		TSharedPtr<PCGEx::FIndexLookup> IOLookup;
		TArray<const UPCGBasePointData*> SourcesData;

		TSharedPtr<PCGExData::FUnionMetadata> CurrentUnionMetadata;
		TSharedPtr<PCGExData::FFacade> CurrentTargetData;

		TArray<FPCGExBlendOperation*> UniqueOps; // One per unique attribute, for Begin/End
	};
}
