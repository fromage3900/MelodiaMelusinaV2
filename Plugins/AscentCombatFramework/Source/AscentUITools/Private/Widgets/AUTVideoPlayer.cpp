// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.


#include "Widgets/AUTVideoPlayer.h"
#include <CommonVideoPlayer.h>
#include <IMediaEventSink.h>

void UAUTVideoPlayer::HandleMediaPlayerEvent(EMediaEvent EventType)
{
    // Call parent first to preserve base behavior
    Super::HandleMediaPlayerEvent(EventType);

    switch (EventType) {
    case EMediaEvent::MediaOpened:
    case EMediaEvent::TracksChanged:

        break;

    case EMediaEvent::PlaybackEndReached:
        OnPlaybackCompletedEvent.Broadcast();
        break;

    case EMediaEvent::PlaybackResumed:
        OnPlaybackResumedEvent.Broadcast();
        break;
    case EMediaEvent::PlaybackSuspended:
        OnPlaybackPausedEvent.Broadcast();
        break;
    case EMediaEvent::MediaClosed:
        break;
    default:
        break;
    }
}
