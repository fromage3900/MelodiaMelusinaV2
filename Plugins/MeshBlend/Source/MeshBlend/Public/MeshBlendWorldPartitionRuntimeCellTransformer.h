// Copyright 2024 Tore Lervik. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "WorldPartition/WorldPartitionRuntimeCellTransformer.h"
#include "MeshBlendProcessor.h"
#include "MeshBlendWorldPartitionRuntimeCellTransformer.generated.h"

UCLASS()
class MESHBLEND_API UMeshBlendWorldPartitionRuntimeCellTransformer : public UWorldPartitionRuntimeCellTransformer
{
	GENERATED_UCLASS_BODY()
	
#if WITH_EDITOR

public:
	virtual void Transform(ULevel* InLevel) override;
#endif
	
private :
    UPROPERTY(Transient, DuplicateTransient)
    TObjectPtr<UMeshBlendProcessor> MeshBlendProcessor;
};
