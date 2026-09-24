// Copyright 2019-2020 UNAmedia. All rights reserved.

#pragma once

#include "CoreMinimal.h"

class UWorld;
class FViewport;
class FOutputDevice;
class UGameInstance;
class UGameViewportClient;
class ULocalPlayer;

/**
All functions that MUST be overridden for the correct behaviour of the MultiWorld plugin.

To properly work, the MultiWorld plugin requires to "hook" into some specific callbacks of Unreal Engine.
Ready-to-use classes (see links below) are provided for the user, that can simply configure them in the "Project Settings".
For more general uses, where the provided pre-made classes can't be used, the user MUST provide all the required hooks.

The user @b MUST guarantee that @b ALL the methods in this class are invoked <b>INSTEAD OF</b> the corresponding Unreal Engine implementations.
Follow the documentation in each method.

@see UMultiWorldGameInstance
@see UMultiWorldGameViewportClient
*/
class MULTIWORLD_API UMultiWorldOverrides final
{
public:
    UMultiWorldOverrides() = delete;

	/** @name UGameInstance overrides
	@{
	*/

    /**
     * This function must be invoked instead of <a href="https://docs.unrealengine.com/en-US/API/Runtime/Engine/Engine/UGameInstance/Exec/index.html">UGameInstance::Exec()</a>.
	 *
     * This implementation prevents that incompatible commands are invoked on the secondary worlds.
     * UGameInstance::Exec is called inside.
     */
    static bool GameInstance_Exec(UGameInstance* Caller, UWorld* InWorld, const TCHAR* Cmd, FOutputDevice& Ar);

    /**
     * This function must be invoked instead of <a href="https://docs.unrealengine.com/en-US/API/Runtime/Engine/Engine/UGameInstance/OnWorldChanged/index.html">UGameInstance::OnWorldChanged()</a>.
	 *
	 * This implementation ensures to forward the event to UMultiWorldManager.
     * UGameInstance::OnWorldChanged is called inside.
     */
    static void GameInstance_OnWorldChanged(UGameInstance* Caller, UWorld* OldWorld, UWorld* NewWorld);

	/// @}

	/** @name UGameViewportClient overrides
	@{
	*/

    /**
     * This function must be invoked overriding <a href="https://docs.unrealengine.com/en-US/API/Runtime/Engine/Engine/UGameViewportClient/AddViewportWidgetContent/index.html">UGameViewportClient::AddViewportWidgetContent()</a>.
     * UGameViewportClient::AddViewportWidgetContent is called inside.
     */
    static void GameViewportClient_AddViewportWidgetContent(UGameViewportClient* Caller, TSharedRef<class SWidget> ViewportContent, const int32 ZOrder = 0);

    /**
     * This function must be invoked overriding <a href="https://docs.unrealengine.com/en-US/API/Runtime/Engine/Engine/UGameViewportClient/AddViewportWidgetForPlayer/index.html">UGameViewportClient::AddViewportWidgetForPlayer()</a>.
     * UGameViewportClient::AddViewportWidgetForPlayer is called inside.
     */
    static void GameViewportClient_AddViewportWidgetForPlayer(UGameViewportClient* Caller, ULocalPlayer* Player, TSharedRef<SWidget> ViewportContent, const int32 ZOrder);

    /**
     * This function must be invoked overriding <a href="https://docs.unrealengine.com/en-US/API/Runtime/Engine/Engine/UGameViewportClient/RemoveViewportWidgetContent/index.html">UGameViewportClient::RemoveViewportWidgetContent()</a>.
     * UGameViewportClient::RemoveViewportWidgetContent is called inside.
     */
    static void GameViewportClient_RemoveViewportWidgetContent(UGameViewportClient* Caller, TSharedRef<SWidget> ViewportContent);

    /**
     * This function must be invoked overriding <a href="https://docs.unrealengine.com/en-US/API/Runtime/Engine/Engine/UGameViewportClient/RemoveViewportWidgetForPlayer/index.html">UGameViewportClient::RemoveViewportWidgetForPlayer()</a>.
     * UGameViewportClient::RemoveViewportWidgetForPlayer is called inside.
     */
    static void GameViewportClient_RemoveViewportWidgetForPlayer(UGameViewportClient* Caller, ULocalPlayer* Player, TSharedRef<SWidget> ViewportContent);
    
    /**
     * This function must be invoked overriding <a href="https://docs.unrealengine.com/en-US/API/Runtime/Engine/Engine/UGameViewportClient/ReceivedFocus/index.html">UGameViewportClient::ReceivedFocus()</a>.
	 *
     * The base behaviour, about the audio, is to activate the main audio device when the viewport
     * receive the focus. Instead, being in a multi-world context,
     * we activate the audio device associated with current active world.
     * UGameViewportClient::ReceivedFocus is called inside.
     */
    static void GameViewportClient_ReceivedFocus(UGameViewportClient* Caller, FViewport* InViewport);

    /**
     * This function must be invoked overriding <a href="https://docs.unrealengine.com/en-US/API/Runtime/Engine/Engine/UGameViewportClient/LayoutPlayers/index.html">UGameViewportClient::LayoutPlayers()</a>.
     * UGameViewportClient::LayoutPlayers is called inside.
     */
    static void GameViewportClient_LayoutPlayers(UGameViewportClient* Caller);

    /**
     * This function must be invoked overriding <a href="https://docs.unrealengine.com/en-US/API/Runtime/Engine/Engine/UGameViewportClient/Tick/index.html">UGameViewportClient::Tick(float)</a>.
     * UGameViewportClient::Tick is called inside.
     */
    static void GameViewportClient_Tick(UGameViewportClient* Caller, float DeltaTime);

	/// @}

#if WITH_EDITOR

private:

    static bool ShouldTickAndDraw(UGameViewportClient* ViewportClient);

#endif
};
