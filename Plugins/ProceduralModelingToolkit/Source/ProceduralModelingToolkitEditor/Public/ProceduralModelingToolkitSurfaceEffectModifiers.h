#pragma once

#include "CoreMinimal.h"
#include "ProceduralModelingToolkitModifier.h"
#include "ProceduralModelingToolkitSurfaceEffectModifiers.generated.h"

UCLASS(BlueprintType, EditInlineNew, DefaultToInstanced)
class UProceduralModelingToolkitCracksModifier : public UProceduralModelingToolkitModifier
{
	GENERATED_BODY()

public:
	UProceduralModelingToolkitCracksModifier();
	virtual FProceduralModelingToolkitModifierResult Execute(UDynamicMesh* TargetMesh, const FProceduralModelingToolkitModifierExecutionContext& Context) override;
};

UCLASS(BlueprintType, EditInlineNew, DefaultToInstanced)
class UProceduralModelingToolkitDamageModifier : public UProceduralModelingToolkitModifier
{
	GENERATED_BODY()

public:
	UProceduralModelingToolkitDamageModifier();
	virtual FProceduralModelingToolkitModifierResult Execute(UDynamicMesh* TargetMesh, const FProceduralModelingToolkitModifierExecutionContext& Context) override;
};

UCLASS(BlueprintType, EditInlineNew, DefaultToInstanced)
class UProceduralModelingToolkitEdgeWearModifier : public UProceduralModelingToolkitModifier
{
	GENERATED_BODY()

public:
	UProceduralModelingToolkitEdgeWearModifier();
	virtual FProceduralModelingToolkitModifierResult Execute(UDynamicMesh* TargetMesh, const FProceduralModelingToolkitModifierExecutionContext& Context) override;
};

UCLASS(BlueprintType, EditInlineNew, DefaultToInstanced)
class UProceduralModelingToolkitDirtModifier : public UProceduralModelingToolkitModifier
{
	GENERATED_BODY()

public:
	UProceduralModelingToolkitDirtModifier();
	virtual FProceduralModelingToolkitModifierResult Execute(UDynamicMesh* TargetMesh, const FProceduralModelingToolkitModifierExecutionContext& Context) override;
};

UCLASS(BlueprintType, EditInlineNew, DefaultToInstanced)
class UProceduralModelingToolkitMossModifier : public UProceduralModelingToolkitModifier
{
	GENERATED_BODY()

public:
	UProceduralModelingToolkitMossModifier();
	virtual FProceduralModelingToolkitModifierResult Execute(UDynamicMesh* TargetMesh, const FProceduralModelingToolkitModifierExecutionContext& Context) override;
};

UCLASS(BlueprintType, EditInlineNew, DefaultToInstanced)
class UProceduralModelingToolkitRustModifier : public UProceduralModelingToolkitModifier
{
	GENERATED_BODY()

public:
	UProceduralModelingToolkitRustModifier();
	virtual FProceduralModelingToolkitModifierResult Execute(UDynamicMesh* TargetMesh, const FProceduralModelingToolkitModifierExecutionContext& Context) override;
};

UCLASS(BlueprintType, EditInlineNew, DefaultToInstanced)
class UProceduralModelingToolkitSnowModifier : public UProceduralModelingToolkitModifier
{
	GENERATED_BODY()

public:
	UProceduralModelingToolkitSnowModifier();
	virtual FProceduralModelingToolkitModifierResult Execute(UDynamicMesh* TargetMesh, const FProceduralModelingToolkitModifierExecutionContext& Context) override;
};

UCLASS(BlueprintType, EditInlineNew, DefaultToInstanced)
class UProceduralModelingToolkitVertexPaintModifier : public UProceduralModelingToolkitModifier
{
	GENERATED_BODY()

public:
	UProceduralModelingToolkitVertexPaintModifier();
	virtual FProceduralModelingToolkitModifierResult Execute(UDynamicMesh* TargetMesh, const FProceduralModelingToolkitModifierExecutionContext& Context) override;
};
