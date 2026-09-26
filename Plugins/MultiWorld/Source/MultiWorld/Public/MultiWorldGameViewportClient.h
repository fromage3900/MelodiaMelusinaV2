// Copyright 2019-2020 UNAmedia. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Engine/GameViewportClient.h"

#include "MultiWorldGameViewportClient.generated.h"

/**
 * Custom GameViewportClient class needed to support MultiWorld on your project.
 *
 * To set it in your project just open the "Project Settings" panel, 
 * go to "Engine > General Settings",
 * here search for the property "Game Viewport Client Class"
 * and then set it to @c MultiWorldGameViewportClient.
 *
 * If you can't use this implementation, follow the instructions at #UMultiWorldOverrides.
 */
UCLASS()
class MULTIWORLD_API UMultiWorldGameViewportClient : public UGameViewportClient
{
    GENERATED_BODY()

    /**
    Override <a href="https://docs.unrealengine.com/en-US/API/Runtime/Engine/Engine/UGameViewportClient/AddViewportWidgetContent/index.html">UGameViewportClient::AddViewportWidgetContent()</a>
    */
	virtual void AddViewportWidgetContent(TSharedRef<class SWidget> ViewportContent, const int32 ZOrder = 0) override;

    /**
    Override <a href="https://docs.unrealengine.com/en-US/API/Runtime/Engine/Engine/UGameViewportClient/AddViewportWidgetForPlayer/index.html">UGameViewportClient::AddViewportWidgetForPlayer()</a>
    */
	virtual void AddViewportWidgetForPlayer(ULocalPlayer* Player, TSharedRef<SWidget> ViewportContent, const int32 ZOrder) override;

    /**
    Override <a href="https://docs.unrealengine.com/en-US/API/Runtime/Engine/Engine/UGameViewportClient/RemoveViewportWidgetContent/index.html">UGameViewportClient::RemoveViewportWidgetContent()</a>
    */
    virtual void RemoveViewportWidgetContent(TSharedRef<class SWidget> ViewportContent) override;

    /**
    Override <a href="https://docs.unrealengine.com/en-US/API/Runtime/Engine/Engine/UGameViewportClient/RemoveViewportWidgetForPlayer/index.html">UGameViewportClient::RemoveViewportWidgetForPlayer()</a>
    */
    virtual void RemoveViewportWidgetForPlayer(ULocalPlayer* Player, TSharedRef<SWidget> ViewportContent) override;

    /** 
	Override of <a href="https://docs.unrealengine.com/en-US/API/Runtime/Engine/Engine/UGameViewportClient/ReceivedFocus/index.html">UGameViewportClient::ReceivedFocus()</a>

    The base behaviour, about the audio, is to activate the main audio device when the viewport
    receive the focus. Instead, being in a multi-world context, 
    we activate the audio device associated with current active world.
    */
    virtual void ReceivedFocus(FViewport* Viewport) override;

    /**
    Override <a href="https://docs.unrealengine.com/en-US/API/Runtime/Engine/Engine/UGameViewportClient/LayoutPlayers/index.html">UGameViewportClient::LayoutPlayers()</a>
    */
    virtual void LayoutPlayers() override;

    virtual void Tick(float DeltaTime) override;
};
