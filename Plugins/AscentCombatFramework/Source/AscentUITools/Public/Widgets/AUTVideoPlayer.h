// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CommonVideoPlayer.h"
#include "CoreMinimal.h"
#include <Delegates/Delegate.h>

#include "AUTVideoPlayer.generated.h"


DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnPlaybackStateEvent);



/**
 * UACFVideoPlayerWidget
 *
 * A widget that extends CommonVideoPlayer to support audio playback
 * and extending the functionality of the video player to Blueprints.
 */
UCLASS()
class ASCENTUITOOLS_API UAUTVideoPlayer : public UCommonVideoPlayer {
    GENERATED_BODY()

public:

    UPROPERTY(BlueprintAssignable, Category = AUT)
    FOnPlaybackStateEvent OnPlaybackCompletedEvent;

    UPROPERTY(BlueprintAssignable, Category = AUT)
    FOnPlaybackStateEvent OnPlaybackPausedEvent;

    UPROPERTY(BlueprintAssignable, Category = AUT)
    FOnPlaybackStateEvent OnPlaybackResumedEvent;

protected:
    /** Override of base media event handler */
    virtual void HandleMediaPlayerEvent(EMediaEvent EventType) override;
};
