#pragma once

#include "CoreMinimal.h"
#include "ProceduralModelingToolkitModifier.h"
#include "ProceduralModelingToolkitAdvancedModifiers.generated.h"

UCLASS(BlueprintType, EditInlineNew, DefaultToInstanced)
class UProceduralModelingToolkitExtrudeModifier : public UProceduralModelingToolkitModifier
{
	GENERATED_BODY()

public:
	UProceduralModelingToolkitExtrudeModifier();
	virtual FProceduralModelingToolkitModifierResult Execute(UDynamicMesh* TargetMesh, const FProceduralModelingToolkitModifierExecutionContext& Context) override;
};

UCLASS(BlueprintType, EditInlineNew, DefaultToInstanced)
class UProceduralModelingToolkitInsetModifier : public UProceduralModelingToolkitModifier
{
	GENERATED_BODY()

public:
	UProceduralModelingToolkitInsetModifier();
	virtual FProceduralModelingToolkitModifierResult Execute(UDynamicMesh* TargetMesh, const FProceduralModelingToolkitModifierExecutionContext& Context) override;
};

UCLASS(BlueprintType, EditInlineNew, DefaultToInstanced)
class UProceduralModelingToolkitRemeshModifier : public UProceduralModelingToolkitModifier
{
	GENERATED_BODY()

public:
	UProceduralModelingToolkitRemeshModifier();
	virtual FProceduralModelingToolkitModifierResult Execute(UDynamicMesh* TargetMesh, const FProceduralModelingToolkitModifierExecutionContext& Context) override;
};

UCLASS(BlueprintType, EditInlineNew, DefaultToInstanced)
class UProceduralModelingToolkitSimplifyModifier : public UProceduralModelingToolkitModifier
{
	GENERATED_BODY()

public:
	UProceduralModelingToolkitSimplifyModifier();
	virtual FProceduralModelingToolkitModifierResult Execute(UDynamicMesh* TargetMesh, const FProceduralModelingToolkitModifierExecutionContext& Context) override;
};

UCLASS(BlueprintType, EditInlineNew, DefaultToInstanced)
class UProceduralModelingToolkitTwistModifier : public UProceduralModelingToolkitModifier
{
	GENERATED_BODY()

public:
	UProceduralModelingToolkitTwistModifier();
	virtual FProceduralModelingToolkitModifierResult Execute(UDynamicMesh* TargetMesh, const FProceduralModelingToolkitModifierExecutionContext& Context) override;
};

UCLASS(BlueprintType, EditInlineNew, DefaultToInstanced)
class UProceduralModelingToolkitBendModifier : public UProceduralModelingToolkitModifier
{
	GENERATED_BODY()

public:
	UProceduralModelingToolkitBendModifier();
	virtual FProceduralModelingToolkitModifierResult Execute(UDynamicMesh* TargetMesh, const FProceduralModelingToolkitModifierExecutionContext& Context) override;
};

UCLASS(BlueprintType, EditInlineNew, DefaultToInstanced)
class UProceduralModelingToolkitInflateModifier : public UProceduralModelingToolkitModifier
{
	GENERATED_BODY()

public:
	UProceduralModelingToolkitInflateModifier();
	virtual FProceduralModelingToolkitModifierResult Execute(UDynamicMesh* TargetMesh, const FProceduralModelingToolkitModifierExecutionContext& Context) override;
};
