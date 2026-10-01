// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "Graph/ACFComboNode.h"
#include "Graph/ACFComboGraph.h"
#include "Math/Color.h"
#include <Kismet/GameplayStatics.h>

void UACFComboNode::ActivateNode()
{
    Super::ActivateNode();
    UACFComboGraph* combo = Cast<UACFComboGraph>(Graph);

}

void UACFComboNode::DeactivateNode()
{
    Super::DeactivateNode();
}

UACFComboNode::UACFComboNode()
{
#if WITH_EDITOR
    BackgroundColor = FLinearColor::Blue;
#endif
}
