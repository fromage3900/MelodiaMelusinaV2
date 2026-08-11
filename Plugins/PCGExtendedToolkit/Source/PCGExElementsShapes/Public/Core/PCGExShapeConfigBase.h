// Copyright 2026 Timothé Lapetite and contributors
// Released under the MIT license https://opensource.org/license/MIT/

#pragma once

#include "CoreMinimal.h"
#include "PCGExCommon.h"
#include "Details/PCGExSettingsMacros.h"
#include "Math/PCGExMathAxis.h"

#include "PCGExShapesCommon.h"
#include "Data/PCGExDataCommon.h"
#include "Details/PCGExInputShorthandsDetails.h"
#include "Fitting/PCGExFitting.h"

#include "PCGExShapeConfigBase.generated.h"

USTRUCT(BlueprintType)
struct PCGEXELEMENTSSHAPES_API FPCGExShapeConfigBase
{
	GENERATED_BODY()

	FPCGExShapeConfigBase()
	{
	}

	explicit FPCGExShapeConfigBase(const bool InThreeDimensions)
		: bThreeDimensions(InThreeDimensions)
	{
	}

	virtual ~FPCGExShapeConfigBase()
	{
	}

	UPROPERTY(meta = (PCG_NotOverridable))
	bool bThreeDimensions = false;

	/** Resolution mode */
	UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = "Settings|Resolution", meta = (PCG_Overridable))
	EPCGExResolutionMode ResolutionMode = EPCGExResolutionMode::Fixed;

	/** Resolution. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = Settings, meta = (PCG_Overridable, EditCondition="!bThreeDimensions", EditConditionHides, HideEditConditionToggle))
	FPCGExInputShorthandSelectorDoubleAbs Resolution = FPCGExInputShorthandSelectorDoubleAbs(FName("Resolution"), 10, false);

	/** Resolution. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = Settings, meta = (PCG_Overridable, EditCondition="bThreeDimensions", EditConditionHides, HideEditConditionToggle))
	FPCGExInputShorthandSelectorVector ResolutionVector = FPCGExInputShorthandSelectorVector(FName("Resolution"), FVector(10), false);

#pragma region DEPRECATED

	UPROPERTY(meta=(DeprecatedProperty, ScriptNoExport))
	EPCGExInputValueType ResolutionInput_DEPRECATED = EPCGExInputValueType::Constant;

	UPROPERTY(meta=(DeprecatedProperty, ScriptNoExport))
	FPCGAttributePropertyInputSelector ResolutionAttribute_DEPRECATED;

	UPROPERTY(meta=(DeprecatedProperty, ScriptNoExport))
	double ResolutionConstant_DEPRECATED = 10;

	UPROPERTY(meta=(DeprecatedProperty, ScriptNoExport))
	FVector ResolutionConstantVector_DEPRECATED = FVector(10);

#pragma endregion

	/** Fitting details */
	UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = Settings, meta = (PCG_Overridable))
	FPCGExFittingDetailsHandler Fitting;

	/** Axis on the source to remap to a target axis on the shape */
	UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = "Settings|Align", meta=(PCG_Overridable))
	EPCGExAxisAlign SourceAxis = EPCGExAxisAlign::Forward;

	/** Shape axis to align to the source axis */
	UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = "Settings|Align", meta=(PCG_Overridable))
	EPCGExAxisAlign TargetAxis = EPCGExAxisAlign::Forward;

	/** Points look at */
	UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = "Settings|Align", meta=(PCG_Overridable))
	EPCGExShapePointLookAt PointsLookAt = EPCGExShapePointLookAt::None;

	/** Axis used to align the look at rotation */
	UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = "Settings|Align", meta=(PCG_Overridable))
	EPCGExAxisAlign LookAtAxis = EPCGExAxisAlign::Forward;


	/** How point bounds/extents are determined */
	UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = "Settings|Data", meta=(PCG_Overridable))
	EPCGExShapeBoundsSource BoundsSource = EPCGExShapeBoundsSource::Fit;

	/** Default point extents (used when BoundsSource is Constant) */
	UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = "Settings|Data", meta=(PCG_Overridable, EditCondition="BoundsSource == EPCGExShapeBoundsSource::Constant", EditConditionHides))
	FVector DefaultExtents = FVector::OneVector * 50;

	/** Shape ID used to identify this specific shape' points */
	UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = "Settings|Data", meta=(PCG_Overridable))
	int32 ShapeId = 0;


	/** Don't output shape if they have less points than a specified amount. */
	UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = "Settings|Pruning", meta = (PCG_Overridable, InlineEditConditionToggle))
	bool bRemoveBelow = true;

	/** Discarded if point count is less than */
	UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = "Settings|Pruning", meta=(PCG_Overridable, EditCondition="bRemoveBelow", ClampMin=0))
	int32 MinPointCount = 2;

	/** Don't output shape if they have more points than a specified amount. */
	UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = "Settings|Pruning", meta = (PCG_Overridable, InlineEditConditionToggle))
	bool bRemoveAbove = false;

	/** Discarded if point count is more than */
	UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = "Settings|Pruning", meta=(PCG_Overridable, EditCondition="bRemoveAbove", ClampMin=0))
	int32 MaxPointCount = 500;


	FTransform LocalTransform = FTransform::Identity;

	virtual void Init();

#if WITH_EDITOR
	virtual void ApplyDeprecation();
#endif
};
