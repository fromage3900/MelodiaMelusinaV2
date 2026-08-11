// Copyright 2026 Timothé Lapetite and contributors
// Released under the MIT license https://opensource.org/license/MIT/

#pragma once

#include "CoreMinimal.h"
#include "UObject/Object.h"

#include "Details/PCGExBlendingDetails.h"
#include "Factories/PCGExFactoryProvider.h"

#include "PCGExNeighborSampleFactoryProvider.h"


#include "PCGExNeighborSampleProperties.generated.h"

///


USTRUCT(BlueprintType, meta=(Hidden=true))
struct FPCGExPropertiesSamplerConfigBase
{
	GENERATED_BODY()

	FPCGExPropertiesSamplerConfigBase()
	{
	}

	/** Properties blending */
	UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = Settings, meta=(PCG_Overridable))
	FPCGExPropertiesBlendingDetails Blending = FPCGExPropertiesBlendingDetails(EPCGExBlendingType::None);
};

UCLASS(MinimalAPI, BlueprintType, ClassGroup = (Procedural), Category="PCGEx|Data")
class UPCGExNeighborSamplerFactoryProperties : public UPCGExNeighborSamplerFactoryData
{
	GENERATED_BODY()

public:
	FPCGExPropertiesSamplerConfigBase Config;
	virtual TSharedPtr<FPCGExNeighborSampleOperation> CreateOperation(FPCGExContext* InContext) const override;
};
