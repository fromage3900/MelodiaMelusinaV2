// Copyright 2026 Timothé Lapetite and contributors
// Released under the MIT license https://opensource.org/license/MIT/

#include "Core/PCGExShapeConfigBase.h"
#include "Details/PCGExSettingsDetails.h"

void FPCGExShapeConfigBase::Init()
{
	FQuat A = FQuat::Identity;
	FQuat B = FQuat::Identity;
	switch (SourceAxis)
	{
	case EPCGExAxisAlign::Forward:
		A = FRotationMatrix::MakeFromX(FVector::ForwardVector).ToQuat().Inverse();
		break;
	case EPCGExAxisAlign::Backward:
		A = FRotationMatrix::MakeFromX(FVector::BackwardVector).ToQuat().Inverse();
		break;
	case EPCGExAxisAlign::Right:
		A = FRotationMatrix::MakeFromX(FVector::RightVector).ToQuat().Inverse();
		break;
	case EPCGExAxisAlign::Left:
		A = FRotationMatrix::MakeFromX(FVector::LeftVector).ToQuat().Inverse();
		break;
	case EPCGExAxisAlign::Up:
		A = FRotationMatrix::MakeFromX(FVector::UpVector).ToQuat().Inverse();
		break;
	case EPCGExAxisAlign::Down:
		A = FRotationMatrix::MakeFromX(FVector::DownVector).ToQuat().Inverse();
		break;
	}

	switch (TargetAxis)
	{
	case EPCGExAxisAlign::Forward:
		B = FRotationMatrix::MakeFromX(FVector::ForwardVector).ToQuat();
		break;
	case EPCGExAxisAlign::Backward:
		B = FRotationMatrix::MakeFromX(FVector::BackwardVector).ToQuat();
		break;
	case EPCGExAxisAlign::Right:
		B = FRotationMatrix::MakeFromX(FVector::RightVector).ToQuat();
		break;
	case EPCGExAxisAlign::Left:
		B = FRotationMatrix::MakeFromX(FVector::LeftVector).ToQuat();
		break;
	case EPCGExAxisAlign::Up:
		B = FRotationMatrix::MakeFromX(FVector::UpVector).ToQuat();
		break;
	case EPCGExAxisAlign::Down:
		B = FRotationMatrix::MakeFromX(FVector::DownVector).ToQuat();
		break;
	}

	LocalTransform = FTransform(A * B, FVector::ZeroVector, FVector::OneVector);
}

#if WITH_EDITOR
void FPCGExShapeConfigBase::ApplyDeprecation()
{
	Resolution.Update(ResolutionInput_DEPRECATED, ResolutionAttribute_DEPRECATED, ResolutionConstant_DEPRECATED);
	ResolutionVector.Update(ResolutionInput_DEPRECATED, ResolutionAttribute_DEPRECATED, ResolutionConstantVector_DEPRECATED);
}
#endif
