// Copyright UNAmedia. All rights reserved.

#pragma once

#include "Templates/UnrealTemplate.h"

class ULocalPlayer;
class APlayerController;
class UWorld;

/**
 Utility class to force the LocalPlayer's World to be the one given in input 
 and assign the right PlayerController for the duration of this context.
 Do nothing if the local player is already in the desired world.
 In destruction it restore the previous state.

 The LocalPlayer's (LP) World is always equal to the world that it's ticking 
 but if we call functions of a different world (e.g just consider delegates),
 calling LocalPlayer->GetWorld() or LocalPlayer->PlayerController, 
 we could get a different world / player controller from what we wait for.

 This utility class is useful when we want to force the local player "to be" in a world before
 calling functions that make use the local player to get the world or the PlayerController
 (e.g ULocalPlayer::GetSubsystem<UEnhancedInputLocalPlayerSubsystem>(LocalPlayer); ).
*/
struct MULTIWORLD_API FScopeLocalPlayerOnWorld final : public FNoncopyable
{
	FScopeLocalPlayerOnWorld(ULocalPlayer* LP, UWorld* World);
	~FScopeLocalPlayerOnWorld();

private:

	ULocalPlayer* LP_ = nullptr;
	APlayerController* PC_ = nullptr;
	UWorld* World_ = nullptr;
};
