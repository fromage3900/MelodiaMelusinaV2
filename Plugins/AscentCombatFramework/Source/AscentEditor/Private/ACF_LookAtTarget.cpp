// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ACF_LookAtTarget.h"
#include "AnimNodeEditModes.h"


UACF_LookAtTarget::UACF_LookAtTarget(const FObjectInitializer& ObjectInitializer)
    : Super(ObjectInitializer)
{
}
FText UACF_LookAtTarget::GetNodeTitle(ENodeTitleType::Type TitleType) const
{
    return FText::FromString("ACF Look At Target");
}

FText UACF_LookAtTarget::GetTooltipText() const
{
    return FText::FromString("This node allow a bone to trace or follow another bone");
}

// FEditorModeID UACF_LookAtTarget::GetEditorMode() const
// {
//  	return AnimNodeEditModes::LookAt;
// }

FText UACF_LookAtTarget::GetControllerDescription() const
{
    return FText::FromString( "Look At Target");
}

void UACF_LookAtTarget::Serialize(FArchive& Ar)
{
    Super::Serialize(Ar);

    Ar.UsingCustomVersion(FAnimPhysObjectVersion::GUID);

    auto GetAlignVector = [](EAxisOption::Type AxisOption, const FVector& CustomAxis) -> FVector {
        switch (AxisOption) {
        case EAxisOption::X:
            return FTransform::Identity.GetUnitAxis(EAxis::X);
        case EAxisOption::X_Neg:
            return -FTransform::Identity.GetUnitAxis(EAxis::X);
        case EAxisOption::Y:
            return FTransform::Identity.GetUnitAxis(EAxis::Y);
        case EAxisOption::Y_Neg:
            return -FTransform::Identity.GetUnitAxis(EAxis::Y);
        case EAxisOption::Z:
            return FTransform::Identity.GetUnitAxis(EAxis::Z);
        case EAxisOption::Z_Neg:
            return -FTransform::Identity.GetUnitAxis(EAxis::Z);
        case EAxisOption::Custom:
            return CustomAxis;
        }

        return FVector(1.f, 0.f, 0.f);
    };

}
