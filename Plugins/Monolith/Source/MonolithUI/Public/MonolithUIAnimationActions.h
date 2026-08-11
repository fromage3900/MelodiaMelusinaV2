// MonolithUIAnimationActions.h
#pragma once

#include "MonolithToolRegistry.h"

class FMonolithUIAnimationActions
{
public:
    static void RegisterActions(FMonolithToolRegistry& Registry);

    static FMonolithActionResult HandleListAnimations(const TSharedPtr<FJsonObject>& Params);
    static FMonolithActionResult HandleGetAnimationDetails(const TSharedPtr<FJsonObject>& Params);
    static FMonolithActionResult HandleCreateAnimation(const TSharedPtr<FJsonObject>& Params);
    static FMonolithActionResult HandleAddAnimationKeyframe(const TSharedPtr<FJsonObject>& Params);
    static FMonolithActionResult HandleRemoveAnimation(const TSharedPtr<FJsonObject>& Params);
};
