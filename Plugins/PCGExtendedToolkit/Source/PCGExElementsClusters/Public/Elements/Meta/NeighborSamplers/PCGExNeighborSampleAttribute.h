// Copyright 2026 Timothé Lapetite and contributors
// Released under the MIT license https://opensource.org/license/MIT/

#pragma once

#include "CoreMinimal.h"
#include "UObject/Object.h"

#include "Details/PCGExBlendingDetails.h"
#include "Factories/PCGExFactoryProvider.h"

#include "PCGExNeighborSampleFactoryProvider.h"

#include "PCGExNeighborSampleAttribute.generated.h"

///

USTRUCT(BlueprintType, meta=(Hidden=true))
struct FPCGExAttributeSamplerConfigBase
{
	GENERATED_BODY()

	FPCGExAttributeSamplerConfigBase()
	{
	}

	/** Unique blendmode applied to all specified attributes. For different blendmodes, create multiple sampler nodes. */
	UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = Settings, meta=(PCG_Overridable))
	EPCGExBlendingType Blending = EPCGExBlendingType::Average;

	/** Attribute to sample & optionally remap. Leave it to None to overwrite the source attribute.  */
	UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = Settings, meta=(PCG_Overridable, ShowOnlyInnerProperties))
	FPCGExAttributeSourceToTargetList SourceAttributes;
};

UCLASS(Hidden, MinimalAPI, BlueprintType, ClassGroup = (Procedural), Category="PCGEx|Data")
class UPCGExNeighborSamplerFactoryAttribute : public UPCGExNeighborSamplerFactoryData
{
	GENERATED_BODY()

public:
	virtual TSharedPtr<FPCGExNeighborSampleOperation> CreateOperation(FPCGExContext* InContext) const override;
};
