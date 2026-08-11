#pragma once

#include "CoreMinimal.h"
#include "ProceduralModelingToolkitModifier.h"
#include "ProceduralModelingToolkitBasicModifiers.generated.h"

UCLASS(BlueprintType, EditInlineNew, DefaultToInstanced)
class UProceduralModelingToolkitTranslateModifier : public UProceduralModelingToolkitModifier
{
	GENERATED_BODY()

public:
	UProceduralModelingToolkitTranslateModifier();
	virtual FProceduralModelingToolkitModifierResult Execute(UDynamicMesh* TargetMesh, const FProceduralModelingToolkitModifierExecutionContext& Context) override;
};

UCLASS(BlueprintType, EditInlineNew, DefaultToInstanced)
class UProceduralModelingToolkitRotateModifier : public UProceduralModelingToolkitModifier
{
	GENERATED_BODY()

public:
	UProceduralModelingToolkitRotateModifier();
	virtual FProceduralModelingToolkitModifierResult Execute(UDynamicMesh* TargetMesh, const FProceduralModelingToolkitModifierExecutionContext& Context) override;
};

UCLASS(BlueprintType, EditInlineNew, DefaultToInstanced)
class UProceduralModelingToolkitScaleModifier : public UProceduralModelingToolkitModifier
{
	GENERATED_BODY()

public:
	UProceduralModelingToolkitScaleModifier();
	virtual FProceduralModelingToolkitModifierResult Execute(UDynamicMesh* TargetMesh, const FProceduralModelingToolkitModifierExecutionContext& Context) override;
};

UCLASS(BlueprintType, EditInlineNew, DefaultToInstanced)
class UProceduralModelingToolkitMirrorModifier : public UProceduralModelingToolkitModifier
{
	GENERATED_BODY()

public:
	UProceduralModelingToolkitMirrorModifier();
	virtual FProceduralModelingToolkitModifierResult Execute(UDynamicMesh* TargetMesh, const FProceduralModelingToolkitModifierExecutionContext& Context) override;
};

UCLASS(BlueprintType, EditInlineNew, DefaultToInstanced)
class UProceduralModelingToolkitNoiseModifier : public UProceduralModelingToolkitModifier
{
	GENERATED_BODY()

public:
	UProceduralModelingToolkitNoiseModifier();
	virtual FProceduralModelingToolkitModifierResult Execute(UDynamicMesh* TargetMesh, const FProceduralModelingToolkitModifierExecutionContext& Context) override;
};

UCLASS(BlueprintType, EditInlineNew, DefaultToInstanced)
class UProceduralModelingToolkitSmoothModifier : public UProceduralModelingToolkitModifier
{
	GENERATED_BODY()

public:
	UProceduralModelingToolkitSmoothModifier();
	virtual FProceduralModelingToolkitModifierResult Execute(UDynamicMesh* TargetMesh, const FProceduralModelingToolkitModifierExecutionContext& Context) override;
};

UCLASS(BlueprintType, EditInlineNew, DefaultToInstanced)
class UProceduralModelingToolkitRecomputeNormalsModifier : public UProceduralModelingToolkitModifier
{
	GENERATED_BODY()

public:
	UProceduralModelingToolkitRecomputeNormalsModifier();
	virtual FProceduralModelingToolkitModifierResult Execute(UDynamicMesh* TargetMesh, const FProceduralModelingToolkitModifierExecutionContext& Context) override;
};
