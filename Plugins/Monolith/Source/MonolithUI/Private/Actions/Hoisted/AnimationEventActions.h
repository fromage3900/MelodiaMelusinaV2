// Copyright tumourlove. All Rights Reserved.
#pragma once

#include "CoreMinimal.h"
#include "MonolithToolRegistry.h"

/**
 * MonolithUI -- UMG widget animation event tracks and delegate bindings.
 *
 * add_animation_event_track:  Adds a UMovieSceneEventTrack (master track) to an
 *                             existing UWidgetAnimation on a WBP, with timed event keys.
 * bind_animation_to_event:    Creates a UWidgetAnimationDelegateBinding entry that
 *                             wires a widget interaction event (OnHovered, etc.) to
 *                             play a named animation on Started or Finished.
 *
 * Editor-only -- UWidgetBlueprint::Animations is WITH_EDITORONLY_DATA.
 */
namespace MonolithUI
{
    struct FAnimationEventActions
    {
        static void Register(FMonolithToolRegistry& Registry);

        static FMonolithActionResult HandleAddAnimationEventTrack(const TSharedPtr<FJsonObject>& Params);
        static FMonolithActionResult HandleBindAnimationToEvent(const TSharedPtr<FJsonObject>& Params);
    };
}
