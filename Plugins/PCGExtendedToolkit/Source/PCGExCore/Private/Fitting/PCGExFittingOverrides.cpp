// Copyright 2026 Timothé Lapetite and contributors
// Released under the MIT license https://opensource.org/license/MIT/

#include "Fitting/PCGExFittingOverrides.h"

#include "Data/PCGExData.h"

#pragma region FPCGExLeanScaleToFitDetails

void FPCGExLeanScaleToFitDetails::Process(const PCGExData::FPoint& InPoint, const FBox& InBounds, FVector& OutScale, FBox& OutBounds) const
{
	PCGExFitting::ScaleToFitAxes(
		ScaleToFitMode, ScaleToFit, ScaleToFitX, ScaleToFitY, ScaleToFitZ,
		InPoint.GetLocalBounds().GetSize(), InPoint.GetTransform().GetScale3D(),
		InBounds, OutScale, OutBounds);
}

#pragma endregion

#pragma region FPCGExLeanJustificationDetails

void FPCGExLeanJustificationDetails::Process(const FBox& InBounds, const FBox& OutBounds, FVector& OutTranslation) const
{
	const FVector InCenter = InBounds.GetCenter();
	const FVector InSize = InBounds.GetSize();

	const FVector OutCenter = OutBounds.GetCenter();
	const FVector OutSize = OutBounds.GetSize();

	if (bDoJustifyX)
	{
		PCGExFitting::JustifyAxis(JustifyX.From, JustifyX.To, JustifyX.FromConstant, JustifyX.ToConstant, 0, InCenter, InSize, OutCenter, OutSize, OutTranslation);
	}
	if (bDoJustifyY)
	{
		PCGExFitting::JustifyAxis(JustifyY.From, JustifyY.To, JustifyY.FromConstant, JustifyY.ToConstant, 1, InCenter, InSize, OutCenter, OutSize, OutTranslation);
	}
	if (bDoJustifyZ)
	{
		PCGExFitting::JustifyAxis(JustifyZ.From, JustifyZ.To, JustifyZ.FromConstant, JustifyZ.ToConstant, 2, InCenter, InSize, OutCenter, OutSize, OutTranslation);
	}
}

#pragma endregion
