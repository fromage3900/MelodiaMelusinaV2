// Copyright 2024 Tore Lervik. All Rights Reserved.


#include "MeshBlendWorldPartitionRuntimeCellTransformer.h"
#include "MeshBlendLevelProcessor.h"
#include "Engine/Level.h"

UMeshBlendWorldPartitionRuntimeCellTransformer::UMeshBlendWorldPartitionRuntimeCellTransformer(const FObjectInitializer& ObjectInitializer)
	: Super(ObjectInitializer)
{
    MeshBlendProcessor = CreateDefaultSubobject<UMeshBlendProcessor>(TEXT("MeshBlendProcessor"));
}

#if WITH_EDITOR

void UMeshBlendWorldPartitionRuntimeCellTransformer::Transform(ULevel* InLevel)
{
    FMeshBlendLevelProcessor::Transform(InLevel, MeshBlendProcessor, true);
}

#endif