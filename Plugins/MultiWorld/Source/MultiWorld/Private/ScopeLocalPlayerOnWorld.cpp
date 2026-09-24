// Copyright UNAmedia. All rights reserved.

#include "ScopeLocalPlayerOnWorld.h"

#include "Engine/LocalPlayer.h"
#include "Engine/World.h"
#include "Engine/GameViewportClient.h"
#include "GameFramework/PlayerController.h"
#include "Kismet/GameplayStatics.h"

namespace FScopeLocalPlayerOnWorld_Internal 
{
	//Note: ULocalPlayer::GetWorld() gets the world from the game viewport.For this reason
	//we have to change the viewport's world.
	class GameViewportClientEx : public UGameViewportClient
	{
	public:

		void SetWorld(UWorld* InWorld)
		{
			World = InWorld;
		}
	};

}

FScopeLocalPlayerOnWorld::FScopeLocalPlayerOnWorld(ULocalPlayer* LP, UWorld* World)
{
	check(LP);
	check(World);

	if (LP->GetWorld() == World)
	{
		return;
	}

	LP_ = LP;
	PC_ = LP->PlayerController;
	World_ = LP->GetWorld();
	static_cast<FScopeLocalPlayerOnWorld_Internal::GameViewportClientEx*>(LP->ViewportClient)->SetWorld(World);
	LP->PlayerController = UGameplayStatics::GetPlayerControllerFromID(World, LP->GetControllerId());
	check(LP->PlayerController);
	//check(LP->PlayerController != PC_);
	check(LP->GetWorld() == World);
}

FScopeLocalPlayerOnWorld::~FScopeLocalPlayerOnWorld()
{
	if (LP_ && PC_ && World_)
	{
		LP_->PlayerController = PC_;
		static_cast<FScopeLocalPlayerOnWorld_Internal::GameViewportClientEx*>(LP_->ViewportClient)->SetWorld(World_);
	}
}